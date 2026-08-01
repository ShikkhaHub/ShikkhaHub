"""
Saved Search Model
Stores user's saved search filters for quick re-access
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class SavedSearch(Base):
    """
    Model for storing user's saved search filters
    Allows users to save search criteria and quickly re-run them
    """
    __tablename__ = "saved_searches"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Search filters (stored as JSON for flexibility)
    query = Column(String(255), nullable=True)  # Search query text
    institution_types = Column(JSON, nullable=True)  # e.g., ["University", "College"]
    divisions = Column(JSON, nullable=True)  # Selected divisions
    districts = Column(JSON, nullable=True)  # Selected districts
    subjects = Column(JSON, nullable=True)  # Selected subjects/programs
    
    # Advanced filters
    min_rating = Column(Integer, nullable=True, default=0)  # Minimum rating (0-5)
    sort_by = Column(String(50), nullable=True, default="relevance")  # relevance, rating, newest
    limit = Column(Integer, nullable=True, default=20)  # Results limit
    
    # Metadata
    name = Column(String(255), nullable=False)  # User-given name for search
    description = Column(String(1000), nullable=True)  # Search description
    
    # Notification settings
    notify_new_matches = Column(Boolean, default=False)  # Notify on new matching institutions
    notify_institution_updates = Column(Boolean, default=False)  # Notify when saved institutions update
    notification_frequency = Column(String(50), default="weekly")  # daily, weekly, never
    
    # Stats and usage
    result_count = Column(Integer, default=0)  # Number of results last time run
    last_run_at = Column(DateTime, nullable=True)  # Last time this search was executed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="saved_searches")
    saved_search_hits = relationship("SavedSearchHit", back_populates="saved_search", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_user_id_created", "user_id", "created_at"),
        Index("idx_user_id_last_run", "user_id", "last_run_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "query": self.query,
            "institution_types": self.institution_types,
            "divisions": self.divisions,
            "districts": self.districts,
            "subjects": self.subjects,
            "min_rating": self.min_rating,
            "sort_by": self.sort_by,
            "limit": self.limit,
            "notify_new_matches": self.notify_new_matches,
            "notify_institution_updates": self.notify_institution_updates,
            "notification_frequency": self.notification_frequency,
            "result_count": self.result_count,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SavedSearchHit(Base):
    """
    Model for storing institutions that match a saved search
    Used to track new results and notify users
    """
    __tablename__ = "saved_search_hits"

    id = Column(String(36), primary_key=True, index=True)
    saved_search_id = Column(String(36), ForeignKey("saved_searches.id"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    
    # Track when this institution was added as a hit
    discovered_at = Column(DateTime, default=datetime.utcnow)
    user_notified_at = Column(DateTime, nullable=True)  # When notification was sent
    user_notified = Column(Boolean, default=False)  # Whether user was notified
    
    # Relationships
    saved_search = relationship("SavedSearch", back_populates="saved_search_hits")
    
    __table_args__ = (
        Index("idx_search_id_institution", "saved_search_id", "institution_id"),
        Index("idx_search_id_notified", "saved_search_id", "user_notified"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "saved_search_id": self.saved_search_id,
            "institution_id": self.institution_id,
            "discovered_at": self.discovered_at.isoformat(),
            "user_notified": self.user_notified,
            "user_notified_at": self.user_notified_at.isoformat() if self.user_notified_at else None,
        }
