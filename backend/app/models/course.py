from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float, Index, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class CourseType(Base):
    """Types of courses (e.g., HSC, BSc, Diploma)."""
    __tablename__ = "course_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))  # secondary, undergraduate, graduate, diploma, certificate
    duration_months = Column(Integer, nullable=True)
    level = Column(String(50), nullable=True)  # national, international
    
    # Relationships
    courses = relationship("Course", back_populates="course_type")
    
    def __repr__(self) -> str:
        return f"<CourseType {self.name}>"


class Course(Base):
    """Courses offered by institutions."""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name_en = Column(String(300), nullable=False)
    name_bn = Column(String(300), nullable=True)
    code = Column(String(50), nullable=True)
    slug = Column(String(300), nullable=False, index=True)
    
    # Classification
    course_type_id = Column(Integer, ForeignKey("course_types.id"), nullable=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    
    # Academic Details
    duration_years = Column(Float, nullable=True)
    total_credits = Column(Integer, nullable=True)
    semester_system = Column(String(20), nullable=True)  # semester, yearly, trimester
    
    # Requirements
    min_qualification = Column(String(200), nullable=True)
    required_subjects = Column(Text, nullable=True)  # JSON or comma-separated
    
    # Career & Outcome
    career_prospects = Column(Text, nullable=True)
    further_study_options = Column(Text, nullable=True)
    
    # Description
    description = Column(Text, nullable=True)
    curriculum_outline = Column(Text, nullable=True)
    
    # Search & Discovery
    keywords = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    popularity_score = Column(Integer, default=0)
    
    # Relationships
    course_type = relationship("CourseType", back_populates="courses")
    institution = relationship("Institution", back_populates="courses")
    subjects = relationship("Subject", back_populates="course", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_course_name', 'name_en'),
        Index('idx_course_institution', 'institution_id'),
        Index('idx_course_type', 'course_type_id'),
        Index('idx_course_slug', 'slug'),
    )
    
    def __repr__(self) -> str:
        return f"<Course {self.name_en}>"
