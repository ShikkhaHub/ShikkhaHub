"""
User Feedback Model
Captures user feedback, bug reports, and feature requests
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Index, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class FeedbackType(str, enum.Enum):
    """Types of feedback"""
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    IMPROVEMENT = "improvement"
    GENERAL = "general"
    COMPLAINT = "complaint"


class FeedbackStatus(str, enum.Enum):
    """Status of feedback"""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"
    CLOSED = "closed"


class FeedbackRating(str, enum.Enum):
    """Rating from user"""
    VERY_POOR = "very_poor"
    POOR = "poor"
    NEUTRAL = "neutral"
    GOOD = "good"
    EXCELLENT = "excellent"


class Feedback(Base):
    """
    Model for storing user feedback
    Captures user suggestions, bug reports, and complaints
    """
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # Nullable for anonymous feedback
    
    # Feedback content
    type = Column(SQLEnum(FeedbackType), nullable=False, default=FeedbackType.GENERAL)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rating = Column(SQLEnum(FeedbackRating), nullable=True)  # User's satisfaction rating
    
    # Context
    section = Column(String(100), nullable=True)  # Which part of app (search, institution, review, etc.)
    page_url = Column(String(500), nullable=True)  # Page where feedback was submitted
    user_agent = Column(String(500), nullable=True)  # Browser/app user agent
    
    # Attachments and metadata
    attachments = Column(JSON, nullable=True)  # URLs to uploaded screenshots/files
    metadata = Column(JSON, nullable=True)  # Additional context (e.g., app version, OS)
    
    # Status and tracking
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.NEW)
    priority = Column(Integer, nullable=True, default=3)  # 1-5, 1 being highest priority
    tags = Column(JSON, nullable=True)  # Internal tags for categorization
    
    # Internal notes
    internal_notes = Column(Text, nullable=True)
    assigned_to = Column(String(100), nullable=True)  # Team member assigned
    
    # Engagement
    is_public = Column(Boolean, default=False)  # Make visible to community
    comment_count = Column(Integer, default=0)
    upvote_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="feedback_items")
    comments = relationship("FeedbackComment", back_populates="feedback", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_user_id_created", "user_id", "created_at"),
        Index("idx_type_status", "type", "status"),
        Index("idx_priority_status", "priority", "status"),
    )

    def to_dict(self, include_comments=False):
        data = {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "description": self.description,
            "rating": self.rating.value if self.rating else None,
            "section": self.section,
            "status": self.status.value,
            "priority": self.priority,
            "is_public": self.is_public,
            "comment_count": self.comment_count,
            "upvote_count": self.upvote_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
        
        if include_comments:
            data["comments"] = [comment.to_dict() for comment in self.comments]
        
        return data


class FeedbackComment(Base):
    """
    Model for comments on feedback items
    Enables discussion between users and team
    """
    __tablename__ = "feedback_comments"

    id = Column(String(36), primary_key=True, index=True)
    feedback_id = Column(String(36), ForeignKey("feedback.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Comment content
    comment = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Only visible to team if True
    
    # Reactions
    like_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    feedback = relationship("Feedback", back_populates="comments")
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_feedback_id_created", "feedback_id", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_id": self.feedback_id,
            "user_id": self.user_id,
            "comment": self.comment,
            "is_internal": self.is_internal,
            "like_count": self.like_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class FeedbackVote(Base):
    """
    Model for tracking upvotes on feedback items
    Helps prioritize based on community voting
    """
    __tablename__ = "feedback_votes"

    id = Column(String(36), primary_key=True, index=True)
    feedback_id = Column(String(36), ForeignKey("feedback.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Vote value
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_feedback_user", "feedback_id", "user_id"),
    )


class FeedbackTemplate(Base):
    """
    Model for feedback templates/forms
    Predefined questions for different feedback types
    """
    __tablename__ = "feedback_templates"

    id = Column(String(36), primary_key=True, index=True)
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False, unique=True)
    
    # Template questions
    questions = Column(JSON, nullable=False)  # List of question objects
    enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "feedback_type": self.feedback_type.value,
            "questions": self.questions,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
        }


class FeedbackAnalytic(Base):
    """
    Model for storing aggregated feedback analytics
    Used for trends and insights
    """
    __tablename__ = "feedback_analytics"

    id = Column(String(36), primary_key=True, index=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD format
    
    # Daily metrics
    total_feedback = Column(Integer, default=0)
    bug_reports = Column(Integer, default=0)
    feature_requests = Column(Integer, default=0)
    improvements = Column(Integer, default=0)
    
    # Sentiment
    positive_ratio = Column(Integer, default=0)  # Percentage 0-100
    negative_ratio = Column(Integer, default=0)  # Percentage 0-100
    neutral_ratio = Column(Integer, default=0)  # Percentage 0-100
    
    # Engagement
    avg_rating = Column(Integer, nullable=True)  # 1-5 scale * 100 for precision
    response_rate = Column(Integer, default=0)  # Percentage 0-100
    resolution_rate = Column(Integer, default=0)  # Percentage 0-100
    
    # Topics
    top_issues = Column(JSON, nullable=True)  # List of top mentioned topics
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "total_feedback": self.total_feedback,
            "bug_reports": self.bug_reports,
            "feature_requests": self.feature_requests,
            "improvements": self.improvements,
            "positive_ratio": self.positive_ratio,
            "negative_ratio": self.negative_ratio,
            "neutral_ratio": self.neutral_ratio,
            "avg_rating": self.avg_rating,
            "response_rate": self.response_rate,
            "resolution_rate": self.resolution_rate,
            "top_issues": self.top_issues,
            "created_at": self.created_at.isoformat(),
        }
