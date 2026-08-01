"""
Data Pipeline Models - Raw and processed data storage
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Float, Boolean, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from app.core.database import Base


class RawData(Base):
    """Raw scraped data before processing"""
    __tablename__ = "raw_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source information
    source_type = Column(String(50), nullable=False, index=True)  # 'government', 'board', 'web', 'facebook', etc
    source_url = Column(String(1000), nullable=False)
    source_name = Column(String(200), nullable=True)  # e.g., "Dhaka Education Board", "UGC"
    
    # Raw data storage
    raw_json = Column(JSONB, nullable=False)  # Complete scraped data as JSON
    extracted_fields = Column(JSONB, nullable=True)  # Partially extracted fields
    
    # Processing status
    status = Column(String(20), default='pending', index=True)  # pending, processing, processed, error, skipped
    error_message = Column(Text, nullable=True)
    processing_attempts = Column(Integer, default=0)
    
    # Metadata
    scrape_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Matched institution (after deduplication)
    matched_institution_id = Column(Integer, nullable=True, index=True)
    match_confidence = Column(Float, nullable=True)  # 0-1.0, how confident dedup engine is
    
    __table_args__ = (
        Index('ix_raw_data_status_timestamp', 'status', 'scrape_timestamp'),
        Index('ix_raw_data_source_type', 'source_type'),
    )


class DataSource(Base):
    """Metadata about data sources"""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), unique=True, nullable=False)
    source_type = Column(String(50), nullable=False)  # government, board, web, social
    tier = Column(Integer, nullable=False)  # 1 (high trust), 2 (medium), 3 (low)
    trust_score = Column(Float, default=0.5)  # 0-1.0
    
    # Scraping config
    base_url = Column(String(1000), nullable=False)
    scraper_enabled = Column(Boolean, default=True)
    last_scraped = Column(DateTime, nullable=True)
    scrape_frequency_days = Column(Integer, default=30)  # Re-scrape every N days
    
    # Statistics
    total_records = Column(Integer, default=0)
    verified_records = Column(Integer, default=0)
    
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VerificationRecord(Base):
    """Track verification status of each institution"""
    __tablename__ = "verification_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    institution_id = Column(Integer, nullable=False, index=True)
    
    # Verification level (0=unverified, 1=source_verified, 2=admin_approved, 3=institution_confirmed)
    verification_level = Column(Integer, default=0, index=True)
    
    # Sources used for verification
    verified_sources = Column(JSON, default=[])  # List of data_source IDs
    
    # Admin notes
    admin_notes = Column(Text, nullable=True)
    verified_by_admin = Column(String(100), nullable=True)
    
    # Completeness tracking
    field_completeness = Column(JSONB, default={})  # {field: percentage_complete}
    missing_fields = Column(JSON, default=[])
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index('ix_verification_level', 'verification_level'),
    )


class DuplicateCandidate(Base):
    """Track potential duplicate institutions found by dedup engine"""
    __tablename__ = "duplicate_candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Two institutions that might be duplicates
    institution_id_1 = Column(Integer, nullable=False, index=True)
    institution_id_2 = Column(Integer, nullable=False, index=True)
    
    # Why they might be duplicates
    similarity_score = Column(Float, nullable=False)  # 0-1.0
    match_reason = Column(String(200))  # "name_match", "phone_match", "location_match", etc
    
    # Resolution
    resolved = Column(Boolean, default=False)
    resolved_action = Column(String(20), nullable=True)  # 'merge', 'keep_separate', 'unrelated'
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ScrapingJob(Base):
    """Track scraping job history"""
    __tablename__ = "scraping_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    data_source_id = Column(Integer, nullable=False, index=True)
    
    # Job status
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    
    # Results
    records_scraped = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_log = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
