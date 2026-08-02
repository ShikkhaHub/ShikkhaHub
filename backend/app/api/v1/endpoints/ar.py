"""Augmented Reality (AR) campus tour endpoints.

Exposes the spatial data needed to power AR tours on mobile devices:

- Nearby POI discovery from the user's GPS position
- Campus POI listing / POI detail with lightweight assets
- Guided tours with wayfinding legs (distance + bearing between stops)
- Admin CRUD for POIs, tours, stops and assets

The client combines GPS/compass data from the device with these coordinates
to anchor AR overlays to the real world.
"""

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.ar import ARAsset, CampusPOI, CampusTour, TourStop
from app.models.user import User
from app.schemas.ar import (
    ARAssetCreate,
    ARAssetResponse,
    CampusPOICreate,
    CampusPOIResponse,
    CampusTourCreate,
    CampusTourResponse,
    GuidedTourResponse,
    NearbyResponse,
    TourStopBase,
    TourStopResponse,
)
from app.services.ar_tours import ARTourService

router = APIRouter()


# ---------------------------------------------------------------------------
# Discovery (public)
# ---------------------------------------------------------------------------


@router.get("/nearby", response_model=NearbyResponse)
def find_nearby_pois(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(1000, ge=10, le=50000),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Find AR points of interest near the user's GPS position."""
    return ARTourService.find_nearby(
        db, lat=lat, lng=lng, radius_m=radius_m, category=category, limit=limit
    )


@router.get("/campuses/{campus_id}/pois", response_model=List[CampusPOIResponse])
def list_campus_pois(
    campus_id: int,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List active AR points of interest for a campus."""
    return ARTourService.list_campus_pois(db, campus_id, category=category)


@router.get("/pois/{poi_id}", response_model=CampusPOIResponse)
def get_poi(poi_id: int, db: Session = Depends(get_db)):
    """Get a single AR point of interest with its assets."""
    poi = db.query(CampusPOI).filter(CampusPOI.id == poi_id).first()
    if poi is None:
        raise HTTPException(status_code=404, detail="POI not found")
    return ARTourService.poi_with_assets(poi)


@router.get("/campuses/{campus_id}/tours", response_model=List[CampusTourResponse])
def list_campus_tours(campus_id: int, db: Session = Depends(get_db)):
    """List curated AR tours for a campus."""
    return ARTourService.list_campus_tours(db, campus_id)


@router.get("/tours/{tour_id}", response_model=CampusTourResponse)
def get_tour(tour_id: int, db: Session = Depends(get_db)):
    """Get a tour with its ordered stops."""
    tour = ARTourService.get_tour(db, tour_id)
    if tour is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour


@router.get("/tours/{tour_id}/guide", response_model=GuidedTourResponse)
def get_guided_tour(tour_id: int, db: Session = Depends(get_db)):
    """Get a guided tour with wayfinding legs between consecutive stops.

    Each step includes `distance_from_prev_m` and `bearing_from_prev_deg`,
    which the AR client uses to draw directional arrows.
    """
    tour = ARTourService.guided_tour(db, tour_id)
    if tour is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour


# ---------------------------------------------------------------------------
# Admin CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/campuses/{campus_id}/pois",
    response_model=CampusPOIResponse,
    status_code=201,
)
def create_poi(
    campus_id: int,
    payload: CampusPOICreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create an AR point of interest on a campus (admin)."""
    from app.models.institution_detail import Campus

    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if campus is None:
        raise HTTPException(status_code=404, detail="Campus not found")
    data = payload.model_dump()
    if data.get("info_tags") is not None:
        data["info_tags"] = json.dumps(data["info_tags"])
    poi = CampusPOI(
        campus_id=campus_id,
        institution_id=campus.institution_id,
        **data,
    )
    db.add(poi)
    db.commit()
    db.refresh(poi)
    return ARTourService.poi_with_assets(poi)


@router.post(
    "/campuses/{campus_id}/tours",
    response_model=CampusTourResponse,
    status_code=201,
)
def create_tour(
    campus_id: int,
    payload: CampusTourCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Create a curated AR tour for a campus (admin)."""
    from app.models.institution_detail import Campus

    campus = db.query(Campus).filter(Campus.id == campus_id).first()
    if campus is None:
        raise HTTPException(status_code=404, detail="Campus not found")
    tour = CampusTour(
        campus_id=campus_id,
        institution_id=campus.institution_id,
        **payload.model_dump(),
    )
    db.add(tour)
    db.commit()
    db.refresh(tour)
    return tour


@router.post(
    "/tours/{tour_id}/stops",
    response_model=TourStopResponse,
    status_code=201,
)
def add_tour_stop(
    tour_id: int,
    payload: TourStopBase,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Add a POI to a tour at a given position (admin)."""
    tour = db.query(CampusTour).filter(CampusTour.id == tour_id).first()
    if tour is None:
        raise HTTPException(status_code=404, detail="Tour not found")
    poi = db.query(CampusPOI).filter(CampusPOI.id == payload.poi_id).first()
    if poi is None:
        raise HTTPException(status_code=404, detail="POI not found")
    stop = TourStop(tour_id=tour_id, **payload.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop


@router.post("/pois/{poi_id}/assets", response_model=ARAssetResponse, status_code=201)
def add_poi_asset(
    poi_id: int,
    payload: ARAssetCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Attach a lightweight AR asset to a POI (admin)."""
    poi = db.query(CampusPOI).filter(CampusPOI.id == poi_id).first()
    if poi is None:
        raise HTTPException(status_code=404, detail="POI not found")
    asset = ARAsset(poi_id=poi_id, **payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
