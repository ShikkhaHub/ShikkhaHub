"""Analytics API endpoints for tracking and reporting."""
from fastapi import APIRouter, Depends, Query, Request, HTTPException, Header, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_admin_user
from app.models.user import User
from app.services.analytics import (
    AnalyticsTracker, AnalyticsAggregator, AnalyticsDashboard,
    SearchMetrics, PageViewMetrics, EngagementMetrics
)

router = APIRouter()


# Request/Response schemas
class TrackSearchRequest(BaseModel):
    query: str
    results_count: int = 0
    filters: Optional[Dict[str, Any]] = None
    search_duration_ms: Optional[float] = None


class TrackClickRequest(BaseModel):
    event_type: str
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    institution_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class TrackPageViewRequest(BaseModel):
    path: str
    institution_id: Optional[int] = None
    referrer: Optional[str] = None
    time_on_page_seconds: Optional[int] = None
    scroll_depth_percent: Optional[int] = None


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_session_id(request: Request) -> str:
    """Get or generate session ID."""
    # Try to get from header or cookie
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        # Generate from IP + User-Agent hash
        import hashlib
        data = f"{get_client_ip(request)}:{request.headers.get('user-agent', '')}"
        session_id = hashlib.md5(data.encode()).hexdigest()[:16]
    return session_id


# ============================================
# TRACKING ENDPOINTS
# ============================================

@router.post("/track/search")
async def track_search(
    data: TrackSearchRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    user_agent: Optional[str] = Header(None)
):
    """
    Track a search query.
    
    Records:
    - Search query text
    - Number of results
    - Filters applied
    - Response time
    - User/session info
    """
    try:
        event = AnalyticsTracker.track_search(
            db=db,
            query=data.query,
            results_count=data.results_count,
            user_id=current_user.id if current_user else None,
            session_id=get_session_id(request),
            filters=data.filters,
            search_duration_ms=data.search_duration_ms,
            user_agent=user_agent,
            ip_address=get_client_ip(request),
            referrer=request.headers.get("referer")
        )
        
        return {
            "success": True,
            "search_event_id": event.id
        }
    except Exception as e:
        # Silently fail for analytics to not block user experience
        return {"success": False, "error": str(e)}


