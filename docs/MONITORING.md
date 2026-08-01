# Production Monitoring & Observability Setup

## Overview

Complete monitoring infrastructure for ShikkhaHub including error tracking, performance monitoring, analytics, and alerting.

## Components

1. **Error Tracking**: Sentry for exception monitoring
2. **Performance Monitoring**: Vercel Analytics + Custom metrics
3. **Logging**: Structured logging (Winston/Python logging)
4. **Analytics**: Google Analytics 4 + Mixpanel
5. **Uptime Monitoring**: Uptime Robot
6. **Database Monitoring**: Query performance, connection pooling
7. **Real User Monitoring**: Core Web Vitals

---

## 1. Sentry Setup (Error Tracking)

### Installation

**Backend (Python)**:
```bash
pip install sentry-sdk
```

**Frontend (React/Vite)**:
```bash
npm install @sentry/react @sentry/vite-plugin
```

**Mobile (React Native)**:
```bash
npm install @sentry/react-native
```

### Backend Configuration

```python
# backend/app/core/config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions
        profiles_sample_rate=0.1,  # 10% of profiling
        environment="production",
        before_send=before_send_sentry,
    )

def before_send_sentry(event, hint):
    """Filter and enrich Sentry events"""
    # Ignore certain errors
    if hint.get("exc_info"):
        exc_type, exc_value, tb = hint["exc_info"]
        if isinstance(exc_value, (HTTPException,)):
            return None
    
    # Add custom context
    event["tags"]["service"] = "shikkhahub-backend"
    
    return event
```

### Frontend Configuration

```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";
import { BrowserTracing } from "@sentry/tracing";

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    integrations: [
      new BrowserTracing({
        routingInstrumentation: Sentry.reactRouterV6Instrumentation(
          useEffect,
          useLocation,
          useNavigationType,
          createRoutesFromChildren,
          matchRoutes
        ),
      }),
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    environment: "production",
  });
}
```

### Mobile Configuration

```typescript
// mobile/App.tsx
import * as Sentry from "@sentry/react-native";

const SENTRY_DSN = Constants.expoConfig?.extra?.sentryDSN;

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    tracesSampleRate: 0.1,
    enableAutoPerformanceTracing: true,
    environment: "production",
  });
}
```

### Sentry Dashboard

**Key Metrics to Monitor**:
- Error frequency and trends
- Most impactful errors (by affected users)
- Performance regressions
- Release health
- User sessions

**Alerts to Set**:
- 5+ errors in 5 minutes
- Error rate > 1%
- New error type
- Performance degradation > 20%

---

## 2. Vercel Analytics

### Setup

**Frontend** - Already included in Vercel deployments:
```typescript
// auto-included via @vercel/analytics/react
import { Analytics } from "@vercel/analytics/react";

export default function App() {
  return (
    <>
      <YourApp />
      <Analytics />
    </>
  );
}
```

**Track Custom Events**:
```typescript
import { track } from "@vercel/analytics";

// Track institution search
track("search_institution", {
  query: searchTerm,
  result_count: results.length,
});

// Track app installation
track("app_installed", {
  platform: "ios" | "android",
  version: APP_VERSION,
});
```

### Backend Monitoring

```python
# backend/app/core/analytics.py
from vercel_analytics import Client

analytics_client = Client(
    token=os.getenv("VERCEL_ANALYTICS_TOKEN")
)

async def track_event(name: str, properties: dict):
    """Track custom event in Vercel Analytics"""
    await analytics_client.track(
        event=name,
        properties={
            "service": "backend",
            "timestamp": datetime.utcnow().isoformat(),
            **properties,
        }
    )
```

---

## 3. Structured Logging

### Backend Logging Setup

```python
# backend/app/core/logging.py
import logging
import json
from datetime import datetime

class JsonFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "shikkhahub-backend",
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(handler)

# In API endpoints
logger.info("institution_search", extra={
    "query": search_query,
    "duration_ms": duration,
    "result_count": len(results),
})
```

### Frontend Logging Setup

