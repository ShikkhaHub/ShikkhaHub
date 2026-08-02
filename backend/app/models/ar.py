"""Augmented Reality (AR) campus tour entities.

Supports the AR Campus Tours roadmap component:

- `CampusPOI` - geolocated points of interest on a campus (gate, library,
  admission office, departments, facilities) with AR overlay metadata. This
  is the "spatial data" that lets AR elements be placed correctly.
- `ARAsset` - lightweight asset records (3D model / image / video overlays)
  referenced by POIs, kept lean for fast mobile loading.
- `CampusTour` / `TourStop` - curated walking tours that chain POIs into an
  ordered, navigable route (wayfinding between stops is computed from the
  stored coordinates).
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ARAsset(Base):
    """Lightweight media asset used as an AR overlay for a POI.

    Kept intentionally small (URL + type + size) so the mobile app can fetch
    only what is needed and load it quickly.
    """

    __tablename__ = "ar_assets"

    id = Column(Integer, primary_key=True, index=True)
    poi_id = Column(Integer, ForeignKey("ar_pois.id"), nullable=False, index=True)

    asset_type = Column(String(20), nullable=False)  # glb, usdz, image, video, audio
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    size_kb = Column(Integer, nullable=True)
    format = Column(String(20), nullable=True)  # gltf/glb, usdz, jpeg, mp4, mp3
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    poi = relationship("CampusPOI", back_populates="assets")

    __table_args__ = (
        Index("idx_ar_asset_poi", "poi_id"),
        Index("idx_ar_asset_type", "asset_type"),
    )

    def __repr__(self) -> str:
        return f"<ARAsset {self.asset_type} poi={self.poi_id}>"


class CampusPOI(Base):
    """A geolocated point of interest on a campus for AR tours.

    `latitude`/`longitude` are GPS coordinates the AR client uses to pin
    overlays to the real world; `marker_type` supports both GPS-anchored and
    visual-marker recognition strategies.
    """

    __tablename__ = "ar_pois"

    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )

    # Identity
    name_en = Column(String(300), nullable=False)
    name_bn = Column(String(300), nullable=True)
    category = Column(
        String(50), nullable=False, index=True
    )  # gate, admission_office, library, lab, department, hostel,
    #   auditorium, cafeteria, playground, landmark
    subcategory = Column(String(100), nullable=True)  # e.g. department name

    # Geolocation (the spatial-data foundation for AR anchoring)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude_m = Column(Float, nullable=True)
    heading_deg = Column(Float, nullable=True)  # camera orientation hint
    radius_m = Column(Float, default=15.0)  # activation radius for the overlay

    # Tracking strategy
    marker_type = Column(String(20), default="gps")  # gps, image_marker, qr, none
    marker_image_url = Column(String(500), nullable=True)

    # Content surfaced in the AR overlay
    title = Column(String(300), nullable=True)
    short_description = Column(Text, nullable=True)
    info_tags = Column(Text, nullable=True)  # JSON list, e.g. opening hours, seats
    department_summary = Column(Text, nullable=True)
    opening_hours = Column(String(200), nullable=True)

    # Ordering & state
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campus = relationship("Campus", back_populates="ar_pois")
    institution = relationship("Institution", back_populates="ar_pois")
    assets = relationship(
        "ARAsset",
        back_populates="poi",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_ar_poi_campus", "campus_id"),
        Index("idx_ar_poi_category", "category"),
        Index("idx_ar_poi_institution", "institution_id"),
        Index("idx_ar_poi_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<CampusPOI {self.name_en} ({self.latitude},{self.longitude})>"


class CampusTour(Base):
    """A curated AR walking tour for a campus."""

    __tablename__ = "ar_tours"

    id = Column(Integer, primary_key=True, index=True)
    campus_id = Column(Integer, ForeignKey("campuses.id"), nullable=False, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )

    title = Column(String(300), nullable=False)
    title_bn = Column(String(300), nullable=True)
    description = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    distance_m = Column(Float, nullable=True)
    difficulty = Column(String(20), default="easy")  # easy, moderate, accessible
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    campus = relationship("Campus", back_populates="ar_tours")
    stops = relationship(
        "TourStop", back_populates="tour", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_ar_tour_campus", "campus_id"),
        Index("idx_ar_tour_institution", "institution_id"),
        Index("idx_ar_tour_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<CampusTour {self.title}>"


class TourStop(Base):
    """A POI as part of an ordered tour, with optional wayfinding hints."""

    __tablename__ = "ar_tour_stops"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("ar_tours.id"), nullable=False, index=True)
    poi_id = Column(Integer, ForeignKey("ar_pois.id"), nullable=False, index=True)
    position = Column(Integer, default=0)  # 1-based order along the route
    narration = Column(Text, nullable=True)  # audio/AR narration script
    dwell_seconds = Column(Integer, default=30)  # suggested time at this stop

    tour = relationship("CampusTour", back_populates="stops")
    poi = relationship("CampusPOI")

    __table_args__ = (
        UniqueConstraint("tour_id", "poi_id", name="uq_tour_stop_poi"),
        Index("idx_tour_stop_position", "tour_id", "position"),
    )

    def __repr__(self) -> str:
        return f"<TourStop tour={self.tour_id} #{self.position} poi={self.poi_id}>"
