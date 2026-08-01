"""
Notification Model
Stores and manages user notifications for various events
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, JSON, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class NotificationType(str, enum.Enum):
    """Types of notifications"""
    SAVED_SEARCH_MATCH = "saved_search_match"
    INSTITUTION_UPDATE = "institution_update"
    REVIEW_REPLY = "review_reply"
    QA_ANSWER = "qa_answer"
    NEW_FEATURE = "new_feature"
    SYSTEM = "system"
    PROMOTIONAL = "promotional"


class NotificationChannel(str, enum.Enum):
    """Channels for sending notifications"""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class Notification(Base):
    """
    Model for storing user notifications
    Handles all types of notifications sent to users
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    title = Column(String(255), nullable=False)
    message = Column(String(1000), nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.SYSTEM)
    
    # Link data (what should open when user clicks)
    action_url = Column(String(500), nullable=True)  # Deep link to app section
    related_institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=True)
    related_saved_search_id = Column(String(36), ForeignKey("saved_searches.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    
    # Channel preferences
    sent_via = Column(JSON, nullable=True)  # ["in_app", "email", "push"]
    send_email = Column(Boolean, default=False)  # Whether email was sent
    send_push = Column(Boolean, default=False)  # Whether push was sent
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index("idx_user_id_created", "user_id", "created_at"),
        Index("idx_user_id_is_read", "user_id", "is_read"),
        Index("idx_user_id_type", "user_id", "type"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "action_url": self.action_url,
            "related_institution_id": self.related_institution_id,
            "related_saved_search_id": self.related_saved_search_id,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "is_archived": self.is_archived,
            "sent_via": self.sent_via,
            "created_at": self.created_at.isoformat(),
        }

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()

    def mark_as_unread(self):
        """Mark notification as unread"""
        self.is_read = False
        self.read_at = None

    def archive(self):
        """Archive notification"""
        self.is_archived = True

    def unarchive(self):
        """Unarchive notification"""
        self.is_archived = False


class NotificationPreference(Base):
    """
    Model for storing user notification preferences
    Controls which types of notifications a user wants to receive
    """
    __tablename__ = "notification_preferences"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Notification type preferences
    saved_search_matches = Column(Boolean, default=True)
    institution_updates = Column(Boolean, default=True)
    review_replies = Column(Boolean, default=True)
    qa_answers = Column(Boolean, default=True)
    new_features = Column(Boolean, default=True)
    promotional = Column(Boolean, default=False)
    
    # Channel preferences
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    
    # Frequency preferences
    email_frequency = Column(String(50), default="weekly")  # daily, weekly, never
    
    # Quiet hours
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_timezone = Column(String(50), default="UTC")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "saved_search_matches": self.saved_search_matches,
            "institution_updates": self.institution_updates,
            "review_replies": self.review_replies,
            "qa_answers": self.qa_answers,
            "new_features": self.new_features,
            "promotional": self.promotional,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "in_app_notifications": self.in_app_notifications,
            "email_frequency": self.email_frequency,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "quiet_hours_timezone": self.quiet_hours_timezone,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class NotificationLog(Base):
    """
    Model for logging notification sending events
    Used for debugging and analytics
    """
    __tablename__ = "notification_logs"

    id = Column(String(36), primary_key=True, index=True)
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Delivery info
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(String(50), nullable=False)  # sent, failed, pending
    error_message = Column(String(1000), nullable=True)
    external_id = Column(String(255), nullable=True)  # Email ID, Push ID from provider
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_notification_id_channel", "notification_id", "channel"),
        Index("idx_user_id_status", "user_id", "status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "channel": self.channel.value,
            "status": self.status,
            "error_message": self.error_message,
            "external_id": self.external_id,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }
