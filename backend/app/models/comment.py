"""Comment system models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class CommentStatus(str, enum.Enum):
    """Comment status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class Comment(Base):
    """Comments on institutions, reviews, or discussions."""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Polymorphic association - comment can be on different content types
    content_type = Column(String(50), nullable=False)  # 'institution', 'review', 'answer', etc.
    content_id = Column(Integer, nullable=False, index=True)
    
    # Comment content
    content = Column(Text, nullable=False)
    
    # Threading (replies)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True, index=True)
    reply_count = Column(Integer, default=0)
    
    # Engagement
    like_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(CommentStatus), default=CommentStatus.APPROVED, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relations
    user = relationship("User", backref="comments")
    parent = relationship("Comment", remote_side=[id], backref="replies")
    likes = relationship("CommentLike", back_populates="comment")


class CommentLike(Base):
    """Likes on comments."""
    __tablename__ = "comment_likes"
    
    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    comment = relationship("Comment", back_populates="likes")
