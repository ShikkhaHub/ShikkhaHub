"""Security and monitoring middleware for FastAPI."""
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging

from app.core.monitoring import metrics_collector, RequestMetric
from datetime import datetime

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (adjust as needed)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Log request
        print(f"[{request.method}] {request.url.path} - Started")
        
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        print(f"[{request.method}] {request.url.path} - {response.status_code} - {duration:.3f}s")
        
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                if size > self.max_size:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request body too large. Max size: {self.max_size} bytes"
                    )
        
        return await call_next(request)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Track detailed performance metrics for all requests."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        error = None
        status_code = 200
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error = str(e)
            status_code = 500
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Skip health checks and docs from metrics
            path = request.url.path
            if not any(skip in path for skip in ['/health', '/docs', '/openapi.json', '/metrics']):
                metric = RequestMetric(
                    method=request.method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow(),
                    user_agent=request.headers.get('user-agent'),
                    error=error
                )
                metrics_collector.record_request(metric)
                
                # Log slow requests
                if duration_ms > 1000:
                    logger.warning(f"Slow request: {request.method} {path} took {duration_ms:.2f}ms")


def setup_cors(app, allowed_origins: list = None):
    """Setup CORS middleware."""
    if allowed_origins is None:
        allowed_origins = [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",    # Alternative dev server
            "http://localhost:4173",    # Vite preview
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"]
    )
