"""Chat/Conversation models for AI assistant."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    """Chat session/conversation thread."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=True)  # Auto-generated or user-set title
    
    # Context information
    context_type = Column(String(50), nullable=True)  # e.g., 'admission_help', 'career_guidance'
    session_metadata = Column(JSON, default=dict)  # Additional context data (renamed to avoid SQLAlchemy reserved word)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relations
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Individual chat message."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    
    # AI-specific fields
    context_used = Column(Integer, default=0)  # Number of documents used for RAG
    sources = Column(JSON, default=list)  # Source institutions cited
    confidence_score = Column(String(20), nullable=True)  # AI confidence in response
    
    # User feedback
    is_helpful = Column(Boolean, nullable=True)  # User feedback: thumbs up/down
    feedback_text = Column(Text, nullable=True)  # Optional text feedback
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    session = relationship("ChatSession", back_populates="messages")
