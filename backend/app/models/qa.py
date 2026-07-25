"""Q&A (Question and Answer) models for community knowledge."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class QuestionStatus(str, enum.Enum):
    """Question status enumeration."""
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"
    FLAGGED = "flagged"


class AnswerStatus(str, enum.Enum):
    """Answer status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACCEPTED = "accepted"  # Marked as best answer
    FLAGGED = "flagged"


class Question(Base):
    """User questions about institutions, admissions, etc."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Question details
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # Categorization
    category = Column(String(50), nullable=True)  # e.g., "admissions", "courses", "campus"
    tags = Column(JSON, default=list)
    
    # Related institution (optional)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True, index=True)
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    answer_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(QuestionStatus), default=QuestionStatus.OPEN, nullable=False)
    
    # Best answer
    best_answer_id = Column(Integer, ForeignKey("answers.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relations
    user = relationship("User", backref="questions")
    institution = relationship("Institution", backref="questions")
    answers = relationship("Answer", back_populates="question", foreign_keys="Answer.question_id")
    best_answer = relationship("Answer", foreign_keys=[best_answer_id])
    votes = relationship("QuestionVote", back_populates="question")


class Answer(Base):
    """Answers to user questions."""
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Answer content
    content = Column(Text, nullable=False)
    
    # Engagement
    upvote_count = Column(Integer, default=0)
    downvote_count = Column(Integer, default=0)
    
    # Status
    status = Column(Enum(AnswerStatus), default=AnswerStatus.PENDING, nullable=False)
    is_official = Column(Boolean, default=False)  # Answer from institution official
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relations
    question = relationship("Question", back_populates="answers", foreign_keys=[question_id])
    user = relationship("User", backref="answers")
    votes = relationship("AnswerVote", back_populates="answer")


class QuestionVote(Base):
    """Votes on questions (upvote/downvote)."""
    __tablename__ = "question_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_upvote = Column(Boolean, nullable=False)  # True = upvote, False = downvote
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    question = relationship("Question", back_populates="votes")


class AnswerVote(Base):
    """Votes on answers (upvote/downvote)."""
    __tablename__ = "answer_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    answer_id = Column(Integer, ForeignKey("answers.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_upvote = Column(Boolean, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    answer = relationship("Answer", back_populates="votes")