```typescript
// frontend/src/utils/logging.ts
export class Logger {
  static info(message: string, data?: Record<string, unknown>) {
    console.log(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: "INFO",
      message,
      ...data,
    }));
  }

  static error(message: string, error?: Error, data?: Record<string, unknown>) {
    console.error(JSON.stringify({
      timestamp: new Date().toISOString(),
      level: "ERROR",
      message,
      error: error?.message,
      stack: error?.stack,
      ...data,
    }));
  }
}

// Usage
Logger.info("search_complete", {
  query: term,
  resultCount: results.length,
  durationMs: performance.now(),
});
```

---

## 4. Google Analytics 4

### Setup

**Frontend**:
```bash
npm install @react-google-analytics/core
```

```typescript
// frontend/src/main.tsx
import { GoogleAnalytics } from "@react-google-analytics/core";

const GA_ID = import.meta.env.VITE_GOOGLE_ANALYTICS_ID;

if (GA_ID) {
  ReactDOM.createRoot(document.getElementById("root")).render(
    <GoogleAnalytics measurementId={GA_ID}>
      <App />
    </GoogleAnalytics>
  );
}
```

### Custom Events

```typescript
// Track key user actions
import { useGoogleAnalytics } from "@react-google-analytics/core";

export function SearchComponent() {
  const { event } = useGoogleAnalytics();

  const handleSearch = (query: string, results: any[]) => {
    event("search", {
      search_term: query,
      result_count: results.length,
    });
  };

  const handleSaveInstitution = (institutionId: string) => {
    event("save_institution", {
      institution_id: institutionId,
    });
  };
}
```

**Backend - GA4 Measurement Protocol**:
```python
# backend/app/core/analytics.py
import httpx

class GA4Client:
    def __init__(self, measurement_id: str, api_secret: str):
        self.measurement_id = measurement_id
        self.api_secret = api_secret
        self.endpoint = "https://www.google-analytics.com/mp/collect"

    async def send_event(self, user_id: str, event_name: str, params: dict):
        """Send event to GA4"""
        payload = {
            "client_id": user_id,
            "events": [{
                "name": event_name,
                "params": params,
            }]
        }
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.endpoint}?measurement_id={self.measurement_id}&api_secret={self.api_secret}",
                json=payload,
            )
```

### Dashboard Setup

**Key Metrics**:
- Users and sessions
- Most viewed institutions
- Search queries
- Conversion funnel (search → save → review)
- Device breakdown (mobile vs web)
- Traffic sources

---

## 5. Real User Monitoring (RUM)

### Core Web Vitals

```typescript
// frontend/src/utils/vitals.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from "web-vitals";

export function initializeWebVitals() {
  getCLS(metric => track("cls", metric.value));
  getFID(metric => track("fid", metric.value));
  getFCP(metric => track("fcp", metric.value));
  getLCP(metric => track("lcp", metric.value));
  getTTFB(metric => track("ttfb", metric.value));
}

function track(name: string, value: number) {
  // Send to Sentry
  Sentry.captureMessage(`Web Vital: ${name}=${value}`, "info");
  
  // Send to Analytics
  analytics.track(`web_vital_${name}`, { value });
}
```

### API Response Time Monitoring

```python
# backend/app/middleware/metrics.py
from time import time
import logging

logger = logging.getLogger(__name__)

async def metrics_middleware(request, call_next):
    start = time()
    
    response = await call_next(request)
    
    duration = (time() - start) * 1000  # Convert to ms
    
    # Log slow requests
    if duration > 1000:  # > 1 second
        logger.warning("slow_request", extra={
            "endpoint": request.url.path,
            "method": request.method,
            "duration_ms": duration,
            "status_code": response.status_code,
        })
    
    # Add timing header
    response.headers["X-Response-Time"] = f"{duration}ms"
    
    return response
```

---

## 6. Database Monitoring

### Query Performance

