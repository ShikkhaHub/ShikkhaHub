"""Pydantic schemas for the web scraping API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FieldSelectorIn(BaseModel):
    """One CSS-selector extraction rule."""

    field: str
    selector: Optional[str] = None
    attribute: Optional[str] = None
    multiple: bool = False
    transform: str = "text"


class ScrapeConfigIn(BaseModel):
    """Extraction plan for a scrape (validated selectors)."""

    record_type: str = "institution"
    item_selector: Optional[str] = None
    fields: List[FieldSelectorIn] = Field(default_factory=list)
    link_selector: Optional[str] = None
    detail_fields: List[FieldSelectorIn] = Field(default_factory=list)
    pagination_selector: Optional[str] = None
    max_pages: int = Field(1, ge=1, le=20)
    max_items: int = Field(0, ge=0)
    headers: Dict[str, str] = Field(default_factory=dict)


class ExtractRequest(BaseModel):
    """Dry-run: fetch one URL and extract records without persisting."""

    url: str
    config: ScrapeConfigIn


class ExtractResponse(BaseModel):
    url: str
    records: List[Dict[str, Any]]
    stats: Dict[str, Any]


class RawSourceCreate(BaseModel):
    name: str
    name_bn: Optional[str] = None
    source_type: str = "government"
    base_url: Optional[str] = None
    description: Optional[str] = None
    reliability_score: float = Field(0.5, ge=0.0, le=1.0)
    is_active: bool = True


class RawSourceResponse(RawSourceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[Any] = None


class JobCreate(BaseModel):
    """Trigger a scrape job against a registered source."""

    raw_source_id: int
    start_url: str
    preset: Optional[str] = None
    config: Optional[ScrapeConfigIn] = None


class JobRunResponse(BaseModel):
    job_id: int
    status: str
    records_found: int
    records_imported: int
    records_failed: int
    errors: Optional[str] = None


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    raw_source_id: int
    status: str
    records_found: int
    records_imported: int
    records_failed: int
    error_log: Optional[str] = None
    started_at: Optional[Any] = None
    completed_at: Optional[Any] = None
    created_at: Optional[Any] = None


class RecordResponse(BaseModel):
    """Serialized ScrapedRecord (raw_data parsed to dict)."""

    id: int
    scrape_job_id: int
    record_type: str
    external_id: Optional[str] = None
    checksum: str
    status: str
    source_url: Optional[str] = None
    confidence_score: Optional[float] = None
    created_at: Optional[Any] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class ImportRecordRequest(BaseModel):
    institution_type_id: Optional[int] = None


class ImportRecordResponse(BaseModel):
    scraped_record_id: int
    institution_id: int
    queue_id: int
    status: str
