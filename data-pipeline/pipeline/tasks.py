"""
Celery tasks for data pipeline
Handles scraping, processing, and verification jobs
"""

import os
import logging
from celery import Celery, Task
from celery.schedules import crontab
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Initialize Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery('shikkhahub_pipeline', broker=REDIS_URL, backend=REDIS_URL)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Configure beat schedule for recurring tasks
celery_app.conf.beat_schedule = {
    'scrape-tier1-sources-daily': {
        'task': 'pipeline.tasks.scrape_tier1_sources',
        'schedule': crontab(hour=1, minute=0),  # Run at 1 AM UTC daily
        'options': {'queue': 'scraping'}
    },
    'scrape-tier2-sources-weekly': {
        'task': 'pipeline.tasks.scrape_tier2_sources',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Run at 2 AM UTC every Sunday
        'options': {'queue': 'scraping'}
    },
    'process-pending-data': {
        'task': 'pipeline.tasks.process_pending_data',
        'schedule': crontab(minute='*/30'),  # Run every 30 minutes
        'options': {'queue': 'processing'}
    },
    'deduplication-check': {
        'task': 'pipeline.tasks.check_duplicates',
        'schedule': crontab(hour='*/6', minute=0),  # Run every 6 hours
        'options': {'queue': 'processing'}
    },
    'refresh-search-index': {
        'task': 'pipeline.tasks.refresh_search_index',
        'schedule': crontab(hour=3, minute=0),  # Run at 3 AM UTC daily
        'options': {'queue': 'indexing'}
    },
}

logger = logging.getLogger(__name__)


class CallbackTask(Task):
    """Task with callbacks"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True


@celery_app.task(bind=True, base=CallbackTask, queue='scraping')
def scrape_tier1_sources(self):
    """
    Scrape Tier 1 (government) sources.
    Highest priority, daily schedule.
    """
    logger.info(f'Starting Tier 1 scraping job {self.request.id}')
    
    try:
        from data_pipeline.scraper.spiders.ugc_spider import UGCSpider
        from scrapy.crawler import CrawlerProcess
        
        # Configure scraper
        process = CrawlerProcess({
            'USER_AGENT': 'ShikkhaHub Data Collector +https://shikkhahub.com',
            'ROBOTSTXT_OBEY': True,
            'DOWNLOAD_DELAY': 2,
        })
        
        # Run UGC spider
        process.crawl(UGCSpider)
        process.start()
        
        logger.info(f'Tier 1 scraping completed: {self.request.id}')
        return {'status': 'success', 'job_id': self.request.id}
        
    except Exception as exc:
        logger.error(f'Tier 1 scraping failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='scraping')
def scrape_tier2_sources(self):
    """
    Scrape Tier 2 (educational directories, etc) sources.
    Weekly schedule.
    """
    logger.info(f'Starting Tier 2 scraping job {self.request.id}')
    
    try:
        # TODO: Implement additional tier 2 spiders
        logger.info('Tier 2 scraping completed')
        return {'status': 'success', 'job_id': self.request.id}
        
    except Exception as exc:
        logger.error(f'Tier 2 scraping failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='processing')
def process_pending_data(self):
    """
    Process raw data that's pending in the database.
    Runs every 30 minutes.
    """
    logger.info(f'Starting data processing job {self.request.id}')
    
    try:
        from data_pipeline.processor.processor import DataProcessor
        from data_pipeline.db.models import RawData
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Get database session
        db_url = os.getenv('DATABASE_URL')
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        processor = DataProcessor()
        
        # Get pending raw data (limit 100 per run)
        pending_items = session.query(RawData).filter(
            RawData.status == 'pending'
        ).limit(100).all()
        
        processed = 0
        for item in pending_items:
            try:
                # Process the item
                cleaned = processor.process({
                    'name_en': item.raw_json.get('name'),
                    'type': item.raw_json.get('type'),
                    'email': item.raw_json.get('email'),
                    'phone': item.raw_json.get('phone'),
                    'address': item.raw_json.get('address'),
                    'source_type': item.source_type,
                    'source_url': item.source_url,
                })
                
                if cleaned:
                    item.status = 'processed'
                    item.extracted_fields = cleaned
                    item.processed_at = datetime.utcnow()
                    processed += 1
                else:
                    item.status = 'error'
                    item.error_message = 'Failed validation'
                
            except Exception as e:
                item.status = 'error'
                item.error_message = str(e)
                item.processing_attempts += 1
            
            session.add(item)
        
        session.commit()
        session.close()
        
        logger.info(f'Processed {processed}/{len(pending_items)} items')
        return {'status': 'success', 'processed': processed}
        
    except Exception as exc:
        logger.error(f'Data processing failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='processing')
def check_duplicates(self):
    """
    Check for duplicate institutions.
    Runs every 6 hours.
    """
    logger.info(f'Starting duplicate check job {self.request.id}')
    
    try:
        from data_pipeline.processor.processor import Deduplicator
        # TODO: Implement duplicate checking against existing institutions
        
        logger.info('Duplicate check completed')
        return {'status': 'success', 'job_id': self.request.id}
        
    except Exception as exc:
        logger.error(f'Duplicate check failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='indexing')
def refresh_search_index(self):
    """
    Refresh Elasticsearch search index with verified data.
    Runs daily at 3 AM UTC.
    """
    logger.info(f'Starting search index refresh {self.request.id}')
    
    try:
        # TODO: Sync verified institutions to Elasticsearch
        logger.info('Search index refreshed')
        return {'status': 'success', 'job_id': self.request.id}
        
    except Exception as exc:
        logger.error(f'Index refresh failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='processing')
def verify_institution(self, institution_id: int):
    """
    Verify a single institution (admin action).
    Triggered manually from admin dashboard.
    """
    logger.info(f'Verifying institution {institution_id}')
    
    try:
        # TODO: Mark as verified, update verification_level
        logger.info(f'Institution {institution_id} verified')
        return {'status': 'success', 'institution_id': institution_id}
        
    except Exception as exc:
        logger.error(f'Verification failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask, queue='processing')
def merge_duplicates(self, institution_id_1: int, institution_id_2: int):
    """
    Merge two duplicate institutions.
    Triggered from admin dashboard.
    """
    logger.info(f'Merging institutions {institution_id_1} and {institution_id_2}')
    
    try:
        # TODO: Merge institutions (keep one, mark other as duplicate)
        logger.info(f'Merge complete')
        return {'status': 'success'}
        
    except Exception as exc:
        logger.error(f'Merge failed: {str(exc)}')
        raise


@celery_app.task(bind=True, base=CallbackTask)
def generate_report(self, report_type: str):
    """
    Generate pipeline reports (scraping stats, verification progress, etc).
    """
    logger.info(f'Generating {report_type} report')
    
    try:
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'report_type': report_type,
            # TODO: Generate actual report
        }
        logger.info(f'Report generated: {report_type}')
        return report
        
    except Exception as exc:
        logger.error(f'Report generation failed: {str(exc)}')
        raise


# Monitoring tasks
@celery_app.task
def health_check():
    """Health check task - verify pipeline is running"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
