from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class InstitutionType(Base):
    """Types of educational institutions."""
    __tablename__ = "institution_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # university, college, school, polytechnic, institute
    category = Column(String(50))  # higher_education, secondary, primary, technical, vocational
    display_order = Column(Integer, default=0)
    
    # Relationships
    institutions = relationship("Institution", back_populates="type")
    
    def __repr__(self) -> str:
        return f"<InstitutionType {self.name}>"


class Institution(Base):
    """Core institution data - the heart of ShikkhaHub."""
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name_en = Column(String(300), nullable=False, index=True)
    name_bn = Column(String(300), nullable=True)
    short_name = Column(String(100), nullable=True, index=True)
    slug = Column(String(300), unique=True, nullable=False, index=True)
    
    # Type & Classification
    type_id = Column(Integer, ForeignKey("institution_types.id"), nullable=False)
    established_year = Column(Integer, nullable=True)
    
    # Location
    upazila_id = Column(Integer, ForeignKey("upazilas.id"), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact (Primary - detailed in InstitutionContact)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Descriptions
    description = Column(Text, nullable=True)
    history = Column(Text, nullable=True)
    
    # Data Quality & Verification
    data_source = Column(String(100), nullable=True)  # bmeb, ugc, manual, scraped
    verification_status = Column(String(20), default="pending")  # verified, pending, flagged
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # SEO & Discovery
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)
    
    # AI/Search
    search_vector = Column(Text, nullable=True)  # For full-text search indexing
    keywords = Column(Text, nullable=True)  # Comma-separated for search
    
    # Relationships
    type = relationship("InstitutionType", back_populates="institutions")
    upazila = relationship("Upazila", back_populates="institutions")
    
    # Contacts (multiple)
    contacts = relationship("InstitutionContact", back_populates="institution", cascade="all, delete-orphan")
    
    # Requirements
    requirements = relationship("InstitutionRequirement", back_populates="institution", cascade="all, delete-orphan")
    
    # Courses offered
    courses = relationship("Course", back_populates="institution")
    
    # Reviews
    reviews = relationship("InstitutionReview", back_populates="institution", cascade="all, delete-orphan")
    
    # Affiliations
    affiliations = relationship("Affiliation", foreign_keys="Affiliation.institution_id", back_populates="institution")
    affiliated_members = relationship("Affiliation", foreign_keys="Affiliation.parent_institution_id", back_populates="parent_institution")
    
    # Education Boards
    education_boards = relationship(
        "EducationBoard",
        secondary="institution_boards",
        back_populates="affiliated_institutions"
    )
    
    # UGC/Authorities
    ugc_affiliations = relationship(
        "UniversityGrantCommission",
        secondary="institution_ugc",
        back_populates="affiliated_institutions"
    )
    
    __table_args__ = (
        Index('idx_institution_name', 'name_en'),
        Index('idx_institution_type', 'type_id'),
        Index('idx_institution_location', 'upazila_id'),
        Index('idx_institution_verification', 'verification_status'),
        Index('idx_institution_active', 'is_active'),
        Index('idx_institution_slug', 'slug'),
        Index('idx_institution_search_vector', 'search_vector'),
    )
    
    def __repr__(self) -> str:
        return f"<Institution {self.name_en}>"


class InstitutionContact(Base):
    """Multiple contacts for an institution."""
    __tablename__ = "institution_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    contact_type = Column(String(50), nullable=False)  # admission, admin, registrar, principal
    name = Column(String(200), nullable=True)
    designation = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    institution = relationship("Institution", back_populates="contacts")
    
    __table_args__ = (
        Index('idx_contact_institution', 'institution_id'),
        Index('idx_contact_type', 'contact_type'),
    )
    
    def __repr__(self) -> str:
        return f"<InstitutionContact {self.contact_type}>"


class InstitutionRequirement(Base):
    """Admission requirements for institutions."""
    __tablename__ = "institution_requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    requirement_type = Column(String(50), nullable=False)  # admission, scholarship, transfer
    level = Column(String(50), nullable=False)  # hsc, undergraduate, graduate
    min_gpa = Column(Float, nullable=True)
    required_subjects = Column(Text, nullable=True)  # JSON or comma-separated
    admission_test_required = Column(Boolean, default=False)
    admission_test_details = Column(Text, nullable=True)
    application_process = Column(Text, nullable=True)
    documents_required = Column(Text, nullable=True)  # JSON list
    fees = Column(Text, nullable=True)
    deadlines = Column(Text, nullable=True)
    
    # Relationships
    institution = relationship("Institution", back_populates="requirements")
    
    __table_args__ = (
        Index('idx_requirement_institution', 'institution_id'),
        Index('idx_requirement_type', 'requirement_type'),
        Index('idx_requirement_level', 'level'),
    )
    
    def __repr__(self) -> str:
        return f"<InstitutionRequirement {self.requirement_type}>"
