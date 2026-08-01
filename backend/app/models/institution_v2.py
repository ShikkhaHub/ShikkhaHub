"""
Enhanced Institution Models for National Education Platform
Priority: Data completeness, verification, trust
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.models.base import Base


class InstitutionType(str, enum.Enum):
    GOVERNMENT_COLLEGE = "government_college"
    PRIVATE_COLLEGE = "private_college"
    UNIVERSITY = "university"
    POLYTECHNIC = "polytechnic"
    INSTITUTE = "institute"
    MADRASAH = "madrasah"


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    OFFICIAL = "official"


class InstitutionV2(Base):
    """Enhanced Institution model with verification and data tracking"""
    __tablename__ = "institutions_v2"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic Info
    name = Column(String(255), nullable=False, unique=True)
    name_bengali = Column(String(255))
    name_slug = Column(String(255), unique=True)
    type = Column(Enum(InstitutionType), nullable=False)
    description = Column(String(1000))

    # Location Hierarchy (Critical for search)
    division = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)
    upazila = Column(String(100))
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)

    # Authority & Registration
    affiliation_authority = Column(String(255))  # "UGC", "Dhaka Board", "BTEB"
    affiliation_id = Column(String(100), unique=True)  # Government ID
    establishment_year = Column(Integer)
    registration_number = Column(String(100))

    # Contact Information
    phone_numbers = Column(JSON)  # ["0123456789", "0987654321"]
    email = Column(String(255))
    website_url = Column(String(500))
    admission_email = Column(String(255))
    admission_phone = Column(JSON)
    admission_process_url = Column(String(500))

    # Data Quality & Verification
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    data_completeness_score = Column(Integer, default=0)  # 0-100
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = Column(DateTime)
    verified_by = Column(String(255))
    verification_notes = Column(String(1000))

    # Trust Metrics
    trust_score = Column(Float, default=0.0)  # 0-1.0
    alumni_verification_count = Column(Integer, default=0)
    official_source_count = Column(Integer, default=0)

    # Statistics
    student_count = Column(Integer)
    faculty_count = Column(Integer)
    founded_year = Column(Integer)

    # Rankings & Ratings
    user_rating = Column(Float)  # 0-5
    review_count = Column(Integer, default=0)
    ranking_score = Column(Integer)

    # Internal Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    programs = relationship("ProgramV2", back_populates="institution", cascade="all, delete-orphan")
    data_sources = relationship("DataSourceV2", back_populates="institution", cascade="all, delete-orphan")
    verifications = relationship("VerificationRecordV2", back_populates="institution", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("ix_inst_division_district", "division", "district"),
        Index("ix_inst_type_verify", "type", "verification_status"),
        Index("ix_inst_trust_score", "trust_score"),
        Index("ix_inst_created", "created_at"),
    )


class ProgramV2(Base):
    """Enhanced Program/Course model"""
    __tablename__ = "programs_v2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions_v2.id"), nullable=False)

    # Program Info
    name = Column(String(255), nullable=False)
    name_bengali = Column(String(255))
    description = Column(String(1000))
    level = Column(String(50))  # diploma, bachelor, master, phd
    category = Column(String(100))  # engineering, science, arts, commerce, medical, law
    duration_years = Column(Integer)
    duration_semesters = Column(Integer)

    # Admission Requirements
    admission_requirements = Column(JSON)  # {min_gpa: 3.5, subjects: [...], tests: [...]}
    seats = Column(Integer)
    admission_process = Column(String(100))  # merit, entrance, mixed
    entrance_exam = Column(String(255))
    exam_difficulty = Column(String(50))  # easy, moderate, hard

    # Program Content
    subjects = Column(JSON)  # Array of subject names
    syllabus_url = Column(String(500))
    course_structure = Column(JSON)

    # Career & Outcomes
    career_paths = Column(JSON)  # Array of career options
    avg_salary_range = Column(JSON)  # {min: 30000, max: 100000}
    job_placement_rate = Column(Float)
    alumni_success_stories = Column(JSON)

    # Fees
    semester_fee = Column(Integer)
    total_fee = Column(Integer)
    scholarship_available = Column(Boolean, default=False)
    scholarship_details = Column(String(1000))

    # Verification
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    verified_from_source = Column(String(255))

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionV2", back_populates="programs")


class DataSourceV2(Base):
    """Track data collection sources"""
    __tablename__ = "data_sources_v2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions_v2.id"), nullable=False)

    # Source Info
    source_type = Column(String(50))  # official_website, ugc_directory, board_portal, scrape, alumni, api
    source_url = Column(String(500))
    source_name = Column(String(255))

    # Collection Details
    data_collected = Column(JSON)  # What was collected
    collection_date = Column(DateTime, default=datetime.utcnow)
    collection_method = Column(String(255))
    last_verified_date = Column(DateTime)

    # Trust Metrics
    confidence_score = Column(Float, default=0.5)  # 0-1.0
    is_official = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionV2", back_populates="data_sources")


class VerificationRecordV2(Base):
    """Track verification activities"""
    __tablename__ = "verification_records_v2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey("institutions_v2.id"), nullable=False)

    # Verification Type
    verification_type = Column(String(50))  # official_source, alumni_verified, admin_checked, crowd_verified
    verified_by = Column(String(255))  # User ID or "system" or authority name
    verified_date = Column(DateTime, default=datetime.utcnow)

    # What Was Verified
    fields_verified = Column(JSON)  # {name: true, courses: true, contact: false, ...}
    verification_confidence = Column(Float, default=0.8)  # 0-1.0
    verification_notes = Column(String(1000))

    # Status
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255))
    approved_at = Column(DateTime)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    institution = relationship("InstitutionV2", back_populates="verifications")


class AuthorityV2(Base):
    """Government & regulatory authorities"""
    __tablename__ = "authorities_v2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)  # "UGC", "Dhaka Board", "BTEB"
    name_bengali = Column(String(255))
    authority_type = Column(String(50))  # government, regulatory, international
    
    # Contact
    website = Column(String(500))
    email = Column(String(255))
    phone = Column(String(20))

    # API Integration
    api_endpoint = Column(String(500))
    api_credentials = Column(JSON)  # Encrypted in production
    api_last_sync = Column(DateTime)

    # Trust
    verification_weight = Column(Float, default=1.0)  # Higher = more trusted
    institutions_managed = Column(Integer, default=0)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
