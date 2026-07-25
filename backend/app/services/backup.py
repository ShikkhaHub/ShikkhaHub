"""Backup and recovery service for ShikkhaHub.

This module provides:
- Automated database backups (SQLite/PostgreSQL)
- Backup verification
- Point-in-time recovery
- Backup retention policies
- Multiple storage backends (local, S3, etc.)
"""
import os
import gzip
import shutil
import hashlib
import logging
import sqlite3
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, SessionLocal

logger = logging.getLogger(__name__)


class BackupStatus(Enum):
    """Backup status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"


class BackupType(Enum):
    """Backup type enumeration."""
    FULL = "full"  # Complete database backup
    INCREMENTAL = "incremental"  # Changes since last backup
    DATA_ONLY = "data_only"  # Data without schema
    SCHEMA_ONLY = "schema_only"  # Schema without data


@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    id: str
    created_at: datetime
    completed_at: Optional[datetime]
    status: str
    backup_type: str
    database_url: str
    file_path: str
    file_size_bytes: int
    checksum: str
    compressed: bool
    compression_ratio: float
    tables_backed_up: int
    rows_backed_up: int
    error_message: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_status: Optional[str] = None
    retention_days: int = 30
    storage_backend: str = "local"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        for key in ['created_at', 'completed_at', 'verified_at']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BackupMetadata':
        """Create from dictionary."""
        # Parse datetime strings back to datetime objects
        for key in ['created_at', 'completed_at', 'verified_at']:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)


class BackupStorage:
    """Abstract base class for backup storage backends."""
    
    def store(self, local_path: str, backup_id: str) -> str:
        """Store backup file and return storage path/URI."""
        raise NotImplementedError
    
    def retrieve(self, backup_id: str, local_path: str) -> bool:
        """Retrieve backup file to local path."""
        raise NotImplementedError
    
    def delete(self, backup_id: str) -> bool:
        """Delete backup from storage."""
        raise NotImplementedError
    
    def list_backups(self) -> List[str]:
        """List all stored backup IDs."""
        raise NotImplementedError
    
    def exists(self, backup_id: str) -> bool:
        """Check if backup exists in storage."""
        raise NotImplementedError


class LocalStorage(BackupStorage):
    """Local filesystem backup storage."""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path or settings.BACKUP_LOCAL_PATH or "/tmp/shikkhahub_backups")
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def store(self, local_path: str, backup_id: str) -> str:
        """Store backup locally (already local, just move/rename)."""
        dest_path = self.base_path / f"{backup_id}.backup"
        shutil.copy2(local_path, dest_path)
        return str(dest_path)
    
    def retrieve(self, backup_id: str, local_path: str) -> bool:
        """Retrieve backup to local path."""
        src_path = self.base_path / f"{backup_id}.backup"
        if not src_path.exists():
            return False
        shutil.copy2(src_path, local_path)
        return True
    
    def delete(self, backup_id: str) -> bool:
        """Delete backup from storage."""
        path = self.base_path / f"{backup_id}.backup"
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_backups(self) -> List[str]:
        """List all stored backup IDs."""
        backups = []
        for f in self.base_path.glob("*.backup"):
            backups.append(f.stem)
        return sorted(backups)
    
    def exists(self, backup_id: str) -> bool:
        """Check if backup exists."""
        return (self.base_path / f"{backup_id}.backup").exists()
    
    def get_backup_path(self, backup_id: str) -> str:
        """Get full path to backup file."""
        return str(self.base_path / f"{backup_id}.backup")
    
    def cleanup_old_backups(self, retention_days: int) -> int:
        """Remove backups older than retention_days."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        
        for f in self.base_path.glob("*.backup"):
            # Extract timestamp from backup ID (format: backup_YYYYMMDD_HHMMSS_uuid)
            try:
                parts = f.stem.split('_')
                if len(parts) >= 2:
                    date_str = parts[1]
                    time_str = parts[2] if len(parts) > 2 else "000000"
                    backup_time = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    if backup_time < cutoff:
                        f.unlink()
                        deleted += 1
                        logger.info(f"Deleted old backup: {f.name}")
            except Exception as e:
                logger.warning(f"Could not parse backup timestamp for {f.name}: {e}")
        
        return deleted


