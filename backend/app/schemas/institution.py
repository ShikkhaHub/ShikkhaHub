from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class InstitutionContactBase(BaseModel):
    contact_type: str
    name: Optional[str] = None
    designation: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False

class InstitutionContactResponse(InstitutionContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class InstitutionRequirementBase(BaseModel):
    requirement_type: str
    level: str
    min_gpa: Optional[float] = None
    required_subjects: Optional[str] = None
    admission_test_required: bool = False
    admission_test_details: Optional[str] = None
    application_process: Optional[str] = None
    documents_required: Optional[str] = None
    fees: Optional[str] = None
    deadlines: Optional[str] = None

class InstitutionRequirementResponse(InstitutionRequirementBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class InstitutionBase(BaseModel):
    name_en: str
    name_bn: Optional[str] = None
    short_name: Optional[str] = None
    type_id: int
    established_year: Optional[int] = None
    upazila_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name_en: Optional[str] = None
    name_bn: Optional[str] = None
    short_name: Optional[str] = None
    type_id: Optional[int] = None
    established_year: Optional[int] = None
    upazila_id: Optional[int] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    history: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = None

class InstitutionResponse(InstitutionBase):
    """Simplified institution response for lists."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    type_name: Optional[str] = None
    upazila_name: Optional[str] = None
    district_name: Optional[str] = None
    division_name: Optional[str] = None
    verification_status: str
    is_featured: bool
    view_count: int
    data_source: Optional[str] = None
    last_updated: datetime

class InstitutionDetailResponse(InstitutionResponse):
    """Full institution details with related data."""
    model_config = ConfigDict(from_attributes=True)
    
    # Extended info
    created_at: datetime
    search_count: int
    keywords: Optional[str] = None
    
    # Related data
    contacts: List[InstitutionContactResponse] = []
    requirements: List[InstitutionRequirementResponse] = []
    education_boards: List[Dict[str, Any]] = []
    ugc_affiliations: List[Dict[str, Any]] = []

class InstitutionListResponse(BaseModel):
    """Paginated institution list response."""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[InstitutionResponse]
    total: int
    page: int
    page_size: int
    pages: int

class InstitutionSearchRequest(BaseModel):
    """Search request parameters."""
    q: Optional[str] = None
    type_id: Optional[int] = None
    division_id: Optional[int] = None
    district_id: Optional[int] = None
    upazila_id: Optional[int] = None
    verification_status: Optional[str] = "verified"
    is_featured: Optional[bool] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "name_en"
    sort_order: str = "asc"
