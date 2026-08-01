"""Rate limiting configuration for FastAPI."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Request, FastAPI
from app.core.redis import get_redis_client


def get_remote_address(request: Request) -> str:
    """Extract a stable client identifier.

    Behind proxies (e.g. Vercel) `request.client` may be missing, so prefer
    forwarded headers and fall back to a local value rather than crashing.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


# Create limiter with Redis storage if available, otherwise in-memory
def get_limiter() -> Limiter:
    """Create and configure rate limiter."""
    try:
        # Try to use Redis for distributed rate limiting
        redis_client = get_redis_client()
        if redis_client:
            # Use Redis storage for rate limiting
            return Limiter(
                key_func=get_remote_address,
                storage_uri=f"redis://{redis_client.connection_pool.connection_kwargs.get('host', 'localhost')}:{redis_client.connection_pool.connection_kwargs.get('port', 6379)}/1"
            )
    except Exception:
        pass

    # Fallback to in-memory storage
    return Limiter(key_func=get_remote_address)


# Create global limiter instance
limiter = get_limiter()


def setup_rate_limiting(app: FastAPI) -> None:
    """Setup rate limiting for FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Rate limit decorators for common use cases
def auth_limit():
    """Strict rate limit for authentication endpoints."""
    return limiter.limit("5 per minute")


def standard_limit():
    """Standard rate limit for most endpoints."""
    return limiter.limit("100 per minute")


def search_limit():
    """Rate limit for search endpoints (higher limit)."""
    return limiter.limit("200 per minute")


def admin_limit():
    """Rate limit for admin endpoints."""
    return limiter.limit("300 per minute")


def public_limit():
    """Rate limit for public/read-only endpoints."""
    return limiter.limit("150 per minute")
