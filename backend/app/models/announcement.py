"""Announcement entities: admissions, notices and scholarships.

These tables power time-bound, student-facing information in the
national education knowledge graph.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    Float,
    Index,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Admission(Base):
    """An admission circular/cycle for an institution or course offering."""

    __tablename__ = "admissions"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    institution_course_id = Column(
        Integer, ForeignKey("institution_courses.id"), nullable=True
    )
    title = Column(String(300), nullable=False)
    session = Column(String(20), nullable=True)  # 2025-26, 2026, ...
    program = Column(String(200), nullable=True)
    application_start = Column(DateTime, nullable=True)
    application_end = Column(DateTime, nullable=True)
    exam_date = Column(DateTime, nullable=True)
    minimum_gpa = Column(Float, nullable=True)
    minimum_gpa_scale = Column(Float, default=5.0)
    total_seats = Column(Integer, nullable=True)
    application_fee = Column(Float, nullable=True)
    eligibility = Column(Text, nullable=True)
    required_documents = Column(Text, nullable=True)  # JSON list
    application_link = Column(String(500), nullable=True)
    status = Column(String(20), default="open")  # upcoming, open, closed, announced
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution", back_populates="admissions")
    institution_course = relationship("InstitutionCourse", back_populates="admissions")

    __table_args__ = (
        Index("idx_admission_institution", "institution_id"),
        Index("idx_admission_status", "status"),
        Index("idx_admission_session", "session"),
    )

    def __repr__(self) -> str:
        return f"<Admission {self.title}>"


class Notice(Base):
    """Notices and announcements published by an institution."""

    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    title = Column(String(300), nullable=False)
    body = Column(Text, nullable=True)
    category = Column(
        String(50), default="general"
    )  # general, admission, examination, result, holiday
    publish_at = Column(DateTime, nullable=True)
    expire_at = Column(DateTime, nullable=True)
    is_important = Column(Boolean, default=False)
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="notices")

    __table_args__ = (
        Index("idx_notice_institution", "institution_id"),
        Index("idx_notice_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<Notice {self.title}>"


class Scholarship(Base):
    """Scholarships and financial aid offered at an institution."""

    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    name = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String(10), default="BDT")
    scholarship_type = Column(
        String(50), default="merit"
    )  # merit, need, sports, research, special
    eligibility = Column(Text, nullable=True)
    application_deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="scholarships")

    __table_args__ = (
        Index("idx_scholarship_institution", "institution_id"),
        Index("idx_scholarship_type", "scholarship_type"),
    )

    def __repr__(self) -> str:
        return f"<Scholarship {self.name}>"
