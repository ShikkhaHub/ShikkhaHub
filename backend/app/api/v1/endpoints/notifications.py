"""
Notifications API Endpoints
Handles notification retrieval, preferences, and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.notification import (
    Notification,
    NotificationPreference,
    NotificationType,
    NotificationLog,
)
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    is_read: bool = Query(None),
    notification_type: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    List notifications for the current user
    
    Args:
        current_user: Current authenticated user
        skip: Number of results to skip
        limit: Number of results to return
        is_read: Filter by read status
        notification_type: Filter by notification type
        db: Database session
        
    Returns:
        List of notifications
    """
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_archived == False,
    )
    
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    total = query.count()
    
    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return NotificationListResponse(
        total=total,
        skip=skip,
        limit=limit,
        unread_count=db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
            Notification.is_archived == False,
        ).count(),
        items=notifications,
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific notification
    
    Args:
        notification_id: ID of notification
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Notification object
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as read
    
    Args:
        notification_id: ID of notification
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated notification object
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.mark_as_read()
    db.commit()
    db.refresh(notification)
    
    return notification


@router.patch("/{notification_id}/unread")
async def mark_notification_unread(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark a notification as unread
    
    Args:
        notification_id: ID of notification
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated notification object
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.mark_as_unread()
    db.commit()
    db.refresh(notification)
    
    return notification


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all notifications as read for the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    unread_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    
    db.commit()
    
    return {"message": f"{unread_count} notifications marked as read"}


@router.patch("/{notification_id}/archive")
async def archive_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Archive a notification
    
    Args:
        notification_id: ID of notification
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated notification object
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.archive()
    db.commit()
    db.refresh(notification)
    
    return notification


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a notification
    
    Args:
        notification_id: ID of notification
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted successfully"}


@router.get("/preferences/current", response_model=NotificationPreferenceResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get notification preferences for the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User notification preferences
    """
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        # Create default preferences if they don't exist
        from uuid import uuid4
        preferences = NotificationPreference(
            id=str(uuid4()),
            user_id=current_user.id,
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences


@router.patch("/preferences/update", response_model=NotificationPreferenceResponse)
async def update_notification_preferences(
    update_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update notification preferences for the current user
    
    Args:
        update_data: Updated preferences
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated notification preferences
    """
    preferences = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).first()
    
    if not preferences:
        from uuid import uuid4
        preferences = NotificationPreference(
            id=str(uuid4()),
            user_id=current_user.id,
        )
        db.add(preferences)
        db.commit()
    
    # Update provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(preferences, key, value)
    
    preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(preferences)
    
    return preferences


@router.get("/summary/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get count of unread notifications
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Unread count by type
    """
    unread_by_type = {}
    
    for notif_type in NotificationType:
        count = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.type == notif_type,
            Notification.is_read == False,
            Notification.is_archived == False,
        ).count()
        if count > 0:
            unread_by_type[notif_type.value] = count
    
    total_unread = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
        Notification.is_archived == False,
    ).count()
    
    return {
        "total_unread": total_unread,
        "by_type": unread_by_type,
    }


@router.post("/send-test")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a test notification to current user (for testing preferences)
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Notification object
    """
    from uuid import uuid4
    from app.core.notifications import NotificationService
    
    # Create test notification
    notification = Notification(
        id=str(uuid4()),
        user_id=current_user.id,
        title="Test Notification",
        message="This is a test notification from ShikkhaHub",
        type=NotificationType.SYSTEM,
        sent_via=["in_app"],
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    # Send via notification service
    notification_service = NotificationService(db)
    await notification_service.send_test_notification(current_user)
    
    return notification
