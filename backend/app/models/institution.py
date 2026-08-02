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

# National education knowledge graph constants
INSTITUTION_OWNERSHIPS = ("government", "private", "trust", "autonomous")
INSTITUTION_EDUCATION_LEVELS = (
    "primary",
    "secondary",
    "higher_secondary",
    "diploma",
    "degree",
    "postgraduate",
)
INSTITUTION_STATUSES = ("active", "inactive", "suspended", "merged")
VERIFICATION_LEVELS = (0, 1, 2, 3)


class InstitutionType(Base):
    """Types of educational institutions."""

    __tablename__ = "institution_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(50), unique=True, nullable=False
    )  # university, college, school, polytechnic, institute
    category = Column(
        String(50)
    )  # higher_education, secondary, primary, technical, vocational
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
    ownership = Column(
        String(50), nullable=True, index=True
    )  # government, private, trust, autonomous
    education_level = Column(
        String(50), nullable=True, index=True
    )  # primary, secondary, higher_secondary, diploma, degree, postgraduate

    # National identifiers
    eiin = Column(
        String(20), unique=True, nullable=True, index=True
    )  # Education Institution Identification Number
    board = Column(
        String(50), nullable=True, index=True
    )  # dhaka, rajshahi, technical, madrasah, etc.
    university_affiliation = Column(String(200), nullable=True)
    ugc_approved = Column(Boolean, default=False)

    # Location (normalized to the national administrative graph)
    division_id = Column(Integer, ForeignKey("divisions.id"), nullable=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    upazila_id = Column(Integer, ForeignKey("upazilas.id"), nullable=True, index=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Contact (Primary - detailed in InstitutionContact)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    facebook = Column(String(255), nullable=True)

    # Media
    logo = Column(String(500), nullable=True)
    banner = Column(String(500), nullable=True)

    # Descriptions
    description = Column(Text, nullable=True)
    history = Column(Text, nullable=True)

    # Data Quality & Verification
    data_source = Column(String(100), nullable=True)  # bmeb, ugc, manual, scraped
    verification_status = Column(
        String(20), default="pending"
    )  # verified, pending, flagged
    verification_level = Column(
        Integer, default=0
    )  # 0 unverified, 1 basic, 2 enhanced, 3 fully verified
    status = Column(
        String(20), default="active", index=True
    )  # active, inactive, suspended, merged
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
    division = relationship("Division", back_populates="institutions")
    district = relationship("District", back_populates="institutions")
    upazila = relationship("Upazila", back_populates="institutions")

    # Contacts (multiple)
    contacts = relationship(
        "InstitutionContact", back_populates="institution", cascade="all, delete-orphan"
    )

    # Requirements
    requirements = relationship(
        "InstitutionRequirement",
        back_populates="institution",
        cascade="all, delete-orphan",
    )

    # Courses offered
    courses = relationship("Course", back_populates="institution")

    # Course offerings (normalized many-to-many with seat/fee/shift metadata)
    course_offerings = relationship(
        "InstitutionCourse", back_populates="institution", cascade="all, delete-orphan"
    )

    # Campuses
    campuses = relationship(
        "Campus", back_populates="institution", cascade="all, delete-orphan"
    )

    # Facilities
    facilities = relationship(
        "InstitutionFacility",
        back_populates="institution",
        cascade="all, delete-orphan",
    )

    # Gallery
    gallery = relationship(
        "GalleryImage", back_populates="institution", cascade="all, delete-orphan"
    )

    # Rankings & Accreditations
    rankings = relationship(
        "InstitutionRanking", back_populates="institution", cascade="all, delete-orphan"
    )
    accreditations = relationship(
        "Accreditation", back_populates="institution", cascade="all, delete-orphan"
    )

    # Announcements
    admissions = relationship(
        "Admission", back_populates="institution", cascade="all, delete-orphan"
    )
    notices = relationship(
        "Notice", back_populates="institution", cascade="all, delete-orphan"
    )
    scholarships = relationship(
        "Scholarship", back_populates="institution", cascade="all, delete-orphan"
    )

    # Reviews
    reviews = relationship(
        "InstitutionReview", back_populates="institution", cascade="all, delete-orphan"
    )

    # Affiliations
    affiliations = relationship(
        "Affiliation",
        foreign_keys="Affiliation.institution_id",
        back_populates="institution",
    )
    affiliated_members = relationship(
        "Affiliation",
        foreign_keys="Affiliation.parent_institution_id",
        back_populates="parent_institution",
    )

    # Education Boards
    education_boards = relationship(
        "EducationBoard",
        secondary="institution_boards",
        back_populates="affiliated_institutions",
    )

    # UGC/Authorities
    ugc_affiliations = relationship(
        "UniversityGrantCommission",
        secondary="institution_ugc",
        back_populates="affiliated_institutions",
    )

    # Saved by users
    saved_by = relationship(
        "SavedInstitution", back_populates="institution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_institution_name", "name_en"),
        Index("idx_institution_type", "type_id"),
        Index("idx_institution_location", "upazila_id"),
        Index("idx_institution_verification", "verification_status"),
        Index("idx_institution_active", "is_active"),
        Index("idx_institution_slug", "slug"),
        Index("idx_institution_search_vector", "search_vector"),
        Index("idx_institution_district", "district_id"),
        Index("idx_institution_division", "division_id"),
        Index("idx_institution_ownership", "ownership"),
        Index("idx_institution_education_level", "education_level"),
        Index("idx_institution_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Institution {self.name_en}>"


class InstitutionContact(Base):
    """Multiple contacts for an institution."""

    __tablename__ = "institution_contacts"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    contact_type = Column(
        String(50), nullable=False
    )  # admission, admin, registrar, principal
    name = Column(String(200), nullable=True)
    designation = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    is_primary = Column(Boolean, default=False)

    # Relationships
    institution = relationship("Institution", back_populates="contacts")

    __table_args__ = (
        Index("idx_contact_institution", "institution_id"),
        Index("idx_contact_type", "contact_type"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionContact {self.contact_type}>"


class InstitutionRequirement(Base):
    """Admission requirements for institutions."""

    __tablename__ = "institution_requirements"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    requirement_type = Column(
        String(50), nullable=False
    )  # admission, scholarship, transfer
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
        Index("idx_requirement_institution", "institution_id"),
        Index("idx_requirement_type", "requirement_type"),
        Index("idx_requirement_level", "level"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionRequirement {self.requirement_type}>"
