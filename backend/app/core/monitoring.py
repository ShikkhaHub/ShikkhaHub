"""Monitoring and metrics collection for ShikkhaHub.

This module provides:
- Performance metrics collection
- Application health monitoring
- Error tracking integration
- Request/response metrics
"""
import time
import logging
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import psutil
import os

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class RequestMetric:
    """Metrics for a single request."""
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    user_agent: Optional[str] = None
    error: Optional[str] = None


class MetricsCollector:
    """Collect and store application metrics."""
    
    def __init__(self, max_requests: int = 10000):
        self.max_requests = max_requests
        self.request_metrics: List[RequestMetric] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'error_count': 0,
            'status_codes': defaultdict(int)
        })
        self._start_time = datetime.utcnow()
        
    def record_request(self, metric: RequestMetric):
        """Record a request metric."""
        self.request_metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.request_metrics) > self.max_requests:
            self.request_metrics = self.request_metrics[-self.max_requests:]
        
        # Update endpoint stats
        endpoint_key = f"{metric.method} {metric.path}"
        stats = self.endpoint_stats[endpoint_key]
        stats['count'] += 1
        stats['total_duration'] += metric.duration_ms
        stats['status_codes'][metric.status_code] += 1
        
        if metric.error:
            stats['error_count'] += 1
            self.error_counts[metric.error] += 1
    
    def get_request_rate(self, window_minutes: int = 5) -> float:
        """Get requests per minute for the last window."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [m for m in self.request_metrics if m.timestamp > cutoff]
        return len(recent) / window_minutes if window_minutes > 0 else 0
    
    def get_average_response_time(self, window_minutes: int = 5) -> float:
        """Get average response time for the last window."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [m for m in self.request_metrics if m.timestamp > cutoff]
        if not recent:
            return 0.0
        return sum(m.duration_ms for m in recent) / len(recent)
    
    def get_error_rate(self, window_minutes: int = 5) -> float:
        """Get error rate for the last window."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [m for m in self.request_metrics if m.timestamp > cutoff]
        if not recent:
            return 0.0
        errors = [m for m in recent if m.error or m.status_code >= 500]
        return len(errors) / len(recent) * 100
    
    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest endpoints by average response time."""
        results = []
        for endpoint, stats in self.endpoint_stats.items():
            if stats['count'] > 0:
                avg_duration = stats['total_duration'] / stats['count']
                results.append({
                    'endpoint': endpoint,
                    'avg_duration_ms': avg_duration,
                    'request_count': stats['count'],
                    'error_count': stats['error_count'],
                    'error_rate': stats['error_count'] / stats['count'] * 100
                })
        
        results.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
        return results[:limit]
    
    def get_error_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get summary of most common errors."""
        errors = [
            {'error_type': error, 'count': count}
            for error, count in self.error_counts.items()
        ]
        errors.sort(key=lambda x: x['count'], reverse=True)
        return errors[:limit]
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds."""
        return (datetime.utcnow() - self._start_time).total_seconds()
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        return {
            'uptime_seconds': self.get_uptime_seconds(),
            'request_rate_5m': self.get_request_rate(5),
            'request_rate_1h': self.get_request_rate(60),
            'avg_response_time_ms': self.get_average_response_time(5),
            'error_rate_5m': self.get_error_rate(5),
            'total_requests': len(self.request_metrics),
            'slowest_endpoints': self.get_slowest_endpoints(10),
            'top_errors': self.get_error_summary(10),
            'system': SystemMetrics.get_metrics()
        }


class SystemMetrics:
    """System-level metrics collector."""
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            # Memory
            memory = psutil.virtual_memory()
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            
            # Disk
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            return {
                'memory': {
                    'total_mb': memory.total / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'used_percent': memory.percent,
                    'process_mb': process_memory
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'used_percent': disk.percent
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {'error': str(e)}


# Global metrics collector instance
metrics_collector = MetricsCollector()


def timed(func: Callable) -> Callable:
    """Decorator to time function execution and record metrics."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start) * 1000
            logger.debug(f"{func.__name__} completed in {duration:.2f}ms")
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(f"{func.__name__} failed after {duration:.2f}ms: {e}")
            raise
    return wrapper


def record_error(error_type: str, message: str, extra: Optional[Dict] = None):
    """Record an error for monitoring."""
    metrics_collector.error_counts[error_type] += 1
    logger.error(f"[{error_type}] {message}", extra=extra or {})


class HealthChecker:
    """System health check utilities."""
    
    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database connectivity."""
        from app.core.database import engine
        try:
            start = time.time()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            duration = (time.time() - start) * 1000
            return {
                'status': 'healthy',
                'response_time_ms': duration
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity."""
        from app.core.redis import redis_client
        try:
            start = time.time()
            redis_client.ping()
            duration = (time.time() - start) * 1000
            return {
                'status': 'healthy',
                'response_time_ms': duration
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def check_elasticsearch() -> Dict[str, Any]:
        """Check Elasticsearch connectivity."""
        from app.core.elasticsearch import es_client
        try:
            start = time.time()
            health = es_client.cluster.health()
            duration = (time.time() - start) * 1000
            return {
                'status': health.get('status', 'unknown'),
                'response_time_ms': duration,
                'cluster_name': health.get('cluster_name')
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def get_all_checks() -> Dict[str, Any]:
        """Run all health checks."""
        return {
            'database': HealthChecker.check_database(),
            'redis': HealthChecker.check_redis(),
            'elasticsearch': HealthChecker.check_elasticsearch(),
            'timestamp': datetime.utcnow().isoformat()
        }
