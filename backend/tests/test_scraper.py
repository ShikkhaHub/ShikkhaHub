"""Tests for the web scraping engine (service + API)."""

import json
import uuid

import httpx
import pytest

from app.models.data_verification import RawSource, ScrapedRecord, ScrapeJob
from app.models.user import User, UserRole
from app.core.security import create_access_token, get_password_hash
from app.services import scraper
from app.services.scraper_presets import PRESETS, get_preset

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _admin_auth(db_session):
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin = User(
        email=email,
        username=f"admin_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("pw123456"),
        first_name="A",
        last_name="U",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    token = create_access_token({"sub": str(admin.id)})
    return {"Authorization": f"Bearer {token}"}


LIST_HTML = """
<html><body>
<div class="school-item" data-eiin="104391">
  <h2 class="name">Dhaka College</h2>
  <span class="board">Dhaka</span>
  <span class="upazila">Dhanmondi</span>
  <span class="district">Dhaka</span>
  <span class="established">Established 1841</span>
  <a class="link" href="/institutions/104391">Detail</a>
</div>
<div class="school-item" data-eiin="106810">
  <h2 class="name">Notre Dame College</h2>
  <span class="board">dhaka</span>
  <span class="upazila">Motijheel</span>
  <span class="district">Dhaka</span>
</div>
</body></html>
"""

DETAIL_HTML = """
<html><body>
<h1 class="name">Dhaka College</h1>
<p class="address">Ramna, Dhaka</p>
<p class="contact">Phone: +880-2-861 7X 7 / 01710-123456 Email: info@dhakacollege.edu.bd</p>
<a class="website" href="https://www.dhakacollege.edu.bd">Site</a>
</body></html>
"""


def _mock_fetcher(url_map):
    """Build a PoliteFetcher backed by an in-memory transport."""
    def handler(request):
        html = url_map.get(str(request.url))
        if html is None:
            return httpx.Response(404, request=request)
        return httpx.Response(200, text=html, request=request)

    return scraper.PoliteFetcher(
        delay_range=(0.0, 0.0),
        max_retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )


LIST_CONFIG = scraper.ScrapeConfig(
    record_type="institution",
    item_selector=".school-item",
    fields=[
        scraper.FieldSelector("name_en", ".name"),
        scraper.FieldSelector("eiin", None, attribute="data-eiin"),
        scraper.FieldSelector("education_board", ".board", transform="lower"),
        scraper.FieldSelector("upazila", ".upazila"),
        scraper.FieldSelector("district", ".district"),
        scraper.FieldSelector("established_year", ".established", transform="year"),
    ],
)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def test_normalize_phone():
    assert scraper.normalize_phone("01710-123456") == "+8801710123456"
    assert scraper.normalize_phone("+8801711001100") == "+8801711001100"
    assert scraper.normalize_phone("+880 2 861 7X7") == "+880 2 861 7X7"
    assert scraper.normalize_phone(None) is None
    assert scraper.normalize_phone("") is None


def test_extract_emails():
    assert scraper.extract_emails("mail info@a.edu.bd and b@c.org") == ["info@a.edu.bd", "b@c.org"]
    assert scraper.extract_emails("no emails here") == []


def test_extract_year():
    assert scraper.extract_year("Established 1841") == 1841
    assert scraper.extract_year("2005 CE") == 2005
    assert scraper.extract_year(None) is None
    assert scraper.extract_year("n/a") is None


def test_normalize_location():
    assert scraper.normalize_location(" Dhaka ") == "dhaka"
    assert scraper.normalize_location("Dhaka Zila") == "dhaka"
    assert scraper.normalize_location("Chittagong") == "chattogram"
    assert scraper.normalize_location(None) is None


def test_slugify():
    assert scraper.slugify("Dhaka College") == "dhaka-college"
    assert scraper.slugify("  COMSATS   Uni  ") == "comsats-uni"


def test_record_checksum():
    a = {"name_en": "X", "eiin": "1"}
    b = {"eiin": "1", "name_en": "X"}
    c = {"name_en": "Y", "eiin": "1"}
    assert scraper.record_checksum(a) == scraper.record_checksum(b)
    assert scraper.record_checksum(a) != scraper.record_checksum(c)


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------


def test_extract_page_list_mode():
    records = scraper.extract_page(LIST_HTML, LIST_CONFIG, base_url="https://board.gov.bd")
    assert len(records) == 2
    first = records[0]
    assert first["name_en"] == "Dhaka College"
    assert first["eiin"] == "104391"
    assert first["education_board"] == "dhaka"
    assert first["established_year"] == 1841


def test_extract_page_single_mode():
    config = scraper.ScrapeConfig(
        fields=[
            scraper.FieldSelector("title", "h1.name"),
            scraper.FieldSelector("website", "a.website", attribute="href"),
        ]
    )
    records = scraper.extract_page(DETAIL_HTML, config, base_url="https://board.gov.bd/detail")
    assert len(records) == 1
    assert records[0]["title"] == "Dhaka College"
    assert records[0]["website"] == "https://www.dhakacollege.edu.bd"


def test_extract_href_is_absolutized():
    config = scraper.ScrapeConfig(
        fields=[scraper.FieldSelector("link", "a.link", attribute="href")]
    )
    records = scraper.extract_page(LIST_HTML, config, base_url="https://board.gov.bd/list")
    assert records[0]["link"] == "https://board.gov.bd/institutions/104391"


def test_extract_next_page_url():
    config = scraper.ScrapeConfig(pagination_selector=".pagination a.next")
    html = '<div class="pagination"><a class="next" href="/list?page=2">Next</a></div>'
    url = scraper.extract_next_page_url(html, config, "https://board.gov.bd/list")
    assert url == "https://board.gov.bd/list?page=2"

    assert scraper.extract_next_page_url(LIST_HTML, config, "https://b") is None


# ---------------------------------------------------------------------------
# Fetching layer
# ---------------------------------------------------------------------------


def test_fetcher_success_and_headers():
    seen_agents = []

    def handler(request):
        seen_agents.append(request.headers.get("user-agent"))
        return httpx.Response(200, text="<html>ok</html>", request=request)

    fetcher = scraper.PoliteFetcher(
        delay_range=(0.0, 0.0),
        max_retries=1,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    html = fetcher.get("https://example.com/")
    fetcher.close()
    assert html == "<html>ok</html>"
    assert seen_agents and seen_agents[0]


def test_fetcher_retries_on_5xx_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, request=request)
        return httpx.Response(200, text="<html>recovered</html>", request=request)

    fetcher = scraper.PoliteFetcher(
        delay_range=(0.0, 0.0),
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    assert fetcher.get("https://example.com/") == "<html>recovered</html>"
    assert calls["n"] == 2
    fetcher.close()


def test_fetcher_raises_on_non_retriable():
    fetcher = scraper.PoliteFetcher(
        delay_range=(0.0, 0.0),
        max_retries=3,
        transport=httpx.MockTransport(lambda r: httpx.Response(404, request=r)),
        sleep=lambda _: None,
    )
    with pytest.raises(scraper.ScrapeError):
        fetcher.get("https://example.com/missing")
    fetcher.close()


def test_fetcher_gives_up_after_retries():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500, request=request)

    fetcher = scraper.PoliteFetcher(
        delay_range=(0.0, 0.0),
        max_retries=3,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )
    with pytest.raises(scraper.ScrapeError):
        fetcher.get("https://example.com/")
    assert calls["n"] == 3
    fetcher.close()


# ---------------------------------------------------------------------------
# Full job run (service level, DB-backed)
# ---------------------------------------------------------------------------


def _create_raw_source(db_session):
    source = RawSource(
        name=f"UGC {uuid.uuid4().hex[:6]}",
        source_type="government",
        base_url="https://ugc-universities.gov.bd",
        reliability_score=0.8,
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)
    return source


def test_run_scrape_list_mode(db_session):
    source = _create_raw_source(db_session)
    url_map = {"https://board.gov.bd/list": LIST_HTML}
    fetcher = _mock_fetcher(url_map)

    result = scraper.run_scrape(
        db_session,
        source,
        "https://board.gov.bd/list",
        LIST_CONFIG,
        fetcher=fetcher,
    )

    assert result["status"] == "completed"
    assert result["records_found"] == 2
    assert result["records_imported"] == 2

    job = db_session.query(ScrapeJob).filter(ScrapeJob.raw_source_id == source.id).first()
    assert job.records_found == 2
    assert job.records_imported == 2

    records = (
        db_session.query(ScrapedRecord)
        .filter(ScrapedRecord.scrape_job_id == job.id)
        .all()
    )
    assert len(records) == 2
    raw = json.loads(records[0].raw_data)
    assert raw["name_en"] == "Dhaka College"
    assert raw["record_type"] == "institution"


def test_run_scrape_deduplicates_by_checksum(db_session):
    source = _create_raw_source(db_session)
    fetcher = _mock_fetcher({"https://board.gov.bd/list": LIST_HTML})

    first = scraper.run_scrape(
        db_session, source, "https://board.gov.bd/list", LIST_CONFIG, fetcher=fetcher
    )
    assert first["records_imported"] == 2

    fetcher2 = _mock_fetcher({"https://board.gov.bd/list": LIST_HTML})
    second = scraper.run_scrape(
        db_session, source, "https://board.gov.bd/list", LIST_CONFIG, fetcher=fetcher2
    )
    assert second["records_imported"] == 0
    assert second["records_found"] == 2

    total = db_session.query(ScrapedRecord).count()
    assert total == 2


def test_run_scrape_two_phase_crawl(db_session):
    source = _create_raw_source(db_session)
    list_html = """
    <html><body>
    <div class="school-item">
      <h1 class="name">Dhaka College</h1>
      <a class="link" href="/institutions/104391">Detail</a>
    </div>
    <div class="school-item">
      <h1 class="name">Notre Dame College</h1>
      <a class="link" href="/institutions/106810">Detail</a>
    </div>
    </body></html>
    """
    url_map = {
        "https://board.gov.bd/list": list_html,
        "https://board.gov.bd/institutions/104391": DETAIL_HTML,
        "https://board.gov.bd/institutions/106810": (
            "<html><body><h1 class='name'>Notre Dame College</h1></body></html>"
        ),
    }
    config = scraper.ScrapeConfig(
        record_type="institution",
        link_selector="a.link",
        detail_fields=[
            scraper.FieldSelector("name_en", "h1.name"),
            scraper.FieldSelector("address", ".address"),
            scraper.FieldSelector("email", ".contact", transform="email"),
            scraper.FieldSelector("phone", ".contact", transform="phone"),
            scraper.FieldSelector("website", "a.website", attribute="href"),
        ],
    )
    fetcher = _mock_fetcher(url_map)
    result = scraper.run_scrape(
        db_session, source, "https://board.gov.bd/list", config, fetcher=fetcher
    )

    assert result["records_found"] == 2
    assert result["records_imported"] == 2

    record = (
        db_session.query(ScrapedRecord)
        .filter(ScrapedRecord.source_url == "https://board.gov.bd/institutions/104391")
        .first()
    )
    raw = json.loads(record.raw_data)
    assert raw["name_en"] == "Dhaka College"
    assert raw["address"] == "Ramna, Dhaka"
    assert raw["email"] == "info@dhakacollege.edu.bd"
    assert raw["phone"] == "+8801710123456"
    assert raw["website"] == "https://www.dhakacollege.edu.bd"


def test_import_record_creates_institution_and_queue(db_session):
    from app.models.institution import Institution, InstitutionType

    itype = InstitutionType(name=f"college_{uuid.uuid4().hex[:6]}")
    db_session.add(itype)
    db_session.commit()
    db_session.refresh(itype)

    source = _create_raw_source(db_session)
    fetcher = _mock_fetcher({"https://board.gov.bd/list": LIST_HTML})
    scraper.run_scrape(
        db_session, source, "https://board.gov.bd/list", LIST_CONFIG, fetcher=fetcher
    )

    record = db_session.query(ScrapedRecord).first()
    raw = json.loads(record.raw_data)
    imported = scraper.import_record(db_session, record.id, institution_type_id=itype.id)
    assert imported is not None
    assert imported.status == "imported"

    institution = (
        db_session.query(Institution).filter(Institution.eiin == raw["eiin"]).first()
    )
    assert institution is not None
    assert institution.name_en == "Dhaka College"
    assert institution.data_source == "scraped"

    from app.models.data_verification import VerificationQueue

    queue = (
        db_session.query(VerificationQueue)
        .filter(VerificationQueue.scraped_record_id == record.id)
        .first()
    )
    assert queue is not None
    assert queue.status == "pending"


def test_import_record_missing_returns_none(db_session):
    assert scraper.import_record(db_session, 99999) is None


def test_presets_are_valid():
    for name, config in PRESETS.items():
        assert config.record_type == "institution"
        assert get_preset(name) is config


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


def test_presets_endpoint(client):
    response = client.get("/api/v1/scraping/presets")
    assert response.status_code == 200
    body = response.json()
    assert "education_board" in body
    assert "fields" in body["education_board"]


def test_extract_endpoint_dry_run(client, monkeypatch):
    url_map = {"https://board.gov.bd/list": LIST_HTML}
    fake = _mock_fetcher(url_map)

    def fake_factory(*args, **kwargs):
        return fake

    monkeypatch.setattr(scraper, "PoliteFetcher", fake_factory)
    payload = {
        "url": "https://board.gov.bd/list",
        "config": {
            "record_type": "institution",
            "item_selector": ".school-item",
            "fields": [
                {"field": "name_en", "selector": ".name"},
                {"field": "eiin", "selector": None, "attribute": "data-eiin"},
                {"field": "education_board", "selector": ".board", "transform": "lower"},
            ],
        },
    }
    response = client.post("/api/v1/scraping/extract", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert len(body["records"]) == 2
    assert body["records"][0]["name_en"] == "Dhaka College"
    assert body["records"][0]["education_board"] == "dhaka"
    assert "stats" in body


def test_create_source_requires_admin(client):
    response = client.post(
        "/api/v1/scraping/sources",
        json={"name": "UGC", "source_type": "government"},
    )
    assert response.status_code in (401, 403)


def test_create_and_list_sources(client, db_session):
    headers = _admin_auth(db_session)
    response = client.post(
        "/api/v1/scraping/sources",
        headers=headers,
        json={"name": "UGC", "source_type": "government", "base_url": "https://ugc.gov.bd"},
    )
    assert response.status_code == 201
    source_id = response.json()["id"]

    dup = client.post(
        "/api/v1/scraping/sources",
        headers=headers,
        json={"name": "UGC", "source_type": "government"},
    )
    assert dup.status_code == 409

    listing = client.get("/api/v1/scraping/sources")
    assert listing.status_code == 200
    assert any(s["id"] == source_id for s in listing.json())


def test_run_job_endpoint(db_session, client, monkeypatch):
    source = _create_raw_source(db_session)
    headers = _admin_auth(db_session)
    fake = _mock_fetcher({"https://board.gov.bd/list": LIST_HTML})
    monkeypatch.setattr(scraper, "PoliteFetcher", lambda *a, **k: fake)

    payload = {
        "raw_source_id": source.id,
        "start_url": "https://board.gov.bd/list",
        "config": {
            "record_type": "institution",
            "item_selector": ".school-item",
            "fields": [
                {"field": "name_en", "selector": ".name"},
                {"field": "eiin", "selector": None, "attribute": "data-eiin"},
            ],
        },
    }
    response = client.post("/api/v1/scraping/jobs", headers=headers, json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["records_imported"] == 2

    job_id = body["job_id"]
    detail = client.get(f"/api/v1/scraping/jobs/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["records_found"] == 2

    records = client.get(f"/api/v1/scraping/jobs/{job_id}/records")
    assert records.status_code == 200
    body = records.json()
    assert len(body) == 2
    names = {r["data"]["name_en"] for r in body}
    assert names == {"Dhaka College", "Notre Dame College"}


def test_run_job_requires_admin(client, db_session):
    source = _create_raw_source(db_session)
    payload = {"raw_source_id": source.id, "start_url": "https://x", "preset": "education_board"}
    response = client.post("/api/v1/scraping/jobs", json=payload)
    assert response.status_code in (401, 403)


def test_unknown_preset_rejected(client, db_session):
    source = _create_raw_source(db_session)
    headers = _admin_auth(db_session)
    payload = {"raw_source_id": source.id, "start_url": "https://x", "preset": "nope"}
    response = client.post("/api/v1/scraping/jobs", headers=headers, json=payload)
    assert response.status_code == 400


def test_import_endpoint(client, db_session, monkeypatch):
    from app.models.institution import InstitutionType

    itype = InstitutionType(name=f"college_{uuid.uuid4().hex[:6]}")
    db_session.add(itype)
    db_session.commit()
    db_session.refresh(itype)

    source = _create_raw_source(db_session)
    fake = _mock_fetcher({"https://board.gov.bd/list": LIST_HTML})
    monkeypatch.setattr(scraper, "PoliteFetcher", lambda *a, **k: fake)
    scraper.run_scrape(
        db_session, source, "https://board.gov.bd/list", LIST_CONFIG, fetcher=fake
    )

    record = db_session.query(ScrapedRecord).first()
    headers = _admin_auth(db_session)
    response = client.post(
        f"/api/v1/scraping/records/{record.id}/import",
        headers=headers,
        json={"institution_type_id": itype.id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["institution_id"]
    assert body["status"] == "imported"
