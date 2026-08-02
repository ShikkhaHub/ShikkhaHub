"""Web scraping engine for the Bangladesh Education Directory.

Implements the four-stage data-ingestion pipeline that powers the directory's
initial seeding and periodic updates:

1. **Requesting**   - `PoliteFetcher` issues HTTP GETs (via httpx) with rotating
   user-agents, retries with exponential backoff on transient failures, and
   enforces a configurable per-request delay so we crawl at a human-like pace.
2. **Parsing**      - responses are turned into a BeautifulSoup DOM so data can
   be located with CSS selectors / XPath-style navigation.
3. **Extraction**   - `ScrapeConfig`-driven selector rules pull structured
   fields out of the DOM, then `normalize_record` cleans/normalizes values
   (phones, emails, years, locations, slugs) across heterogeneous sources.
4. **Storage**      - each record is checksummed (sha256) for idempotent
   deduplication and persisted as an immutable `ScrapedRecord` under a
   `ScrapeJob`, which also aggregates found/imported/failed counts.

Dynamic/JS-rendered pages are supported through an optional headless-renderer
hook: if a renderer is configured (e.g. Playwright), the fetcher will render
the page before parsing; otherwise it degrades to static HTML.

The engine deliberately stays database-agnostic for the fetch/parse/extract
stages so it is unit-testable against inline HTML and mock transports, and
only touches the DB when persisting a job run.
"""

