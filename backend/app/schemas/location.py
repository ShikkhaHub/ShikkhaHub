from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class DivisionBase(BaseModel):
    name_en: str
    name_bn: Optional[str] = None
    code: Optional[str] = None

class DivisionCreate(DivisionBase):
    pass

class DivisionResponse(DivisionBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    district_count: Optional[int] = None

class DistrictBase(BaseModel):
    name_en: str
    name_bn: Optional[str] = None
    code: Optional[str] = None
    division_id: int

class DistrictCreate(DistrictBase):
    pass

class DistrictResponse(DistrictBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    division_name: Optional[str] = None
    upazila_count: Optional[int] = None

class UpazilaBase(BaseModel):
    name_en: str
    name_bn: Optional[str] = None
    code: Optional[str] = None
    district_id: int

class UpazilaCreate(UpazilaBase):
    pass

class UpazilaResponse(UpazilaBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    district_name: Optional[str] = None
    division_name: Optional[str] = None

class LocationHierarchyResponse(BaseModel):
    """Full location hierarchy: Division -> District -> Upazila."""
    model_config = ConfigDict(from_attributes=True)
    
    divisions: List[DivisionResponse]
    total_districts: int
    total_upazilas: int
