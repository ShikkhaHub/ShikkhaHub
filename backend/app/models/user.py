"""User model for authentication and authorization."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    MODERATOR = "moderator"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Role and permissions
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Preferences
    preferred_language = Column(String(10), default="en")
    notification_enabled = Column(Boolean, default=True)

    # Analytics relationships
    search_events = relationship("SearchEvent", back_populates="user")
    page_views = relationship("PageView", back_populates="user")
    click_events = relationship("ClickEvent", back_populates="user")

    # Student analytics relationships
    student_profile = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    analytics_events = relationship("AnalyticsEvent", back_populates="user")
    study_sessions = relationship("StudySession", back_populates="user")
    consent_records = relationship("ConsentRecord", back_populates="user")

    # Saved institutions (knowledge-graph bookmarks)
    saved_institutions = relationship(
        "SavedInstitution", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username or self.email

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def is_admin(self) -> bool:
        """Check if user is admin or super admin."""
        return self.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]

    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == UserRole.SUPER_ADMIN