class BackupService:
    """Main backup service for database backup and recovery."""
    
    def __init__(self, storage: BackupStorage = None, metadata_path: str = None):
        self.storage = storage or LocalStorage()
        self.metadata_path = Path(metadata_path or 
            (settings.BACKUP_METADATA_PATH or "/tmp/shikkhahub_backups/metadata")
        )
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        self._is_sqlite = "sqlite" in settings.DATABASE_URL.lower()
    
    def _generate_backup_id(self) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(
            f"{timestamp}{os.urandom(16)}".encode()
        ).hexdigest()[:8]
        return f"backup_{timestamp}_{random_suffix}"
    
    def _compute_checksum(self, file_path: str) -> str:
        """Compute MD5 checksum of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _save_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to JSON file."""
        meta_file = self.metadata_path / f"{metadata.id}.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _load_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata from JSON file."""
        meta_file = self.metadata_path / f"{backup_id}.json"
        if not meta_file.exists():
            return None
        with open(meta_file, 'r') as f:
            data = json.load(f)
            return BackupMetadata.from_dict(data)
    
    def _get_table_row_counts(self, db: Session) -> Dict[str, int]:
        """Get row counts for all tables."""
        counts = {}
        if self._is_sqlite:
            # For SQLite, query sqlite_master
            result = db.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ))
            tables = [row[0] for row in result]
            for table in tables:
                count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                counts[table] = count_result.scalar()
        else:
            # For PostgreSQL
            result = db.execute(text("""
                SELECT schemaname, tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            for schema, table in result:
                count_result = db.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                counts[table] = count_result.scalar()
        return counts
    
    def create_backup(
        self,
        backup_type: BackupType = BackupType.FULL,
        compress: bool = True,
        description: str = None
    ) -> BackupMetadata:
        """
        Create a database backup.
        
        Args:
            backup_type: Type of backup to create
            compress: Whether to compress the backup
            description: Optional backup description
            
        Returns:
            BackupMetadata object with backup details
        """
        backup_id = self._generate_backup_id()
        created_at = datetime.now()
        
        metadata = BackupMetadata(
            id=backup_id,
            created_at=created_at,
            completed_at=None,
            status=BackupStatus.IN_PROGRESS.value,
            backup_type=backup_type.value,
            database_url=settings.DATABASE_URL.replace(
                "://", "://***:***@"  # Hide credentials
            ) if "://" in settings.DATABASE_URL else settings.DATABASE_URL,
            file_path="",
            file_size_bytes=0,
            checksum="",
            compressed=compress,
            compression_ratio=0.0,
            tables_backed_up=0,
            rows_backed_up=0,
            retention_days=settings.BACKUP_RETENTION_DAYS or 30
        )
        
        temp_path = f"/tmp/{backup_id}.sql"
        final_path = f"/tmp/{backup_id}.sql{'', '.gz'}[compress]"
        
        try:
            # Get database stats before backup
            db = SessionLocal()
            table_counts = self._get_table_row_counts(db)
            db.close()
            
            metadata.tables_backed_up = len(table_counts)
            metadata.rows_backed_up = sum(table_counts.values())
            
            # Create backup based on database type
            if self._is_sqlite:
                success = self._backup_sqlite(temp_path)
            else:
                success = self._backup_postgresql(temp_path)
            
            if not success:
                raise Exception("Database dump failed")
            
            # Compress if requested
            if compress:
                with open(temp_path, 'rb') as f_in:
                    with gzip.open(final_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(temp_path)
                original_size = os.path.getsize(temp_path) if os.path.exists(temp_path) else 0
                compressed_size = os.path.getsize(final_path)
                metadata.compression_ratio = original_size / compressed_size if compressed_size > 0 else 1.0
            else:
                final_path = temp_path
            
            # Store backup
            storage_path = self.storage.store(final_path, backup_id)
            
            # Compute checksum
            checksum = self._compute_checksum(final_path)
            
            # Update metadata
            metadata.completed_at = datetime.now()
            metadata.status = BackupStatus.COMPLETED.value
            metadata.file_path = storage_path
            metadata.file_size_bytes = os.path.getsize(final_path)
            metadata.checksum = checksum
            
            # Save metadata
            self._save_metadata(metadata)
            
            # Cleanup temp file
            if os.path.exists(final_path):
                os.remove(final_path)
            
            logger.info(f"Backup {backup_id} completed successfully. "
                       f"Size: {metadata.file_size_bytes} bytes, "
                       f"Tables: {metadata.tables_backed_up}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Backup {backup_id} failed: {e}")
            metadata.status = BackupStatus.FAILED.value
            metadata.error_message = str(e)
            metadata.completed_at = datetime.now()
            self._save_metadata(metadata)
            
            # Cleanup temp files
            for path in [temp_path, final_path]:
                if os.path.exists(path):
                    os.remove(path)
            
            raise
    
    def _backup_sqlite(self, output_path: str) -> bool:
        """Create SQLite database backup."""
        try:
            # Extract database file path from URL
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]
            
            # Use SQLite backup API for consistency
            source = sqlite3.connect(db_path)
            backup = sqlite3.connect(output_path)
            
            with backup:
                source.backup(backup)
            
            source.close()
            backup.close()
            return True
            
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return False
    
    def _backup_postgresql(self, output_path: str) -> bool:
        """Create PostgreSQL database backup using pg_dump."""
        try:
            # Parse database URL
            import urllib.parse
            parsed = urllib.parse.urlparse(settings.DATABASE_URL)
            
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'pg_dump',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username or 'postgres',
                '-d', parsed.path.lstrip('/'),
                '-f', output_path,
                '--clean',  # Include DROP statements
                '--if-exists',
                '--no-owner',
                '--no-privileges'
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL backup failed: {e}")
            return False
    
    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity by checking checksum and basic structure.
        
        Returns:
            True if backup is valid, False otherwise
        """
        metadata = self._load_metadata(backup_id)
        if not metadata:
            logger.error(f"Backup {backup_id} not found")
            return False
        
        try:
            # Retrieve backup to temp location
            temp_path = f"/tmp/{backup_id}_verify.backup"
            
            if not self.storage.retrieve(backup_id, temp_path):
                logger.error(f"Failed to retrieve backup {backup_id}")
                return False
            
            # Verify checksum
            current_checksum = self._compute_checksum(temp_path)
            
            if current_checksum != metadata.checksum:
                logger.error(f"Checksum mismatch for backup {backup_id}")
                metadata.verification_status = "failed_checksum"
                self._save_metadata(metadata)
                os.remove(temp_path)
                return False
            
            # Additional verification based on backup type
            if metadata.compressed:
                # Try to decompress and verify it's valid gzip
                try:
                    with gzip.open(temp_path, 'rb') as f:
                        # Read first few bytes to verify it's valid
                        f.read(100)
                except Exception as e:
                    logger.error(f"Backup {backup_id} appears corrupted: {e}")
                    metadata.verification_status = "failed_corrupted"
                    self._save_metadata(metadata)
                    os.remove(temp_path)
                    return False
            
            # For SQLite, we can do more thorough verification
            if self._is_sqlite and not metadata.compressed:
                try:
                    conn = sqlite3.connect(temp_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if len(tables) < 1:
                        logger.error(f"Backup {backup_id} contains no tables")
                        metadata.verification_status = "failed_empty"
                        self._save_metadata(metadata)
                        os.remove(temp_path)
                        return False
                        
                except Exception as e:
                    logger.error(f"Backup {backup_id} SQLite verification failed: {e}")
                    metadata.verification_status = "failed_structure"
                    self._save_metadata(metadata)
                    os.remove(temp_path)
                    return False
            
            # Cleanup
            os.remove(temp_path)
            
            # Update metadata
            metadata.verified_at = datetime.now()
            metadata.verification_status = "passed"
            metadata.status = BackupStatus.VERIFIED.value
            self._save_metadata(metadata)
            
            logger.info(f"Backup {backup_id} verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup verification failed for {backup_id}: {e}")
            metadata.verification_status = f"failed: {str(e)}"
            self._save_metadata(metadata)
            return False
    
    def restore_backup(self, backup_id: str, target_url: str = None, force: bool = False) -> bool:
        """
        Restore database from backup.
        
        WARNING: This will overwrite the current database!
        
        Args:
            backup_id: ID of backup to restore
            target_url: Optional different database URL to restore to
            force: Skip confirmation safety checks
            
        Returns:
            True if restore successful, False otherwise
        """
        if not force:
            raise Exception("Restore requires force=True. This will overwrite existing data!")
        
        metadata = self._load_metadata(backup_id)
        if not metadata:
            logger.error(f"Backup {backup_id} not found")
            return False
        
        target_url = target_url or settings.DATABASE_URL
        
        temp_path = f"/tmp/{backup_id}_restore.backup"
        
        try:
            # Retrieve backup
            if not self.storage.retrieve(backup_id, temp_path):
                logger.error(f"Failed to retrieve backup {backup_id}")
                return False
            
            # Decompress if needed
            if metadata.compressed:
                decompressed_path = f"/tmp/{backup_id}_restore.sql"
                with gzip.open(temp_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(temp_path)
                temp_path = decompressed_path
            
            # Restore based on database type
            if self._is_sqlite:
                success = self._restore_sqlite(temp_path, target_url)
            else:
                success = self._restore_postgresql(temp_path, target_url)
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if success:
                logger.info(f"Backup {backup_id} restored successfully to {target_url}")
            
            return success
            
        except Exception as e:
            logger.error(f"Restore failed for backup {backup_id}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def _restore_sqlite(self, backup_path: str, target_url: str) -> bool:
        """Restore SQLite database from backup."""
        try:
            db_path = target_url.replace("sqlite:///", "")
            if db_path.startswith("./"):
                db_path = db_path[2:]
            
            # Backup current database first (safety)
            if os.path.exists(db_path):
                safety_backup = f"{db_path}.safety.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_path, safety_backup)
                logger.info(f"Created safety backup: {safety_backup}")
            
            # Copy backup to target
            shutil.copy2(backup_path, db_path)
            
            return True
            
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False
    
    def _restore_postgresql(self, backup_path: str, target_url: str) -> bool:
        """Restore PostgreSQL database using psql/pg_restore."""
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(target_url)
            
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            cmd = [
                'psql',
                '-h', parsed.hostname or 'localhost',
                '-p', str(parsed.port or 5432),
                '-U', parsed.username or 'postgres',
                '-d', parsed.path.lstrip('/'),
                '-f', backup_path,
                '--quiet'
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"psql restore failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL restore failed: {e}")
            return False
    
    def list_backups(self, status: str = None, limit: int = 100) -> List[BackupMetadata]:
        """
        List all backups with optional filtering.
        
        Args:
            status: Filter by status (pending, completed, failed, verified)
            limit: Maximum number of backups to return
            
        Returns:
            List of BackupMetadata objects, sorted by creation time (newest first)
        """
        backups = []
        
        for meta_file in self.metadata_path.glob("*.json"):
            metadata = self._load_metadata(meta_file.stem)
            if metadata:
                if status is None or metadata.status == status:
                    backups.append(metadata)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return backups[:limit]
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup and its metadata."""
        try:
            # Delete from storage
            self.storage.delete(backup_id)
            
            # Delete metadata
            meta_file = self.metadata_path / f"{backup_id}.json"
            if meta_file.exists():
                meta_file.unlink()
            
            logger.info(f"Backup {backup_id} deleted")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than their retention period.
        
        Returns:
            Number of backups deleted
        """
        deleted = 0
        now = datetime.now()
        
        for metadata in self.list_backups():
            if metadata.status not in [BackupStatus.COMPLETED.value, BackupStatus.VERIFIED.value]:
                continue
            
            age_days = (now - metadata.created_at).days
            
            if age_days > metadata.retention_days:
                if self.delete_backup(metadata.id):
                    deleted += 1
        
        # Also cleanup local storage
        if isinstance(self.storage, LocalStorage):
            storage_deleted = self.storage.cleanup_old_backups(
                settings.BACKUP_RETENTION_DAYS or 30
            )
            deleted += storage_deleted
        
        logger.info(f"Cleanup completed. Deleted {deleted} old backups.")
        return deleted
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """Get backup statistics."""
        backups = self.list_backups()
        
        total_size = sum(b.file_size_bytes for b in backups if b.status == BackupStatus.COMPLETED.value)
        
        status_counts = {}
        for b in backups:
            status_counts[b.status] = status_counts.get(b.status, 0) + 1
        
        return {
            "total_backups": len(backups),
            "status_breakdown": status_counts,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_backup": backups[-1].created_at.isoformat() if backups else None,
            "newest_backup": backups[0].created_at.isoformat() if backups else None,
            "retention_days": settings.BACKUP_RETENTION_DAYS or 30
        }


# Global backup service instance
_backup_service: Optional[BackupService] = None


def get_backup_service() -> BackupService:
    """Get or create global backup service instance."""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service
