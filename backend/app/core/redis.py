"""Redis caching layer for ShikkhaHub."""
import json
import pickle
from typing import Optional, Any, Callable
from functools import wraps
import redis
from app.core.config import settings

# Redis client instance
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 0),
                password=getattr(settings, 'REDIS_PASSWORD', None),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            # Test connection
            redis_client.ping()
        except (redis.ConnectionError, redis.ResponseError) as e:
            print(f"Redis connection failed: {e}")
            redis_client = None
    return redis_client

def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        data = client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None

def cache_set(key: str, value: Any, expire: int = 3600) -> bool:
    """Set value in cache with expiration (default 1 hour)."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.setex(key, expire, json.dumps(value, default=str))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False

def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False

def cache_clear_pattern(pattern: str) -> bool:
    """Clear all keys matching pattern."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
        return True
    except Exception as e:
        print(f"Cache clear error: {e}")
        return False

def cached(key_prefix: str, expire: int = 3600):
    """Decorator to cache function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_set(cache_key, result, expire)
            return result
        return wrapper
    return decorator

# Cache key generators
def get_divisions_cache_key() -> str:
    return "shikkhahub:divisions"

def get_institution_list_cache_key(page: int, page_size: int, **filters) -> str:
    filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
    return f"shikkhahub:institutions:list:{page}:{page_size}:{filter_str}"

def get_institution_detail_cache_key(slug: str) -> str:
    return f"shikkhahub:institutions:detail:{slug}"

def get_search_cache_key(query: str, **filters) -> str:
    filter_str = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
    return f"shikkhahub:search:{query}:{filter_str}"