```python
# backend/app/core/database.py
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time() - conn.info['query_start_time'].pop(-1)
    
    if total > 1:  # Log slow queries
        logger.warning("slow_query", extra={
            "query": statement,
            "duration_ms": total * 1000,
        })
```

### Connection Pool Monitoring

```python
# Monitor connection pool
pool = engine.pool

logger.info("db_pool_status", extra={
    "size": pool.size(),
    "checked_in": pool.checkedin(),
    "checked_out": pool.checkedout(),
})
```

---

## 7. Uptime Monitoring

### Using Uptime Robot

**Endpoints to Monitor**:
1. Frontend: `https://shikkhahub.edu.bd/` - Check for 200 status
2. Backend Health: `https://api.shikkhahub.edu.bd/health` - Check for 200 status
3. API: `https://api.shikkhahub.edu.bd/api/v1/institutions` - Check response time

**Alert Configuration**:
- Down time alert
- SSL certificate expiration
- Response time > 2 seconds
- Check interval: 5 minutes

---

## 8. Production Dashboard

### Real-Time Alerts

**Critical Alerts** (Immediate):
- 5+ errors in 5 minutes
- Backend response time > 5 seconds
- Database connection errors
- API rate limiting triggered
- SSL certificate expiring < 7 days

**Warning Alerts** (Daily):
- Error rate > 0.1%
- p95 response time > 2 seconds
- Database queries > 1 second
- Search results < 100ms p50

**Channels**:
- Slack for team notifications
- Email for critical issues
- PagerDuty for on-call escalation

### Slack Integration

```python
# backend/app/core/alerts.py
import httpx

SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

async def send_alert(severity: str, title: str, message: str):
    """Send alert to Slack"""
    color_map = {
        "critical": "danger",
        "warning": "warning",
        "info": "good",
    }
    
    payload = {
        "attachments": [{
            "color": color_map.get(severity, "good"),
            "title": title,
            "text": message,
            "ts": int(time()),
        }]
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK, json=payload)
```

---

## 9. Environment Variables

```env
# Error Tracking
SENTRY_DSN=https://key@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Analytics
VITE_GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
VERCEL_ANALYTICS_TOKEN=token

# Monitoring
UPTIME_ROBOT_KEY=api_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
PAGERDUTY_INTEGRATION_KEY=integration_key

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## 10. Health Check Endpoint

```python
# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
import httpx

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    Returns status of all critical services
    """
    checks = {
        "status": "healthy",
        "services": {},
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        checks["services"]["database"] = "up"
    except Exception as e:
        checks["services"]["database"] = f"down: {str(e)}"
        checks["status"] = "degraded"
    
    # Check external services (optional)
    try:
        async with httpx.AsyncClient() as client:
            await client.get("https://api.openai.com/v1/models", timeout=5)
        checks["services"]["openai"] = "up"
    except:
        checks["services"]["openai"] = "down"
        checks["status"] = "degraded"
    
    return checks
```

---

## Metrics Dashboard Template

### Key Metrics to Track

| Metric | Target | Alert Level |
|--------|--------|------------|
| API Response Time (p95) | <500ms | >2s |
| Error Rate | <0.1% | >1% |
| Uptime | 99.5% | <99% |
| Search Latency (p95) | <200ms | >500ms |
| Database Connections | <80% pool | >90% |
| Page Load Time (LCP) | <2.5s | >4s |

---

## Runbook: Common Issues

### High Error Rate
1. Check Sentry for error patterns
2. Review recent deployments
3. Check database connection pool
4. Scale backend if CPU high

### Slow Response Times
1. Check database query logs
2. Review slow query log
3. Check cache hit rates
4. Monitor network latency

### Database Issues
1. Check connection pool status
2. Review slow query log
3. Check disk usage
4. Monitor table sizes

---

## Next Steps

1. Set up Sentry project and connect environment
2. Configure GA4 and create events
3. Set up Uptime Robot checks
4. Create Slack alerts
5. Deploy and monitor
6. Iterate based on data

---

**Last Updated**: 2024
**Owner**: DevOps Team
**Review Frequency**: Monthly
