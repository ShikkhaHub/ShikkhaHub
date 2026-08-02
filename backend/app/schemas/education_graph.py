"""Pydantic schemas for the national education knowledge graph entities."""

from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Institution detail: campuses
# ---------------------------------------------------------------------------


class CampusBase(BaseModel):
    institution_id: int
    name_en: str
    name_bn: Optional[str] = None
    campus_type: str = "main"
    division_id: Optional[int] = None
    district_id: Optional[int] = None
    upazila_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_sqft: Optional[float] = None
    established_year: Optional[int] = None
    is_active: bool = True


class CampusCreate(CampusBase):
    pass


class CampusUpdate(BaseModel):
    name_en: Optional[str] = None
    name_bn: Optional[str] = None
    campus_type: Optional[str] = None
    division_id: Optional[int] = None
    district_id: Optional[int] = None
    upazila_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_sqft: Optional[float] = None
    established_year: Optional[int] = None
    is_active: Optional[bool] = None


class CampusResponse(CampusBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Facilities
# ---------------------------------------------------------------------------


class FacilityTypeBase(BaseModel):
    name: str
    name_bn: Optional[str] = None
    icon: Optional[str] = None
    display_order: int = 0


class FacilityTypeResponse(FacilityTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class InstitutionFacilityBase(BaseModel):
    institution_id: int
    facility_type_id: int
    is_available: bool = True
    capacity: Optional[int] = None
    notes: Optional[str] = None


class InstitutionFacilityCreate(BaseModel):
    """Path-bound create: institution comes from the URL."""

    facility_type_id: int
    is_available: bool = True
    capacity: Optional[int] = None
    notes: Optional[str] = None


class InstitutionFacilityResponse(InstitutionFacilityBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    facility_type: Optional[FacilityTypeResponse] = None


# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------


class GalleryImageBase(BaseModel):
    institution_id: int
    title: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    category: str = "campus"
    sort_order: int = 0


class GalleryImageCreate(BaseModel):
    """Path-bound create: institution comes from the URL."""

    title: Optional[str] = None
    url: str
    thumbnail_url: Optional[str] = None
    caption: Optional[str] = None
    category: str = "campus"
    sort_order: int = 0


class GalleryImageResponse(GalleryImageBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Rankings & Accreditations
# ---------------------------------------------------------------------------


class InstitutionRankingBase(BaseModel):
    institution_id: int
    ranking_type: str
    category: Optional[str] = None
    year: int
    rank: int
    score: Optional[float] = None
    source: Optional[str] = None
    description: Optional[str] = None


class InstitutionRankingCreate(BaseModel):
    """Path-bound create: institution comes from the URL."""

    ranking_type: str
    category: Optional[str] = None
    year: int
    rank: int
    score: Optional[float] = None
    source: Optional[str] = None
    description: Optional[str] = None


class InstitutionRankingResponse(InstitutionRankingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class AccreditationBase(BaseModel):
    institution_id: int
    accrediting_body: str
    accreditation_type: Optional[str] = None
    certificate_number: Optional[str] = None
    awarded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str = "active"


class AccreditationCreate(BaseModel):
    """Path-bound create: institution comes from the URL."""

    accrediting_body: str
    accreditation_type: Optional[str] = None
    certificate_number: Optional[str] = None
    awarded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    status: str = "active"


class AccreditationResponse(AccreditationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Announcements: admissions, notices, scholarships
# ---------------------------------------------------------------------------


class AdmissionBase(BaseModel):
    institution_id: int
    institution_course_id: Optional[int] = None
    title: str
    session: Optional[str] = None
    program: Optional[str] = None
    application_start: Optional[datetime] = None
    application_end: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    minimum_gpa: Optional[float] = None
    minimum_gpa_scale: float = 5.0
    total_seats: Optional[int] = None
    application_fee: Optional[float] = None
    eligibility: Optional[str] = None
    required_documents: Optional[str] = None
    application_link: Optional[str] = None
    status: str = "open"


class AdmissionCreate(AdmissionBase):
    pass


class AdmissionUpdate(BaseModel):
    title: Optional[str] = None
    session: Optional[str] = None
    program: Optional[str] = None
    application_start: Optional[datetime] = None
    application_end: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    minimum_gpa: Optional[float] = None
    minimum_gpa_scale: Optional[float] = None
    total_seats: Optional[int] = None
    application_fee: Optional[float] = None
    eligibility: Optional[str] = None
    required_documents: Optional[str] = None
    application_link: Optional[str] = None
    status: Optional[str] = None


class AdmissionResponse(AdmissionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class NoticeBase(BaseModel):
    institution_id: int
    title: str
    body: Optional[str] = None
    category: str = "general"
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    is_important: bool = False
    attachment_url: Optional[str] = None


class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    publish_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    is_important: Optional[bool] = None
    attachment_url: Optional[str] = None


class NoticeResponse(NoticeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ScholarshipBase(BaseModel):
    institution_id: int
    name: str
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: str = "BDT"
    scholarship_type: str = "merit"
    eligibility: Optional[str] = None
    application_deadline: Optional[datetime] = None
    is_active: bool = True


class ScholarshipCreate(ScholarshipBase):
    pass


class ScholarshipUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    scholarship_type: Optional[str] = None
    eligibility: Optional[str] = None
    application_deadline: Optional[datetime] = None
    is_active: Optional[bool] = None


class ScholarshipResponse(ScholarshipBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Course offerings & saved institutions
# ---------------------------------------------------------------------------


class InstitutionCourseBase(BaseModel):
    institution_id: int
    course_id: int
    total_seats: Optional[int] = None
    reserved_seats: Optional[int] = None
    shift: str = "morning"
    fee: Optional[float] = None
    fee_currency: str = "BDT"
    language: str = "bangla"
    intake_year: Optional[int] = None
    duration_years: Optional[float] = None
    status: str = "open"
    notes: Optional[str] = None


class InstitutionCourseCreate(BaseModel):
    """Path-bound create: institution comes from the URL."""

    course_id: int
    total_seats: Optional[int] = None
    reserved_seats: Optional[int] = None
    shift: str = "morning"
    fee: Optional[float] = None
    fee_currency: str = "BDT"
    language: str = "bangla"
    intake_year: Optional[int] = None
    duration_years: Optional[float] = None
    status: str = "open"
    notes: Optional[str] = None


class InstitutionCourseUpdate(BaseModel):
    total_seats: Optional[int] = None
    reserved_seats: Optional[int] = None
    shift: Optional[str] = None
    fee: Optional[float] = None
    fee_currency: Optional[str] = None
    language: Optional[str] = None
    intake_year: Optional[int] = None
    duration_years: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class InstitutionCourseResponse(InstitutionCourseBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    course_name: Optional[str] = None


class SavedInstitutionBase(BaseModel):
    institution_id: int
    note: Optional[str] = None


class SavedInstitutionCreate(BaseModel):
    note: Optional[str] = None


class SavedInstitutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    institution_id: int
    note: Optional[str] = None
    created_at: datetime
    institution_name: Optional[str] = None
    institution_slug: Optional[str] = None


# ---------------------------------------------------------------------------
# Pagination helpers
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    items: List[Any] = []
    total: int
    page: int
    page_size: int
    pages: int
