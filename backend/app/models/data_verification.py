"""Data verification and provenance layer for the national education knowledge graph.

Every piece of institution data on ShikkhaHub must be traceable back to its
source. These tables model the full lifecycle:

- `RawSource`       -> an authoritative origin (UGC, BMED, education board, manual)
- `ScrapeJob`       -> a single crawl/import run against a source
- `ScrapedRecord`   -> one raw record harvested by a job (immutable, deduplicated)
- `VerificationQueue` -> candidate records awaiting human/official review
- `ChangeRequest`   -> community/official proposed edits to an institution
- `InstitutionHistory` -> append-only audit trail of every field change
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class RawSource(Base):
    """Authoritative origin of education data (government or manual)."""

    __tablename__ = "raw_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)  # UGC, BMED, Board-1, manual
    name_bn = Column(String(200), nullable=True)
    source_type = Column(
        String(50), default="government"
    )  # government, official_api, manual, community
    base_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    reliability_score = Column(Float, default=0.5)  # 0-1 trust weight
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scrape_jobs = relationship("ScrapeJob", back_populates="raw_source")

    __table_args__ = (Index("idx_raw_source_type", "source_type"),)

    def __repr__(self) -> str:
        return f"<RawSource {self.name}>"


class ScrapeJob(Base):
    """A single crawl/import run against a raw source."""

    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    raw_source_id = Column(
        Integer, ForeignKey("raw_sources.id"), nullable=False, index=True
    )
    status = Column(
        String(20), default="pending"
    )  # pending, running, completed, failed, cancelled
    records_found = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    raw_source = relationship("RawSource", back_populates="scrape_jobs")
    scraped_records = relationship(
        "ScrapedRecord", back_populates="scrape_job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_scrape_job_source_status", "raw_source_id", "status"),
        Index("idx_scrape_job_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ScrapeJob {self.id} source={self.raw_source_id} {self.status}>"


class ScrapedRecord(Base):
    """One immutable raw record harvested by a scrape job."""

    __tablename__ = "scraped_records"

    id = Column(Integer, primary_key=True, index=True)
    scrape_job_id = Column(
        Integer, ForeignKey("scrape_jobs.id"), nullable=False, index=True
    )
    record_type = Column(
        String(50), nullable=False, index=True
    )  # institution, course, admission, notice, scholarship
    external_id = Column(String(200), nullable=True)  # ID as known by the source
    raw_data = Column(Text, nullable=False)  # JSON blob as harvested
    checksum = Column(String(64), nullable=True, index=True)  # sha256 for dedup
    status = Column(
        String(20), default="new"
    )  # new, imported, updated, skipped, duplicate, failed
    source_url = Column(String(500), nullable=True)
    confidence_score = Column(Float, nullable=True)  # 0-1
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    scrape_job = relationship("ScrapeJob", back_populates="scraped_records")
    verification_queue_items = relationship(
        "VerificationQueue", back_populates="scraped_record"
    )

    __table_args__ = (
        UniqueConstraint("checksum", name="uq_scraped_record_checksum"),
        Index("idx_scraped_type_status", "record_type", "status"),
    )

    def __repr__(self) -> str:
        return f"<ScrapedRecord {self.id} type={self.record_type} {self.status}>"


class VerificationQueue(Base):
    """Candidate records awaiting human or official verification."""

    __tablename__ = "verification_queue"

    id = Column(Integer, primary_key=True, index=True)
    scraped_record_id = Column(
        Integer, ForeignKey("scraped_records.id"), nullable=True, index=True
    )
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=True, index=True
    )
    record_type = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=True)  # which field to verify
    current_value = Column(Text, nullable=True)
    suggested_value = Column(Text, nullable=True)
    source_summary = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    status = Column(
        String(20), default="pending"
    )  # pending, in_review, verified, rejected, auto_verified
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scraped_record = relationship(
        "ScrapedRecord", back_populates="verification_queue_items"
    )
    institution = relationship("Institution")

    __table_args__ = (
        Index("idx_vq_status_priority", "status", "priority"),
        Index("idx_vq_type", "record_type"),
    )

    def __repr__(self) -> str:
        return f"<VerificationQueue {self.id} {self.record_type} {self.status}>"


class ChangeRequest(Base):
    """Community/official proposal to edit an institution's data."""

    __tablename__ = "change_requests"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(
        String(20), default="pending"
    )  # pending, approved, rejected, merged, withdrawn
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    institution = relationship("Institution")

    __table_args__ = (
        Index("idx_change_req_institution", "institution_id", "status"),
        Index("idx_change_req_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<ChangeRequest {self.id} {self.field_name} {self.status}>"


class InstitutionHistory(Base):
    """Append-only audit trail of every change to an institution record."""

    __tablename__ = "institution_history"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_type = Column(
        String(20), default="update"
    )  # create, update, merge, delete, verify
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    source = Column(String(100), nullable=True)  # manual, api, scrape, system, community
    change_request_id = Column(
        Integer, ForeignKey("change_requests.id"), nullable=True, index=True
    )
    context = Column(Text, nullable=True)  # JSON context
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    institution = relationship("Institution")

    __table_args__ = (
        Index("idx_institution_history_inst", "institution_id", "created_at"),
        Index("idx_institution_history_field", "field_name"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionHistory {self.institution_id} {self.field_name}>"
