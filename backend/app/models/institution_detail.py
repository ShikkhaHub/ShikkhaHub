"""Institution detail entities for the national education knowledge graph.

These tables model the fine-grained structure of an institution:
campuses, facilities, gallery, rankings and accreditations.
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


class Campus(Base):
    """Campuses of an institution (some universities have multiple campuses)."""

    __tablename__ = "campuses"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    name_en = Column(String(300), nullable=False)
    name_bn = Column(String(300), nullable=True)
    campus_type = Column(String(50), default="main")  # main, permanent, temporary, city
    division_id = Column(Integer, ForeignKey("divisions.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    upazila_id = Column(Integer, ForeignKey("upazilas.id"), nullable=True)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    area_sqft = Column(Float, nullable=True)
    established_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="campuses")

    # AR campus tours
    ar_pois = relationship("CampusPOI", back_populates="campus")
    ar_tours = relationship("CampusTour", back_populates="campus")

    __table_args__ = (
        Index("idx_campus_institution", "institution_id"),
        Index("idx_campus_location", "upazila_id"),
    )

    def __repr__(self) -> str:
        return f"<Campus {self.name_en}>"


class FacilityType(Base):
    """Catalog of facility types (library, lab, hostel, playground, ...)."""

    __tablename__ = "facility_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    name_bn = Column(String(100), nullable=True)
    icon = Column(String(100), nullable=True)
    display_order = Column(Integer, default=0)

    institutions = relationship("InstitutionFacility", back_populates="facility_type")

    def __repr__(self) -> str:
        return f"<FacilityType {self.name}>"


class InstitutionFacility(Base):
    """Availability of a facility at an institution."""

    __tablename__ = "institution_facilities"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    facility_type_id = Column(
        Integer, ForeignKey("facility_types.id"), nullable=False, index=True
    )
    is_available = Column(Boolean, default=True)
    capacity = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    institution = relationship("Institution", back_populates="facilities")
    facility_type = relationship("FacilityType", back_populates="institutions")

    __table_args__ = (
        Index(
            "idx_facility_institution_type",
            "institution_id",
            "facility_type_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<InstitutionFacility {self.institution_id}:{self.facility_type_id}>"


class GalleryImage(Base):
    """Photos in an institution's gallery."""

    __tablename__ = "gallery_images"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    title = Column(String(300), nullable=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    category = Column(
        String(50), default="campus"
    )  # campus, building, lab, hostel, event
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="gallery")

    __table_args__ = (Index("idx_gallery_institution", "institution_id"),)

    def __repr__(self) -> str:
        return f"<GalleryImage {self.id}>"


class InstitutionRanking(Base):
    """Ranking of an institution within a category/level/year."""

    __tablename__ = "institution_rankings"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    ranking_type = Column(
        String(50), nullable=False
    )  # national, university_grants, subject_wise, city
    category = Column(
        String(100), nullable=True
    )  # overall, engineering, medical, business
    year = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)  # ugc, bmeb, manual
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="rankings")

    __table_args__ = (
        Index("idx_ranking_institution", "institution_id"),
        Index("idx_ranking_type_year", "ranking_type", "year"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionRanking {self.institution_id} #{self.rank} {self.year}>"


class Accreditation(Base):
    """Accreditations and certifications held by an institution."""

    __tablename__ = "accreditations"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    accrediting_body = Column(String(200), nullable=False)  # BAETE, IEB, UGC, ministry
    accreditation_type = Column(String(100), nullable=True)
    certificate_number = Column(String(100), nullable=True)
    awarded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, expired, revoked
    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="accreditations")

    __table_args__ = (Index("idx_accreditation_institution", "institution_id"),)

    def __repr__(self) -> str:
        return f"<Accreditation {self.accrediting_body}>"
