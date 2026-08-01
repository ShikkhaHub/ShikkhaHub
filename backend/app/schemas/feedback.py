"""
Pydantic schemas for Feedback operations
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    type: str = Field(..., regex="^(bug_report|feature_request|improvement|general|complaint)$")
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10, max_length=5000)
    rating: Optional[str] = Field(None, regex="^(very_poor|poor|neutral|good|excellent)$")
    section: Optional[str] = Field(None, max_length=100)  # e.g., "search", "institution", "review"
    page_url: Optional[str] = Field(None, max_length=500)
    user_agent: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None  # App version, OS, etc.
    is_public: bool = False


class FeedbackResponse(BaseModel):
    """Response schema for feedback"""
    id: str
    type: str
    title: str
    description: str
    rating: Optional[str]
    section: Optional[str]
    status: str
    priority: Optional[int]
    is_public: bool
    comment_count: int
    upvote_count: int
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    """Response schema for feedback list"""
    total: int
    skip: int
    limit: int
    items: List[FeedbackResponse]


class FeedbackCommentCreate(BaseModel):
    """Schema for creating feedback comment"""
    comment: str = Field(..., min_length=1, max_length=2000)
    is_internal: bool = False


class FeedbackCommentResponse(BaseModel):
    """Response schema for feedback comment"""
    id: str
    feedback_id: str
    user_id: str
    comment: str
    is_internal: bool
    like_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeedbackAnalyticsResponse(BaseModel):
    """Response schema for feedback analytics"""
    date: str
    total_feedback: int
    bug_reports: int
    feature_requests: int
    improvements: int
    positive_ratio: int
    negative_ratio: int
    neutral_ratio: int
    avg_rating: Optional[int]
    response_rate: int
    resolution_rate: int
    top_issues: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True
