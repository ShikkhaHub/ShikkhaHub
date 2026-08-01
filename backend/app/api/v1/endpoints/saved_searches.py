"""
Saved Searches API Endpoints
Handles CRUD operations for user's saved searches
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.saved_search import SavedSearch, SavedSearchHit
from app.models.user import User
from app.schemas.saved_search import (
    SavedSearchCreate,
    SavedSearchUpdate,
    SavedSearchResponse,
    SavedSearchListResponse,
)

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])


@router.post("", response_model=SavedSearchResponse)
async def create_saved_search(
    saved_search: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new saved search for the current user
    
    Args:
        saved_search: Search criteria to save
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created saved search object
    """
    # Create new saved search
    new_search = SavedSearch(
        id=str(uuid4()),
        user_id=current_user.id,
        name=saved_search.name,
        description=saved_search.description,
        query=saved_search.query,
        institution_types=saved_search.institution_types,
        divisions=saved_search.divisions,
        districts=saved_search.districts,
        subjects=saved_search.subjects,
        min_rating=saved_search.min_rating,
        sort_by=saved_search.sort_by,
        limit=saved_search.limit,
        notify_new_matches=saved_search.notify_new_matches,
        notify_institution_updates=saved_search.notify_institution_updates,
        notification_frequency=saved_search.notification_frequency,
    )
    
    db.add(new_search)
    db.commit()
    db.refresh(new_search)
    
    return new_search


@router.get("", response_model=SavedSearchListResponse)
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List all saved searches for the current user
    
    Args:
        current_user: Current authenticated user
        skip: Number of results to skip
        limit: Number of results to return
        db: Database session
        
    Returns:
        List of saved searches
    """
    query = db.query(SavedSearch).filter(SavedSearch.user_id == current_user.id)
    total = query.count()
    
    searches = query.order_by(SavedSearch.created_at.desc()).offset(skip).limit(limit).all()
    
    return SavedSearchListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=searches,
    )


@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific saved search
    
    Args:
        search_id: ID of saved search
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Saved search object
    """
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    return saved_search


@router.patch("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: str,
    update_data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a saved search
    
    Args:
        search_id: ID of saved search
        update_data: Updated search criteria
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated saved search object
    """
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(saved_search, key, value)
    
    db.commit()
    db.refresh(saved_search)
    
    return saved_search


@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a saved search
    
    Args:
        search_id: ID of saved search
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    db.delete(saved_search)
    db.commit()
    
    return {"message": "Saved search deleted successfully"}


@router.post("/{search_id}/run", response_model=dict)
async def run_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a saved search and return results
    
    Args:
        search_id: ID of saved search
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Search results
    """
    from app.core.search import search_institutions
    
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Build search parameters from saved search
    search_params = {
        "query": saved_search.query,
        "types": saved_search.institution_types,
        "divisions": saved_search.divisions,
        "districts": saved_search.districts,
        "subjects": saved_search.subjects,
        "min_rating": saved_search.min_rating,
        "sort_by": saved_search.sort_by,
        "limit": saved_search.limit,
    }
    
    # Execute search
    results = search_institutions(search_params, db)
    
    # Update last run time and result count
    from datetime import datetime
    saved_search.last_run_at = datetime.utcnow()
    saved_search.result_count = len(results)
    db.commit()
    
    return {
        "saved_search_id": search_id,
        "result_count": len(results),
        "results": results,
    }


@router.post("/{search_id}/toggle-notifications")
async def toggle_notifications(
    search_id: str,
    enable: bool = Query(...),
    frequency: str = Query("weekly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Toggle notifications for a saved search
    
    Args:
        search_id: ID of saved search
        enable: Whether to enable notifications
        frequency: Notification frequency (daily, weekly)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated saved search object
    """
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    saved_search.notify_new_matches = enable
    saved_search.notification_frequency = frequency if enable else None
    
    db.commit()
    db.refresh(saved_search)
    
    return saved_search


@router.get("/{search_id}/results")
async def get_saved_search_results(
    search_id: str,
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get cached results for a saved search
    
    Args:
        search_id: ID of saved search
        current_user: Current authenticated user
        skip: Number of results to skip
        limit: Number of results to return
        db: Database session
        
    Returns:
        Cached search results
    """
    saved_search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id,
    ).first()
    
    if not saved_search:
        raise HTTPException(status_code=404, detail="Saved search not found")
    
    # Get cached results
    hits = db.query(SavedSearchHit).filter(
        SavedSearchHit.saved_search_id == search_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(SavedSearchHit).filter(
        SavedSearchHit.saved_search_id == search_id
    ).count()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": hits,
        "last_run_at": saved_search.last_run_at,
    }
