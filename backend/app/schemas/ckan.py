"""Pydantic schemas for the CKAN data catalog integration."""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class CKANResource(BaseModel):
    """A resource file/API inside a CKAN dataset."""

    name: Optional[str] = None
    url: str
    format: Optional[str] = None
    description: Optional[str] = None
    resource_type: Optional[str] = "primary"
    checksum: Optional[str] = None


class CKANDatasetCreate(BaseModel):
    """Dataset creation payload following the ShikkhaHub metadata standard."""

    title: str
    name: Optional[str] = None  # slug; auto-generated if omitted
    dataset_category: str = Field(
        ...,
        description="institutions | admission | academic_programs | results | "
        "rankings | scholarships | job_career | geographic",
    )
    description: str
    owner_org: Optional[str] = None
    tags: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    resources: Optional[List[CKANResource]] = None
    verification_status: str = "pending_review"
    source_url: Optional[str] = None
    source_type: Optional[str] = "manual"
    license_id: Optional[str] = "cc-by"
    language: Optional[List[str]] = ["en"]
    update_frequency: Optional[str] = "monthly"
    quality_score: Optional[float] = None
    version: Optional[str] = "1.0.0"
    extras: Optional[Dict[str, Any]] = None


class CKANDatasetUpdate(BaseModel):
    """Partial dataset update."""

    title: Optional[str] = None
    description: Optional[str] = None
    dataset_category: Optional[str] = None
    verification_status: Optional[str] = None
    tags: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    resources: Optional[List[CKANResource]] = None
    version: Optional[str] = None
    extras: Optional[Dict[str, Any]] = None


class CKANDatasetSearchResult(BaseModel):
    """A dataset in search results."""

    id: str
    name: str
    title: str
    dataset_category: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[Dict[str, Any]] = None
    verification_status: Optional[str] = None
    metadata_modified: Optional[str] = None
    version: Optional[str] = None
    resources: List[Dict[str, Any]] = Field(default_factory=list)
    tags: List[Dict[str, Any]] = Field(default_factory=list)
    extras: List[Dict[str, Any]] = Field(default_factory=list)


class CKANSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    count: int
    start: int
    rows: int


class CKANStatusResponse(BaseModel):
    enabled: bool
    healthy: Optional[bool] = None
    api_url: Optional[str] = None
    version: Optional[str] = None
    organization_count: Optional[int] = None
    group_count: Optional[int] = None
