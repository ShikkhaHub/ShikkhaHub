"""
Pydantic schemas for Notification operations
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class NotificationResponse(BaseModel):
    """Response schema for a notification"""
    id: str
    title: str
    message: str
    type: str
    action_url: Optional[str]
    related_institution_id: Optional[str]
    related_saved_search_id: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    is_archived: bool
    sent_via: Optional[List[str]]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Response schema for list of notifications"""
    total: int
    skip: int
    limit: int
    unread_count: int
    items: List[NotificationResponse]


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences"""
    id: str
    saved_search_matches: bool
    institution_updates: bool
    review_replies: bool
    qa_answers: bool
    new_features: bool
    promotional: bool
    email_notifications: bool
    push_notifications: bool
    in_app_notifications: bool
    email_frequency: str
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    quiet_hours_timezone: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating notification preferences"""
    saved_search_matches: Optional[bool] = None
    institution_updates: Optional[bool] = None
    review_replies: Optional[bool] = None
    qa_answers: Optional[bool] = None
    new_features: Optional[bool] = None
    promotional: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None
    email_frequency: Optional[str] = Field(None, regex="^(daily|weekly|never)$")
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = Field(None, regex="^\\d{2}:\\d{2}$")
    quiet_hours_end: Optional[str] = Field(None, regex="^\\d{2}:\\d{2}$")
    quiet_hours_timezone: Optional[str] = None


class NotificationLogResponse(BaseModel):
    """Response schema for notification log"""
    id: str
    notification_id: str
    user_id: str
    channel: str
    status: str
    error_message: Optional[str]
    external_id: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    class Config:
        from_attributes = True
