"""
Notifications API
Manages push notifications, email alerts, and user preferences
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Models
class NotificationPreferences(BaseModel):
    """User notification preferences"""
    email_alerts: bool = True
    push_notifications: bool = True
    sms_alerts: bool = False
    frequency: str = "daily"  # immediate, daily, weekly, monthly
    categories: dict = {
        "saved_searches": True,
        "new_reviews": True,
        "rating_changes": True,
        "news_updates": True,
        "ambassador_rewards": True,
        "events": True
    }

class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    user_id: str
    type: str  # search_alert, review_alert, event_alert, reward_alert
    title: str
    message: str
    data: dict = {}
    read: bool = False
    created_at: datetime
    action_url: str | None = None

    class Config:
        from_attributes = True

# Routes

@router.get("/preferences", response_model=NotificationPreferences)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notification preferences"""
    
    prefs = db.query(UserNotificationPreferences).filter(
        UserNotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Return defaults if not set
        return NotificationPreferences()
    
    return prefs

@router.patch("/preferences", response_model=NotificationPreferences)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user notification preferences"""
    
    prefs = db.query(UserNotificationPreferences).filter(
        UserNotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = UserNotificationPreferences(user_id=current_user.id)
        db.add(prefs)
    
    prefs.email_alerts = preferences.email_alerts
    prefs.push_notifications = preferences.push_notifications
    prefs.sms_alerts = preferences.sms_alerts
    prefs.frequency = preferences.frequency
    prefs.categories = preferences.categories
    
    db.commit()
    db.refresh(prefs)
    
    return prefs

@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    skip: int = Query(0),
    limit: int = Query(20),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user notifications"""
    
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )
    
    if unread_only:
        query = query.filter(Notification.read == False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return notifications

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread notifications"""
    
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).count()
    
    return {"unread_count": count}

@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    notification.read = True
    db.commit()
    
    return {"status": "marked_read"}

@router.patch("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read == False
    ).update({"read": True})
    
    db.commit()
    
    return {"status": "all_marked_read"}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    db.delete(notification)
    db.commit()
    
    return {"status": "deleted"}

@router.post("/test")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test notification to current user"""
    
    notification = Notification(
        user_id=current_user.id,
        type="test",
        title="Test Notification",
        message="This is a test notification from ShikkhaHub",
        read=False,
        created_at=datetime.utcnow()
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return {
        "status": "sent",
        "notification_id": notification.id
    }

# Batch notification endpoints (for admin/scheduled tasks)

@router.post("/batch/search-alerts")
async def send_search_alerts_batch(
    db: Session = Depends(get_db)
):
    """Send saved search alerts to users (typically scheduled)"""
    
    # This would be called by a background job
    # Gets all saved searches with notifications enabled
    # Executes queries and sends notifications to users
    
    return {
        "status": "batch_job_started",
        "job_type": "search_alerts"
    }

@router.post("/batch/review-alerts")
async def send_review_alerts_batch(
    db: Session = Depends(get_db)
):
    """Send alerts for new reviews on saved institutions"""
    
    return {
        "status": "batch_job_started",
        "job_type": "review_alerts"
    }

@router.post("/batch/news-digest")
async def send_news_digest(
    db: Session = Depends(get_db)
):
    """Send daily/weekly news digest"""
    
    return {
        "status": "batch_job_started",
        "job_type": "news_digest"
    }

@router.post("/batch/ambassador-rewards")
async def send_ambassador_notifications(
    db: Session = Depends(get_db)
):
    """Send notifications to ambassadors about rewards and leaderboard"""
    
    return {
        "status": "batch_job_started",
        "job_type": "ambassador_rewards"
    }

# Notification templates

@router.get("/templates")
async def get_notification_templates():
    """Get available notification templates"""
    
    return {
        "templates": [
            {
                "id": "search_alert",
                "name": "Saved Search Alert",
                "description": "New institutions matching your saved search",
                "variables": ["search_name", "institution_count", "top_institution"]
            },
            {
                "id": "review_alert",
                "name": "New Review Alert",
                "description": "New review posted on a saved institution",
                "variables": ["institution_name", "reviewer_name", "rating"]
            },
            {
                "id": "rating_alert",
                "name": "Rating Change Alert",
                "description": "Rating changed on a saved institution",
                "variables": ["institution_name", "old_rating", "new_rating"]
            },
            {
                "id": "ambassador_reward",
                "name": "Ambassador Reward",
                "description": "You earned rewards from referrals",
                "variables": ["reward_amount", "referral_count", "tier"]
            },
            {
                "id": "event_alert",
                "name": "Event Notification",
                "description": "New event at your saved institution",
                "variables": ["institution_name", "event_name", "event_date"]
            }
        ]
    }

@router.get("/notification-history")
async def get_notification_history(
    notification_type: str | None = Query(None),
    days: int = Query(30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification history for analytics"""
    
    from datetime import timedelta
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.created_at >= start_date
    )
    
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).all()
    
    return {
        "total": len(notifications),
        "by_type": {},  # Would aggregate by type
        "notifications": notifications
    }