import hashlib
import json
import logging
import random
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.data_verification import (
    RawSource,
    ScrapedRecord,
    ScrapeJob,
    VerificationQueue,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ScrapeError(Exception):
    """Raised when a URL cannot be fetched or parsed."""


class ExtractionError(ScrapeError):
    """Raised when extraction rules fail to produce usable data."""


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def clean_text(value: Optional[str]) -> Optional[str]:
    """Strip and collapse whitespace; return None for empties."""
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def normalize_phone(value: Optional[str]) -> Optional[str]:
    """Normalize a Bangladeshi phone number to +880XXXXXXXXXX."""
    if not value:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if digits.startswith("880"):
        digits = digits[3:]
    if not digits:
        return None
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    elif len(digits) == 10 and digits.startswith("1"):
        pass
    else:
        return clean_text(value)  # not obviously a BD number - keep as-is
    return "+880" + digits


def extract_emails(text: Optional[str]) -> List[str]:
    """Extract all email addresses from free text."""
    if not text:
        return []
    pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    return list(dict.fromkeys(re.findall(pattern, str(text))))


def extract_phones(text: Optional[str]) -> List[str]:
    """Extract candidate phone numbers from free text (BD formats)."""
    if not text:
        return []
    pattern = r"(?:\+?880|0)?1[3-9](?:[\s-]?\d){8}"
    found = re.findall(pattern, str(text))
    seen = set()
    out = []
    for p in found:
        norm = normalize_phone(p)
        if norm and norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out


def extract_year(text: Optional[str]) -> Optional[int]:
    """Extract a 18xx/19xx/20xx year from text."""
    if not text:
        return None
    match = re.search(r"\b(18|19|20)\d{2}\b", str(text))
    return int(match.group()) if match else None


# Common alternate spellings across public sources -> canonical national names.
DISTRICT_ALIASES = {
    "chittagong": "chattogram",
    "chatgaon": "chattogram",
    "comilla": "cumilla",
    "bogra": "bogura",
    "jessore": "jashore",
    "barisal": "barishal",
    "sylhet": "sylhet",
    "rangpur": "rangpur",
    "mymensingh": "mymensingh",
    "dhaka": "dhaka",
    "rajshahi": "rajshahi",
    "khulna": "khulna",
}
SUFFIXES = re.compile(r"\b(zilla|zila|district|jela|sadar|upazila)\b", re.IGNORECASE)


def normalize_location(value: Optional[str]) -> Optional[str]:
    """Canonicalize a Bangladeshi district/upazila name for cross-source merging."""
    if not value:
        return None
    text = clean_text(value)
    if not text:
        return None
    text = SUFFIXES.sub("", text).strip()
    return DISTRICT_ALIASES.get(text.lower(), text)


def slugify(value: Optional[str], max_length: int = 100) -> Optional[str]:
    """Slugify a name for URL-safe identity."""
    if not value:
        return None
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
    return slug[:max_length]


def record_checksum(record: Dict[str, Any]) -> str:
    """Stable sha256 of a normalized record, used for deduplication."""
    canonical = json.dumps(
        record, sort_keys=True, ensure_ascii=False, default=str
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# Extraction configuration
# ---------------------------------------------------------------------------


@dataclass
class FieldSelector:
    """Rule for extracting one field from the DOM.

    `selector` is a CSS selector. Unless `attribute` is set (e.g. ``href``,
    ``src``) the node's visible text is used. `transform` normalizes the raw
    value (text / int / year / phone / email / url / lower / title).
    """

    field: str
    selector: Optional[str] = None
    attribute: Optional[str] = None
    multiple: bool = False
    transform: str = "text"


@dataclass
class ScrapeConfig:
    """Extraction plan for a source.

    - ``item_selector``: optional repeating container (list-page mode). When
      set, each matching element yields one record.
    - ``fields``: field rules, applied inside each item (or the whole page when
      ``item_selector`` is unset).
    - ``link_selector`` + ``detail_fields``: optional two-phase crawl - list
      items yield links which are fetched individually to enrich records.
    - ``pagination_selector`` + ``max_pages``: follow "next page" links.
    """

    record_type: str = "institution"
    item_selector: Optional[str] = None
    fields: List[FieldSelector] = field(default_factory=list)
    link_selector: Optional[str] = None
    detail_fields: List[FieldSelector] = field(default_factory=list)
    pagination_selector: Optional[str] = None
    max_pages: int = 1
    max_items: int = 0  # 0 = unlimited
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["fields"] = [asdict(f) for f in self.fields]
        data["detail_fields"] = [asdict(f) for f in self.detail_fields]
        return data


# ---------------------------------------------------------------------------
# Requesting layer
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]


class PoliteFetcher:
    """HTTP client with politeness, retries and optional headless rendering.

    Each request sleeps a random delay in ``delay_range`` to avoid hammering the
    target. Transient failures (429/5xx/timeout/connection) are retried with
    exponential backoff. An optional ``renderer`` callable lets dynamic pages be
    rendered to HTML before parsing.
    """

    RETRYABLE_STATUS = (429, 500, 502, 503, 504)

    def __init__(
        self,
        delay_range: tuple = (0.5, 1.5),
        max_retries: int = 3,
        timeout: float = 20.0,
        verify_ssl: bool = True,
        transport: Optional[httpx.BaseTransport] = None,
        renderer: Optional[Callable[[str], str]] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.timeout = timeout
        self.renderer = renderer
        self._sleep = sleep
        self._ua_index = random.randrange(len(USER_AGENTS))
        self.client = httpx.Client(
            timeout=timeout,
            verify=verify_ssl,
            follow_redirects=True,
            transport=transport,
        )
        self.stats = {
            "requests": 0,
            "success": 0,
            "failed": 0,
            "ssl_bypassed": 0,
        }

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        self._ua_index = (self._ua_index + 1) % len(USER_AGENTS)
        headers = {
            "User-Agent": USER_AGENTS[self._ua_index],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        if extra:
            headers.update(extra)
        return headers

    def _sleep_for_politeness(self) -> None:
        low, high = self.delay_range
        self._sleep(random.uniform(low, high))

    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """Fetch a URL, applying politeness, retries and optional rendering."""
        self._sleep_for_politeness()
        self.stats["requests"] += 1
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.get(url, headers=self._headers(headers))
                self.stats["success"] += 1
                response.raise_for_status()
                html = response.text
                if self.renderer is not None:
                    html = self.renderer(url) or html
                return html
            except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                status = getattr(exc, "response", None)
                retriable = (
                    status is None
                    or status.status_code in self.RETRYABLE_STATUS
                )
                if not retriable:
                    self.stats["failed"] += 1
                    raise ScrapeError(f"{url}: {exc}") from exc
                if attempt < self.max_retries:
                    self._sleep(2 ** attempt)

        self.stats["failed"] += 1
        raise ScrapeError(f"max retries exceeded for {url}: {last_error}")

    def close(self) -> None:
        self.client.close()


# ---------------------------------------------------------------------------
# Parsing & extraction
# ---------------------------------------------------------------------------

TEXT_TRANSFORMS = {
    "text": lambda v: v,
    "lower": lambda v: v.lower() if v else v,
    "title": lambda v: v.title() if v else v,
}


def _node_value(node: Any, fs: FieldSelector) -> Any:
    if node is None:
        return None
    if fs.attribute:
        value = node.get(fs.attribute)
    else:
        value = node.get_text(" ", strip=True)
    return clean_text(value)


def _apply_transform(value: Any, transform: str) -> Any:
    if value is None:
        return None
    if transform == "int":
        match = re.search(r"\d+", str(value))
        return int(match.group()) if match else None
    if transform == "year":
        return extract_year(str(value))
    if transform == "phone":
        phones = extract_phones(str(value))
        return phones[0] if phones else None
    if transform == "email":
        emails = extract_emails(str(value))
        return emails[0] if emails else None
    if transform == "url":
        return clean_text(str(value))
    return TEXT_TRANSFORMS.get(transform, TEXT_TRANSFORMS["text"])(value)


def _absolute(value: Any, base_url: str) -> Any:
    if value and isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    if value:
        return urljoin(base_url, value)
    return value


def extract_page(
    html: str, config: ScrapeConfig, base_url: str, limit: int = 0
) -> List[Dict[str, Any]]:
    """Extract structured records from HTML per the scrape config."""
    soup = BeautifulSoup(html, "html.parser")
    records: List[Dict[str, Any]] = []

    if config.item_selector:
        containers = soup.select(config.item_selector)
        for container in containers:
            if limit and len(records) >= limit:
                break
            record: Dict[str, Any] = {}
            for fs in config.fields:
                if fs.multiple:
                    values = []
                    for node in container.select(fs.selector) if fs.selector else []:
                        value = _apply_transform(_node_value(node, fs), fs.transform)
                        if fs.attribute == "href":
                            value = _absolute(value, base_url)
                        if value is not None:
                            values.append(value)
                    record[fs.field] = values
                else:
                    node = container if not fs.selector else container.select_one(fs.selector)
                    value = _apply_transform(_node_value(node, fs), fs.transform)
                    if fs.attribute == "href":
                        value = _absolute(value, base_url)
                    record[fs.field] = value
            records.append(record)
    else:
        record: Dict[str, Any] = {}
        for fs in config.fields:
            node = soup if not fs.selector else soup.select_one(fs.selector)
            value = _apply_transform(_node_value(node, fs), fs.transform)
            if fs.attribute == "href":
                value = _absolute(value, base_url)
            record[fs.field] = value
        records.append(record)

    return records


def extract_next_page_url(html: str, config: ScrapeConfig, base_url: str) -> Optional[str]:
    """Find the next page URL from a pagination selector (if configured)."""
    if not config.pagination_selector:
        return None
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one(config.pagination_selector)
    if node is None:
        return None
    href = node.get("href")
    return urljoin(base_url, href) if href else None


# ---------------------------------------------------------------------------
# Record normalization
# ---------------------------------------------------------------------------


def normalize_record(record: Dict[str, Any], record_type: str = "institution") -> Dict[str, Any]:
    """Clean and normalize a raw extracted record into a standard shape."""
    normalized: Dict[str, Any] = {
        "record_type": record_type,
    }
    for key, value in record.items():
        if value is None:
            normalized[key] = None
            continue
        if isinstance(value, list):
            normalized[key] = [clean_text(v) for v in value if v]
        else:
            normalized[key] = clean_text(value)

    # Cross-field normalization for institution-type records
    if record_type == "institution":
        normalized["name_en"] = clean_text(normalized.get("name_en") or normalized.get("name"))
        normalized["district"] = normalize_location(normalized.get("district"))
        normalized["upazila"] = normalize_location(normalized.get("upazila"))
        normalized["division"] = normalize_location(normalized.get("division"))
        if normalized.get("established_year") is None:
            normalized["established_year"] = extract_year(
                normalized.get("established_year_text")
            )
        if normalized.get("phone"):
            normalized["phone"] = normalize_phone(normalized.get("phone"))

    return normalized


# ---------------------------------------------------------------------------
# Storage layer (ScrapeJob + ScrapedRecord)
# ---------------------------------------------------------------------------


def create_job(
    db: Session,
    raw_source: RawSource,
    status: str = "running",
    config: Optional[Dict[str, Any]] = None,
) -> ScrapeJob:
    job = ScrapeJob(
        raw_source_id=raw_source.id,
        status=status,
        started_at=datetime.utcnow(),
        error_log=json.dumps({"config": config}, ensure_ascii=False)
        if config
        else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _store_record(db: Session, job: ScrapeJob, record: Dict[str, Any]) -> str:
    """Persist one normalized record, deduplicating by checksum.

    Returns the record status ('new', 'duplicate', 'failed').
    """
    checksum = record_checksum(record)
    existing = (
        db.query(ScrapedRecord)
        .filter(ScrapedRecord.checksum == checksum)
        .first()
    )
    if existing:
        return "duplicate"

    try:
        db.add(
            ScrapedRecord(
                scrape_job_id=job.id,
                record_type=record.get("record_type", "institution"),
                external_id=record.get("external_id"),
                raw_data=json.dumps(record, ensure_ascii=False),
                checksum=checksum,
                status="new",
                source_url=record.get("source_url"),
                confidence_score=record.get("confidence_score"),
            )
        )
        return "new"
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to store record: %s", exc)
        return "failed"


def _run_job(
    db: Session,
    job: ScrapeJob,
    config: ScrapeConfig,
    start_url: str,
    fetcher: Optional[PoliteFetcher] = None,
) -> ScrapeJob:
    """Execute a scrape job: crawl, extract, normalize and store records."""
    if fetcher is None:
        fetcher = PoliteFetcher(delay_range=(0.1, 0.3), max_retries=2)
    found = 0
    imported = 0
    failed = 0
    errors: List[str] = []

    try:
        current_url: Optional[str] = start_url
        page = 0
        seen_links = set()
        while current_url and page < config.max_pages:
            page += 1
            try:
                html = fetcher.get(current_url, headers=config.headers or None)
            except ScrapeError as exc:
                errors.append(str(exc))
                break

            base_url = current_url

            if config.link_selector and config.detail_fields:
                # Two-phase crawl: extract links, then fetch each detail page.
                soup = BeautifulSoup(html, "html.parser")
                for node in soup.select(config.link_selector):
                    if config.max_items and found >= config.max_items:
                        break
                    href = node.get("href")
                    if not href:
                        continue
                    detail_url = urljoin(base_url, href)
                    if detail_url in seen_links:
                        continue
                    seen_links.add(detail_url)
                    found += 1
                    try:
                        detail_html = fetcher.get(detail_url, headers=config.headers or None)
                        detail_records = extract_page(detail_html, ScrapeConfig(
                            record_type=config.record_type,
                            fields=config.detail_fields,
                        ), base_url=detail_url)
                        if not detail_records:
                            failed += 1
                            continue
                        record = detail_records[0]
                        record["source_url"] = detail_url
                        normalized = normalize_record(record, config.record_type)
                        status = _store_record(db, job, normalized)
                        if status == "new":
                            imported += 1
                        elif status == "failed":
                            failed += 1
                    except ScrapeError as exc:
                        errors.append(str(exc))
                        failed += 1

            else:
                records = extract_page(html, config, base_url, limit=config.max_items)
                for record in records:
                    found += 1
                    record["source_url"] = base_url
                    status = _store_record(db, job, normalize_record(record, config.record_type))
                    if status == "new":
                        imported += 1
                    elif status == "failed":
                        failed += 1

            if config.max_items and found >= config.max_items:
                break

            if page < config.max_pages:
                current_url = extract_next_page_url(html, config, base_url)
            else:
                current_url = None
    finally:
        fetcher.close()

    db.flush()
    job.status = "completed"
    job.records_found = found
    job.records_imported = imported
    job.records_failed = failed
    job.completed_at = datetime.utcnow()
    job.error_log = "; ".join(errors[:10]) if errors else None
    db.commit()
    db.refresh(job)
    return job


def run_scrape(
    db: Session,
    raw_source: RawSource,
    start_url: str,
    config: ScrapeConfig,
    fetcher: Optional[PoliteFetcher] = None,
) -> Dict[str, Any]:
    """Run a scrape against a source and persist its ScrapeJob + records."""
    job = create_job(db, raw_source, config=config.to_dict())
    try:
        job = _run_job(db, job, config, start_url, fetcher=fetcher)
        return {
            "job_id": job.id,
            "status": job.status,
            "records_found": job.records_found,
            "records_imported": job.records_imported,
            "records_failed": job.records_failed,
            "errors": job.error_log,
        }
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scrape job %s failed", job.id)
        job.status = "failed"
        job.error_log = str(exc)
        db.commit()
        return {
            "job_id": job.id,
            "status": job.status,
            "records_found": job.records_found,
            "records_imported": job.records_imported,
            "records_failed": job.records_failed,
            "errors": job.error_log,
        }


# ---------------------------------------------------------------------------
# Record import into the directory + verification queue
# ---------------------------------------------------------------------------


def import_record(
    db: Session,
    record_id: int,
    institution_type_id: Optional[int] = None,
) -> Optional[ScrapedRecord]:
    """Import a scraped record into an Institution and queue it for review.

    Creates the Institution (or finds it by EIIN / normalized name) and
    inserts a `VerificationQueue` entry so the community can confirm the
    scraped values before they are treated as authoritative.
    """
    from app.models.institution import Institution

    record = db.query(ScrapedRecord).filter(ScrapedRecord.id == record_id).first()
    if record is None:
        return None
    data = json.loads(record.raw_data or "{}")

    institution = None
    if data.get("eiin"):
        institution = (
            db.query(Institution).filter(Institution.eiin == str(data["eiin"])).first()
        )
    if institution is None and data.get("name_en"):
        institution = (
            db.query(Institution)
            .filter(Institution.name_en == data["name_en"])
            .first()
        )

    if institution is None:
        from app.models.institution import InstitutionType

        type_id = institution_type_id
        if type_id is None:
            first_type = db.query(InstitutionType).first()
            type_id = first_type.id if first_type else None
        if type_id is None:
            raise ScrapeError(
                "Cannot import: no institution type configured"
            )
        institution = Institution(
            name_en=data.get("name_en") or "Unknown",
            slug=data.get("slug") or slugify(data.get("name_en")) or f"record-{record.id}",
            type_id=type_id,
            eiin=data.get("eiin"),
            board=data.get("education_board"),
            division_id=None,
            district_id=None,
            upazila_id=None,
            address=data.get("address"),
            phone=data.get("phone"),
            email=data.get("email"),
            website=data.get("website"),
            established_year=data.get("established_year"),
            education_level=data.get("education_level"),
            data_source="scraped",
            verification_status="pending",
            verification_level=0,
            is_active=True,
        )
        db.add(institution)
        db.flush()

    # Queue the raw values for human verification before promotion
    queue = VerificationQueue(
        scraped_record_id=record.id,
        institution_id=institution.id,
        record_type=record.record_type,
        field_name="import",
        current_value=None,
        suggested_value=json.dumps(data, ensure_ascii=False),
        source_summary=f"Imported from scrape job {record.scrape_job_id}",
        priority="medium",
        status="pending",
    )
    db.add(queue)

    record.status = "imported"
    record.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Dynamic content hook
# ---------------------------------------------------------------------------


def get_headless_renderer(
    browser: str = "playwright",
) -> Optional[Callable[[str], str]]:
    """Return a renderer that executes JS before parsing (dynamic content).

    Returns None when the optional browser package is unavailable, in which
    case scraping falls back to static HTML.
    """
    try:
        if browser == "playwright":
            from playwright.sync_api import sync_playwright  # type: ignore

            def render(url: str) -> str:
                with sync_playwright() as p:
                    browser_ = p.chromium.launch()
                    page = browser_.new_page()
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    html = page.content()
                    browser_.close()
                return html

            return render
        if browser == "selenium":
            from selenium import webdriver  # type: ignore

            def render(url: str) -> str:
                driver = webdriver.Chrome()
                driver.get(url)
                html = driver.page_source
                driver.quit()
                return html

            return render
    except ImportError:
        logger.info("Headless renderer %s unavailable - using static HTML", browser)
    return None
