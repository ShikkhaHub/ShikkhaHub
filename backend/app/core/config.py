from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShikkhaHub API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Bangladesh Education Information Platform API"
    
    # Database (defaults to SQLite for local dev, override with env for production)
    DATABASE_URL: str = "sqlite:///./shikkhahub.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Redis Cache
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_EXPIRE: int = 3600  # 1 hour
    
    # Elasticsearch
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_ENABLED: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # AI/LLM
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    AI_ASSISTANT_ENABLED: bool = True
    
    # Monitoring & Error Tracking
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    ENABLE_PERFORMANCE_MONITORING: bool = True
    METRICS_RETENTION_MINUTES: int = 60
    
    # Data Quality
    DATA_FRESHNESS_DAYS: int = 90  # Alert if data older than this
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.85  # For duplicate detection
    
    # Backup & Recovery
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM (cron format)
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_LOCAL_PATH: str = "./backups"
    BACKUP_METADATA_PATH: str = "./backups/metadata"
    BACKUP_S3_BUCKET: Optional[str] = None  # For S3 storage backend
    BACKUP_S3_REGION: str = "us-east-1"
    BACKUP_VERIFY_AFTER_CREATE: bool = True
    BACKUP_COMPRESS: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
