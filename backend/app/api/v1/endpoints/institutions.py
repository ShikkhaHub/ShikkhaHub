from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.core.database import get_db
from app.core.redis import cache_get, cache_set, get_institution_list_cache_key, get_institution_detail_cache_key
from app.models import Institution, InstitutionType, Upazila, District, Division
from app.schemas.institution import (
    InstitutionResponse, 
    InstitutionDetailResponse,
    InstitutionListResponse,
    InstitutionSearchRequest,
    InstitutionContactResponse,
    InstitutionRequirementResponse
)

router = APIRouter()

@router.get("/", response_model=InstitutionListResponse)
def list_institutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type_id: Optional[int] = None,
    division_id: Optional[int] = None,
    district_id: Optional[int] = None,
    upazila_id: Optional[int] = None,
    verification_status: Optional[str] = None,
    is_featured: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List institutions with filters and pagination (cached for 5 minutes)."""
    # Generate cache key
    cache_key = get_institution_list_cache_key(
        page=page,
        page_size=page_size,
        type_id=type_id,
        division_id=division_id,
        district_id=district_id,
        upazila_id=upazila_id,
        verification_status=verification_status,
        is_featured=is_featured
    )
    
    # Try to get from cache
    cached_data = cache_get(cache_key)
    if cached_data:
        return InstitutionListResponse(**cached_data)
    
    query = db.query(Institution)
    
    # Apply filters
    if type_id:
        query = query.filter(Institution.type_id == type_id)
    if upazila_id:
        query = query.filter(Institution.upazila_id == upazila_id)
    if verification_status:
        query = query.filter(Institution.verification_status == verification_status)
    if is_featured is not None:
        query = query.filter(Institution.is_featured == is_featured)
    
    # Location filters (requires joins)
    if district_id or division_id:
        query = query.join(Upazila).join(District)
        if district_id:
            query = query.filter(District.id == district_id)
        if division_id:
            query = query.join(Division).filter(Division.id == division_id)
    
    # Count total
    total = query.count()
    
    # Pagination
    institutions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Enhance with location names
    results = []
    for inst in institutions:
        data = {
            **inst.__dict__,
            "type_name": inst.type.name if inst.type else None,
            "upazila_name": inst.upazila.name_en if inst.upazila else None,
            "district_name": inst.upazila.district.name_en if inst.upazila else None,
            "division_name": inst.upazila.district.division.name_en if inst.upazila and inst.upazila.district else None,
        }
        results.append(InstitutionResponse.model_validate(data))
    
    return InstitutionListResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )

@router.get("/search", response_model=InstitutionListResponse)
def search_institutions(
    q: Optional[str] = Query(None, description="Search query"),
    type_id: Optional[int] = None,
    division_id: Optional[int] = None,
    district_id: Optional[int] = None,
    upazila_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search institutions by name, keywords, or description."""
    query = db.query(Institution).filter(Institution.is_active == True)
    
    # Full-text search (simplified - will use ILIKE for now, migrate to tsvector later)
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            Institution.name_en.ilike(search_filter) |
            Institution.name_bn.ilike(search_filter) |
            Institution.short_name.ilike(search_filter) |
            Institution.keywords.ilike(search_filter)
        )
    
    # Filters
    if type_id:
        query = query.filter(Institution.type_id == type_id)
    if upazila_id:
        query = query.filter(Institution.upazila_id == upazila_id)
    
    # Location joins
    if district_id or division_id:
        query = query.join(Upazila).join(District)
        if district_id:
            query = query.filter(District.id == district_id)
        if division_id:
            query = query.join(Division).filter(Division.id == division_id)
    
    # Prioritize verified and featured
    query = query.order_by(
        Institution.verification_status == "verified",
        Institution.is_featured.desc(),
        Institution.name_en
    )
    
    total = query.count()
    institutions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # Enhance responses
    results = []
    for inst in institutions:
        data = {
            **inst.__dict__,
            "type_name": inst.type.name if inst.type else None,
            "upazila_name": inst.upazila.name_en if inst.upazila else None,
            "district_name": inst.upazila.district.name_en if inst.upazila else None,
            "division_name": inst.upazila.district.division.name_en if inst.upazila and inst.upazila.district else None,
        }
        results.append(InstitutionResponse.model_validate(data))
    
    response = InstitutionListResponse(
        items=results,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
    
    # Cache for 5 minutes (300 seconds)
    cache_set(cache_key, response.model_dump(), expire=300)
    return response

@router.get("/types", response_model=List[dict])
def list_institution_types(db: Session = Depends(get_db)):
    """Get all institution types."""
    types = db.query(InstitutionType).order_by(InstitutionType.display_order).all()
    return [{"id": t.id, "name": t.name, "category": t.category} for t in types]

@router.get("/{slug}")
def get_institution(slug: str, db: Session = Depends(get_db)):
    """Get detailed institution information by slug."""
    institution = db.query(Institution).filter(Institution.slug == slug).first()
    
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Increment view count
    institution.view_count += 1
    db.commit()
    
    # Build response with related data
    data = {
        "id": institution.id,
        "name_en": institution.name_en,
        "name_bn": institution.name_bn,
        "short_name": institution.short_name,
        "slug": institution.slug,
        "type_id": institution.type_id,
        "established_year": institution.established_year,
        "upazila_id": institution.upazila_id,
        "address": institution.address,
        "latitude": institution.latitude,
        "longitude": institution.longitude,
        "phone": institution.phone,
        "email": institution.email,
        "website": institution.website,
        "description": institution.description,
        "history": institution.history,
        "verification_status": institution.verification_status,
        "is_featured": institution.is_featured,
        "view_count": institution.view_count,
        "data_source": institution.data_source,
        "last_updated": institution.last_updated,
        "type_name": institution.type.name if institution.type else None,
        "upazila_name": institution.upazila.name_en if institution.upazila else None,
        "district_name": institution.upazila.district.name_en if institution.upazila and institution.upazila.district else None,
        "division_name": institution.upazila.district.division.name_en if institution.upazila and institution.upazila.district and institution.upazila.district.division else None,
        "contacts": [],
        "requirements": [],
        "education_boards": [],
        "ugc_affiliations": [],
    }
    
    return data

@router.get("/by-id/{institution_id}", response_model=InstitutionDetailResponse)
def get_institution_by_id(institution_id: int, db: Session = Depends(get_db)):
    """Get institution by ID (redirects to slug-based endpoint internally)."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Same as slug endpoint
    data = {
        **institution.__dict__,
        "type_name": institution.type.name if institution.type else None,
        "upazila_name": institution.upazila.name_en if institution.upazila else None,
        "district_name": institution.upazila.district.name_en if institution.upazila else None,
        "division_name": institution.upazila.district.division.name_en if institution.upazila and institution.upazila.district else None,
        "contacts": [InstitutionContactResponse.model_validate(c) for c in institution.contacts],
        "requirements": [InstitutionRequirementResponse.model_validate(r) for r in institution.requirements],
        "education_boards": [{"id": b.id, "name": b.name_en, "short_code": b.short_code} for b in institution.education_boards],
        "ugc_affiliations": [{"id": u.id, "name": u.name_en, "type": u.commission_type} for u in institution.ugc_affiliations],
    }
    
    return InstitutionDetailResponse.model_validate(data)
