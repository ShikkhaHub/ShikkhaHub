"""
Pydantic schemas for Saved Search operations
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class SavedSearchCreate(BaseModel):
    """Schema for creating a new saved search"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    query: Optional[str] = Field(None, max_length=255)
    institution_types: Optional[List[str]] = Field(None)
    divisions: Optional[List[str]] = Field(None)
    districts: Optional[List[str]] = Field(None)
    subjects: Optional[List[str]] = Field(None)
    min_rating: Optional[int] = Field(0, ge=0, le=5)
    sort_by: str = Field("relevance", regex="^(relevance|rating|newest)$")
    limit: Optional[int] = Field(20, ge=1, le=100)
    notify_new_matches: bool = False
    notify_institution_updates: bool = False
    notification_frequency: str = Field("weekly", regex="^(daily|weekly|never)$")


class SavedSearchUpdate(BaseModel):
    """Schema for updating a saved search"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    query: Optional[str] = Field(None, max_length=255)
    institution_types: Optional[List[str]] = None
    divisions: Optional[List[str]] = None
    districts: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    min_rating: Optional[int] = Field(None, ge=0, le=5)
    sort_by: Optional[str] = Field(None, regex="^(relevance|rating|newest)$")
    limit: Optional[int] = Field(None, ge=1, le=100)
    notify_new_matches: Optional[bool] = None
    notify_institution_updates: Optional[bool] = None
    notification_frequency: Optional[str] = Field(None, regex="^(daily|weekly|never)$")


class SavedSearchResponse(BaseModel):
    """Response schema for a saved search"""
    id: str
    name: str
    description: Optional[str]
    query: Optional[str]
    institution_types: Optional[List[str]]
    divisions: Optional[List[str]]
    districts: Optional[List[str]]
    subjects: Optional[List[str]]
    min_rating: Optional[int]
    sort_by: str
    limit: Optional[int]
    notify_new_matches: bool
    notify_institution_updates: bool
    notification_frequency: str
    result_count: int
    last_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SavedSearchListResponse(BaseModel):
    """Response schema for list of saved searches"""
    total: int
    skip: int
    limit: int
    items: List[SavedSearchResponse]


class SavedSearchHitResponse(BaseModel):
    """Response schema for a saved search hit"""
    id: str
    saved_search_id: str
    institution_id: str
    discovered_at: datetime
    user_notified: bool
    user_notified_at: Optional[datetime]

    class Config:
        from_attributes = True
