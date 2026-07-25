from fastapi import APIRouter, Depends, Query, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, List
import hashlib

from app.core.database import get_db
from app.core.elasticsearch import (
    search_institutions,
    get_search_suggestions,
    get_elasticsearch_client
)
from app.core.security import get_current_user_optional
from app.models import Institution, User
from app.services.search import (
    fuzzy_search,
    did_you_mean,
    personalized_search,
    get_suggestions_for_user
)

router = APIRouter()


def get_session_id(request: Request) -> str:
    """Generate session ID for anonymous personalization."""
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
    user_agent = request.headers.get("user-agent", "")
    data = f"{ip}:{user_agent}"
    return hashlib.md5(data.encode()).hexdigest()[:16]

@router.get("/autocomplete")
def autocomplete(
    q: str = Query(..., min_length=2, description="Search prefix"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Autocomplete search for institutions."""
    search_filter = f"%{q}%"
    institutions = (
        db.query(Institution)
        .filter(
            Institution.is_active == True,
            Institution.name_en.ilike(search_filter) | Institution.short_name.ilike(search_filter)
        )
        .limit(limit)
        .all()
    )
    
    # Try Elasticsearch suggestions first
    es_suggestions = get_search_suggestions(q, limit)
    
    if es_suggestions:
        return {
            "query": q,
            "suggestions": [{"text": s} for s in es_suggestions],
            "source": "elasticsearch"
        }
    
    # Fallback to database
    return {
        "query": q,
        "suggestions": [
            {
                "id": inst.id,
                "name": inst.name_en,
                "short_name": inst.short_name,
                "slug": inst.slug,
                "type": inst.type.name if inst.type else None
            }
            for inst in institutions
        ],
        "source": "database"
    }

@router.get("/popular-queries")
def popular_searches(
    db: Session = Depends(get_db)
):
    """Get popular/most searched institutions."""
    popular = (
        db.query(Institution)
        .filter(Institution.is_active == True)
        .order_by(Institution.search_count.desc())
        .limit(10)
        .all()
    )
    
    return {
        "popular_searches": [
            {
                "id": inst.id,
                "name": inst.name_en,
                "slug": inst.slug,
                "search_count": inst.search_count
            }
            for inst in popular
        ]
    }

@router.get("/advanced")
def advanced_search(
    q: Optional[str] = Query(None, description="Search query"),
    type_id: Optional[int] = Query(None, description="Filter by institution type"),
    type_name: Optional[str] = Query(None, description="Filter by type name"),
    division_name: Optional[str] = Query(None, description="Filter by division"),
    district_name: Optional[str] = Query(None, description="Filter by district"),
    verification_status: Optional[str] = Query(None, description="Filter by verification status"),
    is_featured: Optional[bool] = Query(None, description="Filter featured institutions"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Advanced search with Elasticsearch (fallback to database)."""
    
    # Check if Elasticsearch is available
    es_client = get_elasticsearch_client()
    
    if es_client:
        # Build filters
        filters = {}
        if type_id:
            filters['type_id'] = type_id
        if type_name:
            filters['type_name'] = type_name
        if division_name:
            filters['division_name'] = division_name
        if district_name:
            filters['district_name'] = district_name
        if verification_status:
            filters['verification_status'] = verification_status
        if is_featured is not None:
            filters['is_featured'] = is_featured
        
        # Elasticsearch search
        results = search_institutions(
            query=q or "",
            filters=filters if filters else None,
            page=page,
            page_size=page_size
        )
        
        return {
            **results,
            "source": "elasticsearch",
            "query": q
        }
    
    # Fallback to database search
    query = db.query(Institution).filter(Institution.is_active == True)
    
    if q:
        search_filter = f"%{q}%"
        query = query.filter(
            Institution.name_en.ilike(search_filter) |
            Institution.short_name.ilike(search_filter) |
            Institution.address.ilike(search_filter)
        )
    
    if type_id:
        query = query.filter(Institution.type_id == type_id)
    
    if verification_status:
        query = query.filter(Institution.verification_status == verification_status)
    
    if is_featured is not None:
        query = query.filter(Institution.is_featured == is_featured)
    
    # Order by featured first, then relevance
    query = query.order_by(
        Institution.is_featured.desc(),
        Institution.name_en
    )
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [
            {
                "id": inst.id,
                "name_en": inst.name_en,
                "name_bn": inst.name_bn,
                "short_name": inst.short_name,
                "slug": inst.slug,
                "type_id": inst.type_id,
                "type_name": inst.type.name if inst.type else None,
                "established_year": inst.established_year,
                "address": inst.address,
                "division_name": inst.upazila.district.division.name_en if inst.upazila and inst.upazila.district else None,
                "district_name": inst.upazila.district.name_en if inst.upazila else None,
                "verification_status": inst.verification_status,
                "is_featured": inst.is_featured,
                "view_count": inst.view_count
            }
            for inst in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "source": "database",
        "query": q
    }


@router.get("/fuzzy")
def fuzzy_search_endpoint(
    q: str = Query(..., min_length=2, description="Search query (with typo tolerance)"),
    threshold: float = Query(0.6, ge=0.1, le=1.0, description="Minimum similarity score"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Fuzzy search for typo-tolerant matching.
    
    Returns institutions even if the query contains typos or spelling errors.
    Each result includes a fuzzy_score indicating match quality.
    """
    results = fuzzy_search(db, q, threshold=threshold, limit=limit)
    
    # Get spell suggestions
    suggestions = did_you_mean(db, q, limit=3)
    
    return {
        "query": q,
        "results": results,
        "count": len(results),
        "suggestions": suggestions,
        "threshold": threshold
    }


@router.get("/did-you-mean")
def spell_suggestions(
    q: str = Query(..., min_length=3, description="Search query to check"),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Get spell correction suggestions for a search query.
    
    Returns institution names that are similar to the query.
    """
    suggestions = did_you_mean(db, q, limit=limit)
    
    return {
        "query": q,
        "suggestions": suggestions,
        "has_corrections": len(suggestions) > 0
    }


@router.get("/personalized")
def personalized_search_endpoint(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    type_id: Optional[int] = Query(None, description="Filter by institution type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Search with personalization based on user behavior.
    
    Results are re-ranked based on:
    - Recent search history
    - Previously viewed institutions
    - Common keywords in user's searches
    
    Works for both logged-in users and anonymous sessions.
    """
    user_id = current_user.id if current_user else None
    session_id = get_session_id(request) if not current_user else None
    
    filters = {}
    if type_id:
        filters['type_id'] = type_id
    
    results = personalized_search(
        db=db,
        query=q or "",
        user_id=user_id,
        session_id=session_id,
        page=page,
        page_size=page_size,
        filters=filters if filters else None
    )
    
    return results


@router.get("/suggestions-for-you")
def personalized_suggestions(
    request: Request,
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get personalized institution suggestions based on user behavior.
    
    Returns institutions the user might be interested in based on:
    - Recently viewed institutions
    - Search keywords
    - Viewing patterns
    """
    user_id = current_user.id if current_user else None
    session_id = get_session_id(request) if not current_user else None
    
    suggestions = get_suggestions_for_user(
        db=db,
        user_id=user_id,
        session_id=session_id,
        limit=limit
    )
    
    return {
        "suggestions": suggestions,
        "count": len(suggestions),
        "personalized": user_id is not None or session_id is not None
    }
