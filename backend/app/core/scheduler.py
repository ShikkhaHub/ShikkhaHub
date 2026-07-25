"""Background task scheduler for ShikkhaHub.

This module provides:
- Automated backup scheduling
- Periodic cleanup tasks
- Background job management
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Callable, List
from dataclasses import dataclass
from croniter import croniter

from app.core.config import settings
from app.services.backup import get_backup_service, BackupType

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """A scheduled task."""
    name: str
    cron_expression: str
    callback: Callable
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True


class TaskScheduler:
    """Simple cron-based task scheduler."""
    
    def __init__(self, check_interval_seconds: int = 60):
        self.tasks: List[ScheduledTask] = []
        self.check_interval = check_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def add_task(self, name: str, cron_expression: str, callback: Callable) -> ScheduledTask:
        """Add a scheduled task."""
        task = ScheduledTask(
            name=name,
            cron_expression=cron_expression,
            callback=callback
        )
        task.next_run = self._calculate_next_run(cron_expression)
        self.tasks.append(task)
        logger.info(f"Added scheduled task: {name} (next run: {task.next_run})")
        return task
    
    def remove_task(self, name: str):
        """Remove a scheduled task."""
        self.tasks = [t for t in self.tasks if t.name != name]
    
    def _calculate_next_run(self, cron_expression: str, base_time: datetime = None) -> datetime:
        """Calculate next run time from cron expression."""
        base = base_time or datetime.now()
        itr = croniter(cron_expression, base)
        return itr.get_next(datetime)
    
    def _should_run(self, task: ScheduledTask, now: datetime) -> bool:
        """Check if task should run now."""
        if not task.enabled or not task.next_run:
            return False
        return now >= task.next_run
    
    async def _run_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        logger.info(f"Running scheduled task: {task.name}")
        task.last_run = datetime.now()
        
        try:
            # Handle both sync and async callbacks
            if asyncio.iscoroutinefunction(task.callback):
                await task.callback()
            else:
                task.callback()
            
            logger.info(f"Scheduled task completed: {task.name}")
        except Exception as e:
            logger.error(f"Scheduled task failed: {task.name} - {e}")
        
        # Schedule next run
        task.next_run = self._calculate_next_run(task.cron_expression)
        logger.info(f"Next run for {task.name}: {task.next_run}")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Task scheduler started")
        
        while self._running:
            now = datetime.now()
            
            # Check each task
            for task in self.tasks:
                if self._should_run(task, now):
                    # Run in background to not block other tasks
                    asyncio.create_task(self._run_task(task))
            
            # Wait before next check
            await asyncio.sleep(self.check_interval)
        
        logger.info("Task scheduler stopped")
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._scheduler_loop())
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._task:
            self._task.cancel()
    
    def get_status(self) -> List[dict]:
        """Get status of all scheduled tasks."""
        return [
            {
                "name": t.name,
                "enabled": t.enabled,
                "cron": t.cron_expression,
                "last_run": t.last_run.isoformat() if t.last_run else None,
                "next_run": t.next_run.isoformat() if t.next_run else None
            }
            for t in self.tasks
        ]


# Global scheduler instance
_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """Get or create global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


# ============================================
# Scheduled Tasks
# ============================================

def scheduled_backup_task():
    """Create automated database backup."""
    if not settings.BACKUP_ENABLED:
        logger.info("Automated backups disabled, skipping")
        return
    
    try:
        backup_service = get_backup_service()
        
        logger.info("Starting scheduled database backup")
        metadata = backup_service.create_backup(
            backup_type=BackupType.FULL,
            compress=settings.BACKUP_COMPRESS
        )
        
        logger.info(f"Scheduled backup completed: {metadata.id}")
        
        # Verify if configured
        if settings.BACKUP_VERIFY_AFTER_CREATE:
            is_valid = backup_service.verify_backup(metadata.id)
            if is_valid:
                logger.info(f"Backup {metadata.id} verified successfully")
            else:
                logger.error(f"Backup {metadata.id} verification failed")
        
        # Cleanup old backups
        deleted = backup_service.cleanup_old_backups()
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backups")
    
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")


def scheduled_cleanup_task():
    """Run periodic cleanup tasks."""
    try:
        backup_service = get_backup_service()
        deleted = backup_service.cleanup_old_backups()
        logger.info(f"Cleanup task completed. Removed {deleted} old backups")
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")


def init_scheduler():
    """Initialize scheduler with default tasks."""
    scheduler = get_scheduler()
    
    # Add automated backup task
    if settings.BACKUP_ENABLED:
        scheduler.add_task(
            name="automated_backup",
            cron_expression=settings.BACKUP_SCHEDULE,
            callback=scheduled_backup_task
        )
        logger.info(f"Automated backup scheduled: {settings.BACKUP_SCHEDULE}")
    
    # Add daily cleanup task
    scheduler.add_task(
        name="daily_cleanup",
        cron_expression="0 3 * * *",  # 3 AM daily
        callback=scheduled_cleanup_task
    )
    
    # Start the scheduler
    scheduler.start()
    
    return scheduler


def shutdown_scheduler():
    """Shutdown the scheduler gracefully."""
    scheduler = get_scheduler()
    scheduler.stop()
    logger.info("Scheduler shutdown complete")