@router.post("/track/pageview")
async def track_page_view(
    data: TrackPageViewRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    user_agent: Optional[str] = Header(None)
):
    """
    Track a page view.
    
    Records:
    - Page path
    - Institution viewed (if applicable)
    - Referrer
    - Device type
    - User/session info
    """
    try:
        view = AnalyticsTracker.track_page_view(
            db=db,
            path=data.path,
            user_id=current_user.id if current_user else None,
            session_id=get_session_id(request),
            institution_id=data.institution_id,
            referrer=data.referrer or request.headers.get("referer"),
            user_agent=user_agent,
            ip_address=get_client_ip(request)
        )
        
        return {
            "success": True,
            "page_view_id": view.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/track/click")
async def track_click(
    data: TrackClickRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Track a click event.
    
    Records:
    - Event type (compare, contact, share, favorite)
    - Element clicked
    - Institution context
    - Metadata
    """
    try:
        event = AnalyticsTracker.track_click(
            db=db,
            event_type=data.event_type,
            page_path=str(request.headers.get("referer", "")),
            element_id=data.element_id,
            element_text=data.element_text,
            institution_id=data.institution_id,
            user_id=current_user.id if current_user else None,
            session_id=get_session_id(request),
            metadata=data.metadata
        )
        
        return {
            "success": True,
            "click_event_id": event.id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/track/search-click")
async def track_search_click(
    search_event_id: int,
    institution_id: int,
    db: Session = Depends(get_db)
):
    """
    Update a search event when user clicks a result.
    
    Used to calculate click-through rates.
    """
    try:
        AnalyticsTracker.update_search_click(db, search_event_id, institution_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# DASHBOARD & REPORTING ENDPOINTS (Admin)
# ============================================

@router.get("/dashboard")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get analytics dashboard data (Admin only).
    
    Returns comprehensive overview including:
    - Today's metrics with day-over-day comparison
    - Last 30 days search and engagement metrics
    - Trending searches
    - Content gaps (no-result searches)
    """
    return AnalyticsDashboard.get_overview(db)


@router.get("/searches/metrics")
def get_search_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get search analytics metrics.
    
    - Total searches
    - Unique queries
    - Click-through rate
    - No-result rate
    - Top queries
    - Trending queries
    """
    metrics = AnalyticsAggregator.get_search_metrics(db, days=days)
    return {
        "period_days": days,
        "total_searches": metrics.total_searches,
        "unique_queries": metrics.unique_queries,
        "avg_results_count": metrics.avg_results_count,
        "click_through_rate": metrics.click_through_rate,
        "no_result_rate": metrics.no_result_rate,
        "top_queries": metrics.top_queries,
        "trending_queries": metrics.trending_queries
    }


@router.get("/pageviews/metrics")
def get_page_view_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get page view analytics metrics.
    
    - Total views
    - Unique visitors
    - Bounce rate
    - Top pages
    - Top institutions
    - Device breakdown
    """
    metrics = AnalyticsAggregator.get_page_view_metrics(db, days=days)
    return {
        "period_days": days,
        "total_views": metrics.total_views,
        "unique_visitors": metrics.unique_visitors,
        "avg_time_on_page": metrics.avg_time_on_page,
        "bounce_rate": metrics.bounce_rate,
        "top_pages": metrics.top_pages,
        "top_institutions": metrics.top_institutions,
        "device_breakdown": metrics.device_breakdown
    }


@router.get("/engagement/metrics")
def get_engagement_metrics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get user engagement metrics.
    
    - Total clicks
    - Button clicks (compare, contact, share, favorite)
    - Institution engagement rate
    """
    metrics = AnalyticsAggregator.get_engagement_metrics(db, days=days)
    return {
        "period_days": days,
        "total_clicks": metrics.total_clicks,
        "compare_button_clicks": metrics.compare_button_clicks,
        "contact_button_clicks": metrics.contact_button_clicks,
        "share_button_clicks": metrics.share_button_clicks,
        "favorite_button_clicks": metrics.favorite_button_clicks,
        "institution_engagement_rate": metrics.institution_engagement_rate
    }


@router.get("/searches/popular")
def get_popular_searches(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get most popular search queries.
    """
    from app.models.analytics import PopularSearch
    
    popular = db.query(PopularSearch).order_by(
        PopularSearch.search_count.desc()
    ).limit(limit).all()
    
    return {
        "popular_searches": [
            {
                "query": p.query,
                "search_count": p.search_count,
                "result_count": p.result_count,
                "last_searched": p.last_searched_at.isoformat() if p.last_searched_at else None
            }
            for p in popular
        ]
    }


@router.get("/searches/no-results")
def get_no_result_searches(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get searches that returned no results (content gaps).
    
    Useful for identifying missing institutions or data.
    """
    return {
        "content_gaps": AnalyticsAggregator.get_no_result_searches(db, limit=limit)
    }


@router.get("/daily/{target_date}")
def get_daily_analytics(
    target_date: date,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get analytics summary for a specific date.
    """
    return AnalyticsAggregator.get_daily_summary(db, target_date)


# ============================================
# PUBLIC ENDPOINTS
# ============================================

@router.get("/public/popular-searches")
def get_public_popular_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get popular searches for display on homepage.
    
    Public endpoint - no authentication required.
    """
    from app.models.analytics import PopularSearch
    
    popular = db.query(PopularSearch).order_by(
        PopularSearch.search_count.desc()
    ).limit(limit).all()
    
    return {
        "popular_searches": [
            {
                "query": p.query,
                "search_count": p.search_count
            }
            for p in popular
        ]
    }


@router.get("/public/trending-searches")
def get_public_trending_searches(
    limit: int = Query(10, ge=1, le=20),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """
    Get trending searches (growing in popularity).
    
    Public endpoint - no authentication required.
    """
    trending = AnalyticsAggregator._get_trending_searches(db, days=days)
    
    return {
        "trending_searches": trending[:limit]
    }
