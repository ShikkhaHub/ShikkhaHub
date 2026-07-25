"""Review and rating models for institutions."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class ReviewStatus(str, enum.Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class InstitutionReview(Base):
    """User reviews for institutions."""
    __tablename__ = "institution_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Rating (1-5 stars)
    overall_rating = Column(Float, nullable=False)  # 1.0 to 5.0
    
    # Detailed ratings
    academics_rating = Column(Float, nullable=True)
    facilities_rating = Column(Float, nullable=True)
    faculty_rating = Column(Float, nullable=True)
    campus_life_rating = Column(Float, nullable=True)
    value_for_money_rating = Column(Float, nullable=True)
    
    # Review content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    pros = Column(JSON, default=list)  # List of positive points
    cons = Column(JSON, default=list)  # List of negative points
    
    # Metadata
    study_program = Column(String(255), nullable=True)  # e.g., "Computer Science"
    graduation_year = Column(Integer, nullable=True)
    is_alumni = Column(Boolean, default=False)
    
    # Status and moderation
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, nullable=False)
    helpful_count = Column(Integer, default=0)
    unhelpful_count = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)  # Verified purchase/attendance
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relations
    institution = relationship("Institution", back_populates="reviews")
    user = relationship("User", backref="institution_reviews")
    helpful_votes = relationship("ReviewHelpfulVote", back_populates="review")
    reports = relationship("ReviewReport", back_populates="review")


class ReviewHelpfulVote(Base):
    """Track helpful/unhelpful votes on reviews."""
    __tablename__ = "review_helpful_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("institution_reviews.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_helpful = Column(Boolean, nullable=False)  # True = helpful, False = unhelpful
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    review = relationship("InstitutionReview", back_populates="helpful_votes")
    
    # Unique constraint
    __table_args__ = (
        # User can only vote once per review
        {'sqlite_autoincrement': True},
    )


class ReviewReport(Base):
    """User reports for inappropriate reviews."""
    __tablename__ = "review_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("institution_reviews.id"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Report details
    reason = Column(String(50), nullable=False)  # e.g., "spam", "inappropriate", "fake"
    description = Column(Text, nullable=True)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution = Column(String(50), nullable=True)  # e.g., "dismissed", "removed"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    review = relationship("InstitutionReview", back_populates="reports")
