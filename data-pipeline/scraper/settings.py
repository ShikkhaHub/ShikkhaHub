"""
Scrapy settings for ShikkhaHub Data Pipeline
"""

import os
from datetime import datetime

# Project name
BOT_NAME = 'shikkhahub_scraper'
PROJECT_NAME = 'ShikkhaHub Data Pipeline'

# Logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
LOG_FILE = f'logs/scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

# Crawl settings
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1  # Respectful crawling
COOKIES_ENABLED = True
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'User-Agent': 'ShikkhaHub Data Collector (Bangladesh Education Platform) +https://shikkhahub.com',
}

# Retry configuration
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Timeout
DOWNLOAD_TIMEOUT = 30
DUPEFILTER_ENABLED = True
DUPEFILTER_CLASS = 'scrapy.dupefilters.BaseDupeFilter'

# Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}

# Pipeline
ITEM_PIPELINES = {
    'data_pipeline.scraper.pipelines.ValidationPipeline': 100,
    'data_pipeline.scraper.pipelines.DeduplicationPipeline': 200,
    'data_pipeline.scraper.pipelines.DatabasePipeline': 300,
}

# Data sources configuration
DATA_SOURCES = {
    'dhaka_board': {
        'name': 'Dhaka Education Board',
        'tier': 1,
        'trust_score': 0.95,
        'url': 'https://dhakaeducationboard.gov.bd',
        'type': 'government',
    },
    'ctg_board': {
        'name': 'Chittagong Education Board',
        'tier': 1,
        'trust_score': 0.95,
        'url': 'https://chittagong.gov.bd',
        'type': 'government',
    },
    'bteb': {
        'name': 'Bangladesh Technical Education Board',
        'tier': 1,
        'trust_score': 0.95,
        'url': 'https://bteb.gov.bd',
        'type': 'government',
    },
    'ugc': {
        'name': 'University Grants Commission',
        'tier': 1,
        'trust_score': 0.95,
        'url': 'https://ugc.gov.bd',
        'type': 'government',
    },
}

# Request headers for different data sources
REQUEST_HEADERS_BY_SOURCE = {
    'government': {
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'bn-BD,bn;q=0.9,en;q=0.8',
    },
}

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/shikkhahub')

# Redis settings (for Celery)
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Storage settings
RAW_DATA_STORAGE = 'database'  # 'database' or 's3'
S3_BUCKET = os.getenv('S3_BUCKET', 'shikkhahub-raw-data')

# Scraping strategy
SCRAPING_STRATEGY = {
    'tier_1_only_first': True,  # Start with tier 1 sources only
    'verify_before_index': True,  # Don't index unverified data
    'daily_update': True,  # Update critical fields daily
    'weekly_refresh': True,  # Full refresh weekly
}

# API settings for external data sources
API_RATE_LIMIT = 100  # requests per minute
BATCH_SIZE = 1000  # Process in batches of 1000

# Performance
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_TIMEOUT = 30

# Feed exports (optional, for testing)
FEEDS = {
    'output/institutions_%(time)s.json': {
        'format': 'json',
    },
}
