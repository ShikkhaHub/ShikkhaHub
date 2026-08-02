"""Web scraping API endpoints.

Exposes the scraping engine to operators:

- **Dry-run extraction** - fetch a URL with a selector config and return the
  structured records without touching the DB. Used to validate/tune selectors
  before scheduling a full crawl.
- **Sources** - register/manage `RawSource` origins (education boards, UGC,
  BMED, BTEB, ...) with reliability weighting.
- **Jobs** - trigger a scrape run against a source (via a named preset or an
  inline config), then inspect job results and harvested records.
- **Import** - promote a scraped record into an `Institution` and queue it in
  the verification pipeline for human confirmation.

All mutating routes are admin-only; reads are public.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.data_verification import (
    RawSource,
    ScrapedRecord,
    ScrapeJob,
)
from app.models.user import User
from app.schemas.scraper import (
    ExtractRequest,
    ExtractResponse,
    ImportRecordRequest,
    ImportRecordResponse,
    JobCreate,
    JobResponse,
    JobRunResponse,
    RawSourceCreate,
    RawSourceResponse,
    RecordResponse,
    ScrapeConfigIn,
)
from app.services import scraper
from app.services.scraper_presets import get_preset, list_presets

router = APIRouter()


def _config_from(payload: ScrapeConfigIn, preset: Optional[str]) -> scraper.ScrapeConfig:
    """Build an internal ScrapeConfig from an inline config or preset."""
    if payload and payload.fields:
        return scraper.ScrapeConfig(
            record_type=payload.record_type,
            item_selector=payload.item_selector,
            fields=[scraper.FieldSelector(**f.model_dump()) for f in payload.fields],
            link_selector=payload.link_selector,
            detail_fields=[scraper.FieldSelector(**f.model_dump()) for f in payload.detail_fields],
            pagination_selector=payload.pagination_selector,
            max_pages=payload.max_pages,
            max_items=payload.max_items,
            headers=payload.headers,
        )
    if preset:
        try:
            return get_preset(preset)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"Unknown preset: {preset}") from exc
    raise HTTPException(status_code=400, detail="Provide a config or preset")


# ---------------------------------------------------------------------------
# Presets & dry-run (public)
# ---------------------------------------------------------------------------


@router.get("/presets")
def list_scrape_presets():
    """List available source preset templates."""
    return list_presets()


@router.post("/extract", response_model=ExtractResponse)
def extract_preview(payload: ExtractRequest):
    """Fetch a URL and extract records with a config - no DB writes.

    Use this to validate CSS selectors against a live page before running a job.
    """
    config = _config_from(payload.config, preset=None)
    fetcher = scraper.PoliteFetcher(delay_range=(0.1, 0.3), max_retries=2)
    try:
        html = fetcher.get(payload.url, headers=config.headers or None)
    except scraper.ScrapeError as exc:
        raise HTTPException(status_code=502, detail=f"Fetch failed: {exc}") from exc
    finally:
        fetcher.close()

    records = scraper.extract_page(html, config, base_url=payload.url)
    return ExtractResponse(
        url=payload.url,
        records=[scraper.normalize_record(r, config.record_type) for r in records],
        stats=fetcher.stats,
    )


# ---------------------------------------------------------------------------
# Sources (admin write)
# ---------------------------------------------------------------------------


@router.get("/sources", response_model=List[RawSourceResponse])
def list_sources(
    source_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List registered data sources (public)."""
    query = db.query(RawSource)
    if source_type:
        query = query.filter(RawSource.source_type == source_type)
    return query.order_by(RawSource.reliability_score.desc()).all()


@router.post("/sources", response_model=RawSourceResponse, status_code=201)
def create_source(
    payload: RawSourceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Register a new data source (admin)."""
    existing = db.query(RawSource).filter(RawSource.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Source already exists")
    source = RawSource(**payload.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.patch("/sources/{source_id}", response_model=RawSourceResponse)
def update_source(
    source_id: int,
    payload: RawSourceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Update a data source (admin)."""
    source = db.query(RawSource).filter(RawSource.id == source_id).first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(source, key, value)
    db.commit()
    db.refresh(source)
    return source


# ---------------------------------------------------------------------------
# Jobs (admin trigger)
# ---------------------------------------------------------------------------


@router.post("/jobs", response_model=JobRunResponse, status_code=201)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Run a scrape job against a source (admin).

    Provide a `preset` name or an inline `config` to define the extraction
    rules, plus the `start_url` to crawl.
    """
    source = db.query(RawSource).filter(RawSource.id == payload.raw_source_id).first()
    if source is None:
        raise HTTPException(status_code=404, detail="Raw source not found")
    config = _config_from(payload.config, payload.preset)
    return scraper.run_scrape(db, source, payload.start_url, config)


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List scrape jobs, most recent first."""
    query = db.query(ScrapeJob)
    if status:
        query = query.filter(ScrapeJob.status == status)
    return query.order_by(ScrapeJob.id.desc()).limit(limit).all()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a scrape job and its summary."""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/records", response_model=List[RecordResponse])
def get_job_records(job_id: int, db: Session = Depends(get_db)):
    """List the records harvested by a job."""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    records = (
        db.query(ScrapedRecord)
        .filter(ScrapedRecord.scrape_job_id == job_id)
        .order_by(ScrapedRecord.id.desc())
        .all()
    )
    return [
        RecordResponse(
            id=r.id,
            scrape_job_id=r.scrape_job_id,
            record_type=r.record_type,
            external_id=r.external_id,
            checksum=r.checksum,
            status=r.status,
            source_url=r.source_url,
            confidence_score=r.confidence_score,
            created_at=r.created_at,
            data=json.loads(r.raw_data or "{}"),
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# Record import (admin)
# ---------------------------------------------------------------------------


@router.post("/records/{record_id}/import", response_model=ImportRecordResponse)
def import_scraped_record(
    record_id: int,
    payload: ImportRecordRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Import a scraped record into the directory and queue it for review."""
    try:
        record = scraper.import_record(
            db, record_id, institution_type_id=payload.institution_type_id
        )
    except scraper.ScrapeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")

    from app.models.data_verification import VerificationQueue

    queue = (
        db.query(VerificationQueue)
        .filter(VerificationQueue.scraped_record_id == record.id)
        .order_by(VerificationQueue.id.desc())
        .first()
    )
    return ImportRecordResponse(
        scraped_record_id=record.id,
        institution_id=queue.institution_id,
        queue_id=queue.id,
        status=record.status,
    )
