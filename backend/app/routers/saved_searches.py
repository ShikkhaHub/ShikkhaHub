"""
Saved Searches API
Allows users to save and manage search queries with notifications
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/saved-searches", tags=["saved-searches"])

# Models
class SavedSearchCreate(BaseModel):
    """Create saved search request"""
    name: str
    query: str
    filters: dict = {}  # {type, division, district, etc}
    notify_on_new: bool = True
    notify_frequency: str = "daily"  # immediate, daily, weekly

class SavedSearchUpdate(BaseModel):
    """Update saved search"""
    name: str | None = None
    notify_on_new: bool | None = None
    notify_frequency: str | None = None

class SavedSearchResponse(BaseModel):
    """Saved search response"""
    id: str
    user_id: str
    name: str
    query: str
    filters: dict
    notify_on_new: bool
    notify_frequency: str
    match_count: int
    last_updated: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class SearchNotificationResponse(BaseModel):
    """Notification response"""
    id: str
    saved_search_id: str
    new_institutions: list
    notification_date: datetime

# Routes

@router.post("/", response_model=SavedSearchResponse)
async def create_saved_search(
    data: SavedSearchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save a search query with name and preferences"""
    
    saved_search = SavedSearch(
        user_id=current_user.id,
        name=data.name,
        query=data.query,
        filters=data.filters,
        notify_on_new=data.notify_on_new,
        notify_frequency=data.notify_frequency,
        match_count=0,
        last_updated=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    db.add(saved_search)
    db.commit()
    db.refresh(saved_search)
    
    return saved_search

@router.get("/", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all saved searches for current user"""
    
    searches = db.query(SavedSearch).filter(
        SavedSearch.user_id == current_user.id
    ).all()
    
    return searches

@router.get("/{search_id}", response_model=SavedSearchResponse)
async def get_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific saved search details"""
    
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    return search

@router.patch("/{search_id}", response_model=SavedSearchResponse)
async def update_saved_search(
    search_id: str,
    data: SavedSearchUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update saved search settings"""
    
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    if data.name is not None:
        search.name = data.name
    if data.notify_on_new is not None:
        search.notify_on_new = data.notify_on_new
    if data.notify_frequency is not None:
        search.notify_frequency = data.notify_frequency
    
    db.commit()
    db.refresh(search)
    
    return search

@router.delete("/{search_id}")
async def delete_saved_search(
    search_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a saved search"""
    
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    db.delete(search)
    db.commit()
    
    return {"status": "deleted"}

@router.get("/{search_id}/results")
async def get_saved_search_results(
    search_id: str,
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current results for a saved search"""
    
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    # Would execute the saved search query here
    # For now, return mock data
    
    return {
        "search_id": search_id,
        "results": [],
        "total_count": 0,
        "last_updated": datetime.utcnow()
    }

@router.get("/{search_id}/notifications")
async def get_search_notifications(
    search_id: str,
    skip: int = Query(0),
    limit: int = Query(20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for a saved search"""
    
    search = db.query(SavedSearch).filter(
        SavedSearch.id == search_id,
        SavedSearch.user_id == current_user.id
    ).first()
    
    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found"
        )
    
    notifications = db.query(SearchNotification).filter(
        SearchNotification.saved_search_id == search_id
    ).order_by(
        SearchNotification.notification_date.desc()
    ).offset(skip).limit(limit).all()
    
    return notifications
