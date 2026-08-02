"""Pydantic schemas for Augmented Reality (AR) campus tours."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


class ARAssetBase(BaseModel):
    asset_type: str  # glb, usdz, image, video, audio
    url: str
    thumbnail_url: Optional[str] = None
    size_kb: Optional[int] = None
    format: Optional[str] = None
    is_primary: bool = False


class ARAssetCreate(ARAssetBase):
    pass


class ARAssetResponse(ARAssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    poi_id: int
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Points of interest
# ---------------------------------------------------------------------------


class CampusPOIBase(BaseModel):
    campus_id: int
    institution_id: int
    name_en: str
    name_bn: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    heading_deg: Optional[float] = None
    radius_m: Optional[float] = 15.0
    marker_type: str = "gps"
    marker_image_url: Optional[str] = None
    title: Optional[str] = None
    short_description: Optional[str] = None
    info_tags: Optional[List[str]] = None
    department_summary: Optional[str] = None
    opening_hours: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CampusPOICreate(BaseModel):
    """Path-bound create: campus & institution come from the URL."""

    name_en: str
    name_bn: Optional[str] = None
    category: str
    subcategory: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude_m: Optional[float] = None
    heading_deg: Optional[float] = None
    radius_m: Optional[float] = 15.0
    marker_type: str = "gps"
    marker_image_url: Optional[str] = None
    title: Optional[str] = None
    short_description: Optional[str] = None
    info_tags: Optional[List[str]] = None
    department_summary: Optional[str] = None
    opening_hours: Optional[str] = None
    display_order: int = 0
    is_active: bool = True


class CampusPOIResponse(CampusPOIBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    assets: List[ARAssetResponse] = []


# ---------------------------------------------------------------------------
# Tours
# ---------------------------------------------------------------------------


class TourStopBase(BaseModel):
    poi_id: int
    position: int = 0
    narration: Optional[str] = None
    dwell_seconds: int = 30


class TourStopResponse(TourStopBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tour_id: int
    poi: Optional[CampusPOIResponse] = None


class CampusTourBase(BaseModel):
    campus_id: int
    institution_id: int
    title: str
    title_bn: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    distance_m: Optional[float] = None
    difficulty: str = "easy"
    is_active: bool = True


class CampusTourCreate(BaseModel):
    """Path-bound create: campus & institution come from the URL."""

    title: str
    title_bn: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    distance_m: Optional[float] = None
    difficulty: str = "easy"
    is_active: bool = True


class CampusTourResponse(CampusTourBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: Optional[datetime] = None
    stops: List[TourStopResponse] = []


# ---------------------------------------------------------------------------
# Wayfinding / nearby responses
# ---------------------------------------------------------------------------


class NearbyPOIResponse(BaseModel):
    poi: CampusPOIResponse
    distance_m: float
    bearing_deg: Optional[float] = None
    estimated_walk_minutes: Optional[float] = None


class NearbyResponse(BaseModel):
    user_lat: float
    user_lng: float
    radius_m: float
    items: List[NearbyPOIResponse]
    total: int


class TourStepResponse(BaseModel):
    position: int
    poi: CampusPOIResponse
    distance_from_prev_m: Optional[float] = None
    bearing_from_prev_deg: Optional[float] = None
    narration: Optional[str] = None
    dwell_seconds: Optional[int] = None


class GuidedTourResponse(BaseModel):
    tour: CampusTourResponse
    total_distance_m: float
    steps: List[TourStepResponse]
