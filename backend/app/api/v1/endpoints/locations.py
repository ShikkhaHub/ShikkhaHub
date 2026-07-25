from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.redis import cache_get, cache_set, get_divisions_cache_key
from app.models import Division, District, Upazila
from app.schemas.location import (
    DivisionResponse, 
    DistrictResponse, 
    UpazilaResponse,
    LocationHierarchyResponse
)

router = APIRouter()

@router.get("/divisions", response_model=List[DivisionResponse])
def list_divisions(db: Session = Depends(get_db)):
    """Get all divisions with district counts (cached for 1 hour)."""
    cache_key = get_divisions_cache_key()
    
    # Try to get from cache
    cached_data = cache_get(cache_key)
    if cached_data:
        return [DivisionResponse(**item) for item in cached_data]
    
    # Query database
    divisions = db.query(Division).all()
    results = []
    for div in divisions:
        # Count districts for this division
        district_count = db.query(District).filter(District.division_id == div.id).count()
        results.append(DivisionResponse(
            id=div.id,
            name_en=div.name_en,
            name_bn=div.name_bn,
            code=div.code,
            district_count=district_count
        ))
    
    # Cache the results
    cache_set(cache_key, [r.model_dump() for r in results], expire=3600)
    return results

@router.get("/divisions/{division_id}/districts", response_model=List[DistrictResponse])
def list_districts_by_division(division_id: int, db: Session = Depends(get_db)):
    """Get districts within a division."""
    division = db.query(Division).filter(Division.id == division_id).first()
    if not division:
        raise HTTPException(status_code=404, detail="Division not found")
    
    districts = db.query(District).filter(District.division_id == division_id).all()
    results = []
    for dist in districts:
        # Count upazilas for this district
        upazila_count = db.query(Upazila).filter(Upazila.district_id == dist.id).count()
        results.append(DistrictResponse(
            id=dist.id,
            name_en=dist.name_en,
            name_bn=dist.name_bn,
            code=dist.code,
            division_id=dist.division_id,
            division_name=division.name_en,
            upazila_count=upazila_count
        ))
    return results

@router.get("/districts/{district_id}/upazilas", response_model=List[UpazilaResponse])
def list_upazilas_by_district(district_id: int, db: Session = Depends(get_db)):
    """Get upazilas within a district."""
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    upazilas = db.query(Upazila).filter(Upazila.district_id == district_id).all()
    results = []
    for upz in upazilas:
        results.append(UpazilaResponse(
            id=upz.id,
            name_en=upz.name_en,
            name_bn=upz.name_bn,
            code=upz.code,
            district_id=upz.district_id,
            district_name=district.name_en,
            division_name=district.division.name_en if district.division else None
        ))
    return results

@router.get("/hierarchy", response_model=LocationHierarchyResponse)
def get_location_hierarchy(db: Session = Depends(get_db)):
    """Get complete location hierarchy: Divisions -> Districts -> Upazilas."""
    divisions = db.query(Division).all()
    total_districts = db.query(District).count()
    total_upazilas = db.query(Upazila).count()
    
    division_responses = []
    for div in divisions:
        # Count districts for this division
        district_count = db.query(District).filter(District.division_id == div.id).count()
        division_responses.append(DivisionResponse(
            id=div.id,
            name_en=div.name_en,
            name_bn=div.name_bn,
            code=div.code,
            district_count=district_count
        ))
    
    return LocationHierarchyResponse(
        divisions=division_responses,
        total_districts=total_districts,
        total_upazilas=total_upazilas
    )
