from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import (
    SecurityHeadersMiddleware,
    LoggingMiddleware,
    RequestSizeLimitMiddleware,
    PerformanceMonitoringMiddleware
)
from app.core.rate_limit import limiter, setup_rate_limiting
from app.core.monitoring import HealthChecker, metrics_collector
from app.core.scheduler import init_scheduler, shutdown_scheduler
from app.api.v1 import api_router
import time
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
import asyncio
import contextlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    """Application factory pattern."""
    # Initialize Sentry if DSN is configured
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
            ],
        )
        logger.info(f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}")
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )
    
    # Performance monitoring middleware (first to capture everything)
    if settings.ENABLE_PERFORMANCE_MONITORING:
        app.add_middleware(PerformanceMonitoringMiddleware)
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Request size limit middleware (10MB)
    app.add_middleware(RequestSizeLimitMiddleware, max_size=10 * 1024 * 1024)
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup rate limiting
    setup_rate_limiting(app)
    
    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Include routers
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check - basic
    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "healthy", "version": settings.VERSION}
    
    # Detailed health check with dependency status
    @app.get("/health/detailed", tags=["health"])
    def health_check_detailed():
        checks = HealthChecker.get_all_checks()
        
        # Determine overall status
        all_healthy = all(
            check.get('status') in ['healthy', 'green', 'yellow']
            for check in checks.values()
            if isinstance(check, dict) and 'status' in check
        )
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "checks": checks
        }
    
    # Application metrics endpoint
    @app.get("/metrics", tags=["monitoring"])
    def get_metrics():
        return metrics_collector.get_all_metrics()
    
    @app.get("/", tags=["root"])
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "description": settings.DESCRIPTION,
            "docs": "/docs"
        }
    
    return app

app = create_application()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up ShikkhaHub API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise - let the app start for health checks
    
    # Initialize background task scheduler
    try:
        init_scheduler()
        logger.info("Background task scheduler initialized")
    except Exception as e:
        logger.error(f"Scheduler initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ShikkhaHub API...")
    try:
        shutdown_scheduler()
        logger.info("Background tasks stopped")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
