from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Index, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Subject(Base):
    """Subjects within courses."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)

    # Basic Info
    name_en = Column(String(200), nullable=False)
    name_bn = Column(String(200), nullable=True)
    code = Column(String(50), nullable=True)

    # Classification
    category = Column(
        String(100), nullable=True
    )  # science, arts, commerce, engineering, medical
    is_compulsory = Column(Boolean, default=False)
    is_core = Column(Boolean, default=False)  # Core subject vs elective

    # Academic Details
    credits = Column(Float, nullable=True)
    theory_hours = Column(Float, nullable=True)
    practical_hours = Column(Float, nullable=True)

    # Relationships
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=True
    )  # optional: subjects are standalone catalog nodes
    course = relationship("Course", back_populates="subjects")

    # Prerequisites (self-referential for subject chains)
    prerequisite_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    prerequisite = relationship(
        "Subject", remote_side="Subject.id", backref="required_for"
    )

    # Description
    description = Column(Text, nullable=True)
    topics_covered = Column(Text, nullable=True)  # JSON or text

    __table_args__ = (
        Index("idx_subject_name", "name_en"),
        Index("idx_subject_course", "course_id"),
        Index("idx_subject_category", "category"),
    )

    def __repr__(self) -> str:
        return f"<Subject {self.name_en}>"
