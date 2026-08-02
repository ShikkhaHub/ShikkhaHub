"""Student analytics models for the ShikkhaHub data analytics platform.

Implements the Student Data Analytics Plan:
- StudentProfile: 360-degree student data (academic, geographic, career, learning)
- AnalyticsEvent: generic event tracking for every important platform action
- StudySession: learning analytics (time, lessons, quiz accuracy)
- ConsentRecord: privacy governance / explicit consent audit trail
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Date,
    Float,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.core.database import Base


class StudentProfile(Base):
    """Comprehensive student profile - the "Student 360" record.

    Maps to the Student Data Model in the analytics plan:
    basic, academic, geographic, career and learning profile data.
    """

    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True
    )

    # ---------- Basic Profile ----------
    full_name = Column(String(200), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, other
    date_of_birth = Column(Date, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)

    # ---------- Academic Profile ----------
    current_level = Column(String(50), nullable=True, index=True)
    # SSC, HSC, Diploma, University, Masters
    education_board = Column(String(100), nullable=True)
    current_institution = Column(String(300), nullable=True)
    department = Column(String(200), nullable=True)
    session = Column(String(50), nullable=True)
    expected_graduation = Column(String(20), nullable=True)  # Year
    gpa_history = Column(
        Text, nullable=True
    )  # JSON list e.g. [{"level":"SSC","gpa":5.0}]
    academic_interests = Column(Text, nullable=True)  # JSON list

    # ---------- Geographic Information ----------
    division = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    upazila = Column(String(100), nullable=True)
    area = Column(String(200), nullable=True)
    current_location = Column(String(300), nullable=True)

    # ---------- Career Information ----------
    dream_career = Column(String(200), nullable=True)
    interested_sectors = Column(Text, nullable=True)  # JSON list
    preferred_university = Column(String(300), nullable=True)
    preferred_subject = Column(String(200), nullable=True)
    expected_salary = Column(Integer, nullable=True)  # Monthly BDT
    abroad_interest = Column(Boolean, default=False)
    scholarship_interest = Column(Boolean, default=False)
    annual_income = Column(
        Integer, nullable=True
    )  # Family income (BDT) for scholarship matching
    disability = Column(String(100), nullable=True)  # For scholarship eligibility

    # ---------- Learning Profile ----------
    favorite_subjects = Column(Text, nullable=True)  # JSON list
    weak_subjects = Column(Text, nullable=True)  # JSON list
    completed_courses = Column(Text, nullable=True)  # JSON list
    study_hours_per_week = Column(Integer, nullable=True)
    # Visual, Auditory, Reading/Writing, Kinesthetic
    learning_style = Column(String(50), nullable=True)
    language_preference = Column(String(10), default="en")
    exam_preparation = Column(Text, nullable=True)  # JSON object
    weekly_study_target_minutes = Column(Integer, nullable=True)

    # ---------- AI Student Profile (cached) ----------
    student_type = Column(String(50), nullable=True)  # Admission Focused, etc.
    strong_subjects = Column(Text, nullable=True)  # JSON list
    interested_universities = Column(Text, nullable=True)  # JSON list
    risk_score = Column(String(20), nullable=True)  # Low, Medium, High
    recommendation_score = Column(Float, nullable=True)  # 0-100
    ai_profile = Column(Text, nullable=True)  # JSON blob of full AI profile
    ai_profile_generated_at = Column(DateTime, nullable=True)

    # ---------- Consent ----------
    analytics_consent = Column(Boolean, default=False, nullable=False)
    analytics_consent_at = Column(DateTime, nullable=True)

    # ---------- Timestamps ----------
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")

    __table_args__ = (
        Index("idx_student_level", "current_level"),
        Index("idx_student_division", "division"),
        Index("idx_student_consent", "analytics_consent"),
    )

    def __repr__(self):
        return f"<StudentProfile user_id={self.user_id}>"


class AnalyticsEvent(Base):
    """Generic analytics event - every important platform action.

    Event types (from the plan):
    search_query, institution_view, admission_interest, admission_page_view,
    save_institution, course_view, video_watch, pdf_read, ai_chat,
    career_assistant_usage, bookmark, download, share, comment, review,
    scholarship_view, apply_click
    """

    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=True, index=True
    )
    course_id = Column(Integer, nullable=True)
    subject = Column(String(200), nullable=True, index=True)

    # Context
    page_path = Column(String(500), nullable=True)
    source = Column(String(100), nullable=True)

    # Additional event-specific data (JSON)
    event_data = Column(Text, nullable=True)

    # Engagement
    duration_seconds = Column(Integer, nullable=True)

    # Privacy: anonymous events are not tied to a student identity in reports
    is_anonymous = Column(Boolean, default=False)

    # Source metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="analytics_events")
    institution = relationship("Institution")

    __table_args__ = (
        Index("idx_event_type_time", "event_type", "created_at"),
        Index("idx_event_user_time", "user_id", "created_at"),
        Index("idx_event_institution", "institution_id", "created_at"),
        Index("idx_event_session", "session_id", "created_at"),
        Index("idx_event_subject", "subject", "created_at"),
    )

    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type} user={self.user_id}>"


class StudySession(Base):
    """A learning session used for learning analytics.

    Enables: daily/weekly/monthly learning time, completed lessons,
    quiz accuracy, average score, learning streak, improvement rate,
    and subject performance.
    """

    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subject = Column(String(200), nullable=True, index=True)
    course_id = Column(Integer, nullable=True)

    session_date = Column(Date, default=date.today, index=True)
    duration_minutes = Column(Integer, default=0)
    lessons_completed = Column(Integer, default=0)
    quiz_accuracy = Column(Float, nullable=True)  # 0-100
    average_score = Column(Float, nullable=True)  # 0-100
    content_type = Column(String(50), nullable=True)  # video, pdf, quiz, practice

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="study_sessions")

    __table_args__ = (
        Index("idx_study_user_date", "user_id", "session_date"),
        Index("idx_study_subject", "subject"),
    )

    def __repr__(self):
        return f"<StudySession user={self.user_id} {self.duration_minutes}min>"


class ConsentRecord(Base):
    """Audit trail of analytics/data consent decisions (privacy governance)."""

    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(
        String(100), nullable=False
    )  # analytics, marketing, data_sharing
    granted = Column(Boolean, nullable=False)
    consent_version = Column(String(20), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="consent_records")

    __table_args__ = (Index("idx_consent_user_type", "user_id", "consent_type"),)

    def __repr__(self):
        return f"<ConsentRecord user={self.user_id} {self.consent_type}={self.granted}>"
