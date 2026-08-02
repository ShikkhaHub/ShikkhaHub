"""Knowledge-graph association entities.

`InstitutionCourse` is the normalized many-to-many join between the
national course catalog and institutions, carrying offering metadata
(seats, shift, fee, language, status). `SavedInstitution` models a
user bookmarking an institution.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Float,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class InstitutionCourse(Base):
    """A course as offered by a specific institution (many-to-many join)."""

    __tablename__ = "institution_courses"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    # Offering metadata
    total_seats = Column(Integer, nullable=True)
    reserved_seats = Column(Integer, nullable=True)
    shift = Column(String(50), default="morning")  # morning, day, evening
    fee = Column(Float, nullable=True)
    fee_currency = Column(String(10), default="BDT")
    language = Column(String(50), default="bangla")  # bangla, english, bilingual
    intake_year = Column(Integer, nullable=True)
    duration_years = Column(Float, nullable=True)
    status = Column(String(20), default="open")  # open, closed, upcoming
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution", back_populates="course_offerings")
    course = relationship("Course", back_populates="institution_offerings")
    admissions = relationship("Admission", back_populates="institution_course")

    __table_args__ = (
        UniqueConstraint("institution_id", "course_id", name="uq_institution_course"),
        Index("idx_ic_course", "course_id"),
        Index("idx_ic_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionCourse {self.institution_id}:{self.course_id}>"


class SavedInstitution(Base):
    """A user has bookmarked/saved an institution."""

    __tablename__ = "saved_institutions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="saved_institutions")
    institution = relationship("Institution", back_populates="saved_by")

    __table_args__ = (
        UniqueConstraint("user_id", "institution_id", name="uq_saved_institution_user"),
        Index("idx_saved_user", "user_id"),
        Index("idx_saved_institution", "institution_id"),
    )

    def __repr__(self) -> str:
        return f"<SavedInstitution {self.user_id}:{self.institution_id}>"
