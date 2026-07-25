"""Analytics service for tracking and aggregating user behavior."""
import json
import logging
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import func, desc, and_, distinct
from sqlalchemy.orm import Session
from user_agents import parse as parse_user_agent

from app.models.analytics import (
    SearchEvent, PageView, ClickEvent,
    PopularSearch, NoResultSearch, DailyAnalytics
)
from app.models.institution import Institution

logger = logging.getLogger(__name__)


@dataclass
class SearchMetrics:
    """Search metrics for a time period."""
    total_searches: int
    unique_queries: int
    avg_results_count: float
    click_through_rate: float
    no_result_rate: float
    top_queries: List[Dict[str, Any]]
    trending_queries: List[Dict[str, Any]]


@dataclass
class PageViewMetrics:
    """Page view metrics for a time period."""
    total_views: int
    unique_visitors: int
    avg_time_on_page: float
    bounce_rate: float
    top_pages: List[Dict[str, Any]]
    top_institutions: List[Dict[str, Any]]
    device_breakdown: Dict[str, int]


@dataclass
class EngagementMetrics:
    """User engagement metrics."""
    total_clicks: int
    compare_button_clicks: int
    contact_button_clicks: int
    share_button_clicks: int
    favorite_button_clicks: int
    institution_engagement_rate: float  # Views that led to a click


class AnalyticsTracker:
    """Track user events and page views."""
    
    DEVICE_PATTERNS = {
        'mobile': r'Mobile|Android|iPhone|iPad|Windows Phone',
        'tablet': r'iPad|Tablet|Android(?!.*Mobile)',
        'desktop': r'Windows|Mac OS X|Linux|CrOS'
    }
    
    @staticmethod
    def detect_device_type(user_agent: Optional[str]) -> str:
        """Detect device type from user agent string."""
        if not user_agent:
            return 'unknown'
        
        user_agent_lower = user_agent.lower()
        
        if re.search(r'ipad|tablet(?!.*pc)|kindle|silk', user_agent_lower):
            return 'tablet'
        elif re.search(r'mobile|android|iphone|ipod|windows phone', user_agent_lower):
            return 'mobile'
        else:
            return 'desktop'
    
    @staticmethod
    def extract_utm_params(referrer: Optional[str]) -> Dict[str, str]:
        """Extract UTM parameters from referrer URL."""
        if not referrer:
            return {}
        
        utm_params = {}
        try:
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(referrer)
            params = parse_qs(parsed.query)
            
            for key in ['utm_source', 'utm_medium', 'utm_campaign']:
                if key in params:
                    utm_params[key] = params[key][0]
        except:
            pass
        
        return utm_params
    
    @classmethod
    def track_search(
        cls,
        db: Session,
        query: str,
        results_count: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        search_duration_ms: Optional[float] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> SearchEvent:
        """Track a search event."""
        event = SearchEvent(
            query=query[:500],  # Truncate if too long
            user_id=user_id,
            session_id=session_id,
            results_count=results_count,
            filters_used=json.dumps(filters) if filters else None,
            search_duration_ms=search_duration_ms,
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
            referrer=referrer[:500] if referrer else None
        )
        
        db.add(event)
        db.commit()
        
        # Update popular searches cache
        cls._update_popular_search(db, query, results_count)
        
        # Track no-result searches
        if results_count == 0:
            cls._update_no_result_search(db, query)
        
        return event
    
    @classmethod
    def track_page_view(
        cls,
        db: Session,
        path: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        institution_id: Optional[int] = None,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> PageView:
        """Track a page view."""
        device_type = cls.detect_device_type(user_agent)
        utm_params = cls.extract_utm_params(referrer)
        
        # Get institution name if viewing institution page
        institution_name = None
        if institution_id:
            inst = db.query(Institution).get(institution_id)
            if inst:
                institution_name = inst.name_en
        
        view = PageView(
            path=path[:500],
            user_id=user_id,
            session_id=session_id,
            institution_id=institution_id,
            institution_name=institution_name[:300] if institution_name else None,
            referrer=referrer[:500] if referrer else None,
            utm_source=utm_params.get('utm_source'),
            utm_medium=utm_params.get('utm_medium'),
            utm_campaign=utm_params.get('utm_campaign'),
            user_agent=user_agent[:500] if user_agent else None,
            ip_address=ip_address,
            device_type=device_type
        )
        
        db.add(view)
        db.commit()
        
        return view
    
    @classmethod
    def track_click(
        cls,
        db: Session,
        event_type: str,
        page_path: str,
        element_id: Optional[str] = None,
        element_text: Optional[str] = None,
        institution_id: Optional[int] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ClickEvent:
        """Track a click event."""
        event = ClickEvent(
            event_type=event_type,
            page_path=page_path[:500],
            element_id=element_id[:100] if element_id else None,
            element_text=element_text[:200] if element_text else None,
            institution_id=institution_id,
            user_id=user_id,
            session_id=session_id,
            metadata=json.dumps(metadata) if metadata else None
        )
        
        db.add(event)
        db.commit()
        
        return event
    
    @classmethod
    def update_search_click(
        cls,
        db: Session,
        search_event_id: int,
        clicked_institution_id: int
    ):
        """Update a search event when user clicks a result."""
        event = db.query(SearchEvent).get(search_event_id)
        if event:
            event.clicked_result = True
            event.clicked_institution_id = clicked_institution_id
            db.commit()
    
    @classmethod
    def _update_popular_search(
        cls,
        db: Session,
        query: str,
        results_count: int
    ):
        """Update or create popular search entry."""
        # Normalize query
        normalized_query = query.lower().strip()
        
        popular = db.query(PopularSearch).filter(
            PopularSearch.query == normalized_query
        ).first()
        
        if popular:
            popular.search_count += 1
            popular.result_count = max(popular.result_count, results_count)
            popular.last_searched_at = datetime.utcnow()
        else:
            popular = PopularSearch(
                query=normalized_query,
                search_count=1,
                result_count=results_count
            )
            db.add(popular)
        
        db.commit()
    
    @classmethod
    def _update_no_result_search(
        cls,
        db: Session,
        query: str
    ):
        """Update or create no-result search entry."""
        normalized_query = query.lower().strip()
        
        noresult = db.query(NoResultSearch).filter(
            NoResultSearch.query == normalized_query
        ).first()
        
        if noresult:
            noresult.search_count += 1
            noresult.last_searched_at = datetime.utcnow()
        else:
            noresult = NoResultSearch(query=normalized_query)
            db.add(noresult)
        
        db.commit()


class AnalyticsAggregator:
    """Aggregate analytics data for reporting."""
    
    @staticmethod
    def get_search_metrics(
        db: Session,
        days: int = 30
    ) -> SearchMetrics:
        """Get search metrics for the specified time period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total searches
        total = db.query(SearchEvent).filter(
            SearchEvent.created_at >= cutoff
        ).count()
        
        # Unique queries
        unique_queries = db.query(distinct(SearchEvent.query)).filter(
            SearchEvent.created_at >= cutoff
        ).count()
        
        # Average results per search
        avg_results = db.query(func.avg(SearchEvent.results_count)).filter(
            SearchEvent.created_at >= cutoff
        ).scalar() or 0
        
        # Click-through rate
        searches_with_clicks = db.query(SearchEvent).filter(
            SearchEvent.created_at >= cutoff,
            SearchEvent.clicked_result == True
        ).count()
        
        click_through_rate = (searches_with_clicks / total * 100) if total > 0 else 0
        
        # No-result searches
        no_result_count = db.query(SearchEvent).filter(
            SearchEvent.created_at >= cutoff,
            SearchEvent.results_count == 0
        ).count()
        
        no_result_rate = (no_result_count / total * 100) if total > 0 else 0
        
        # Top queries
        top_queries = db.query(
            SearchEvent.query,
            func.count(SearchEvent.id).label('count')
        ).filter(
            SearchEvent.created_at >= cutoff
        ).group_by(SearchEvent.query).order_by(desc('count')).limit(10).all()
        
        top_queries_list = [
            {"query": q, "count": c} for q, c in top_queries
        ]
        
        # Trending queries (last 7 days vs previous 7 days)
        trending = AnalyticsAggregator._get_trending_searches(db, days=7)
        
        return SearchMetrics(
            total_searches=total,
            unique_queries=unique_queries,
            avg_results_count=round(avg_results, 2),
            click_through_rate=round(click_through_rate, 2),
            no_result_rate=round(no_result_rate, 2),
            top_queries=top_queries_list,
            trending_queries=trending
        )
    
    @staticmethod
    def _get_trending_searches(db: Session, days: int = 7) -> List[Dict[str, Any]]:
        """Get trending searches by comparing recent vs previous period."""
        now = datetime.utcnow()
        recent_start = now - timedelta(days=days)
        previous_start = now - timedelta(days=days * 2)
        
        # Recent period searches
        recent = db.query(
            SearchEvent.query,
            func.count(SearchEvent.id).label('count')
        ).filter(
            SearchEvent.created_at >= recent_start
        ).group_by(SearchEvent.query).all()
        
        # Previous period searches
        previous = db.query(
            SearchEvent.query,
            func.count(SearchEvent.id).label('count')
        ).filter(
            SearchEvent.created_at >= previous_start,
            SearchEvent.created_at < recent_start
        ).group_by(SearchEvent.query).all()
        
        previous_counts = {q: c for q, c in previous}
        
        trending = []
        for query, recent_count in recent:
            prev_count = previous_counts.get(query, 0)
            growth = ((recent_count - prev_count) / prev_count * 100) if prev_count > 0 else 100
            if recent_count >= 5:  # Minimum threshold
                trending.append({
                    "query": query,
                    "recent_count": recent_count,
                    "previous_count": prev_count,
                    "growth_percent": round(growth, 1)
                })
        
        trending.sort(key=lambda x: x["growth_percent"], reverse=True)
        return trending[:10]
    
    @staticmethod
    def get_page_view_metrics(
        db: Session,
        days: int = 30
    ) -> PageViewMetrics:
        """Get page view metrics for the specified time period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total views
        total = db.query(PageView).filter(
            PageView.created_at >= cutoff
        ).count()
        
        # Unique visitors (by session_id)
        unique_visitors = db.query(distinct(PageView.session_id)).filter(
            PageView.created_at >= cutoff
        ).count()
        
        # Average time on page
        avg_time = db.query(func.avg(PageView.time_on_page_seconds)).filter(
            PageView.created_at >= cutoff,
            PageView.time_on_page_seconds != None
        ).scalar() or 0
        
        # Bounce rate (single page view sessions)
        sessions_with_multiple = db.query(distinct(PageView.session_id)).filter(
            PageView.created_at >= cutoff
        ).group_by(PageView.session_id).having(func.count(PageView.id) > 1).count()
        
        total_sessions = db.query(distinct(PageView.session_id)).filter(
            PageView.created_at >= cutoff
        ).count()
        
        bounce_rate = 100 - (sessions_with_multiple / total_sessions * 100) if total_sessions > 0 else 0
        
        # Top pages
        top_pages = db.query(
            PageView.path,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.created_at >= cutoff
        ).group_by(PageView.path).order_by(desc('views')).limit(10).all()
        
        top_pages_list = [{"path": p, "views": v} for p, v in top_pages]
        
        # Top institutions
        top_institutions = db.query(
            PageView.institution_id,
            PageView.institution_name,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.created_at >= cutoff,
            PageView.institution_id != None
        ).group_by(PageView.institution_id, PageView.institution_name).order_by(
            desc('views')
        ).limit(10).all()
        
        top_institutions_list = [
            {"institution_id": iid, "name": name, "views": v}
            for iid, name, v in top_institutions
        ]
        
        # Device breakdown
        devices = db.query(
            PageView.device_type,
            func.count(PageView.id).label('count')
        ).filter(
            PageView.created_at >= cutoff
        ).group_by(PageView.device_type).all()
        
        device_breakdown = {d: c for d, c in devices}
        
        return PageViewMetrics(
            total_views=total,
            unique_visitors=unique_visitors,
            avg_time_on_page=round(avg_time, 2),
            bounce_rate=round(bounce_rate, 2),
            top_pages=top_pages_list,
            top_institutions=top_institutions_list,
            device_breakdown=device_breakdown
        )
    
    @staticmethod
    def get_engagement_metrics(
        db: Session,
        days: int = 30
    ) -> EngagementMetrics:
        """Get user engagement metrics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Total clicks
        total_clicks = db.query(ClickEvent).filter(
            ClickEvent.created_at >= cutoff
        ).count()
        
        # Clicks by type
        clicks_by_type = db.query(
            ClickEvent.event_type,
            func.count(ClickEvent.id).label('count')
        ).filter(
            ClickEvent.created_at >= cutoff
        ).group_by(ClickEvent.event_type).all()
        
        clicks_dict = {t: c for t, c in clicks_by_type}
        
        # Institution engagement rate
        institution_views = db.query(PageView).filter(
            PageView.created_at >= cutoff,
            PageView.institution_id != None
        ).count()
        
        institution_clicks = db.query(ClickEvent).filter(
            ClickEvent.created_at >= cutoff,
            ClickEvent.institution_id != None
        ).count()
        
        engagement_rate = (institution_clicks / institution_views * 100) if institution_views > 0 else 0
        
        return EngagementMetrics(
            total_clicks=total_clicks,
            compare_button_clicks=clicks_dict.get('compare', 0),
            contact_button_clicks=clicks_dict.get('contact', 0),
            share_button_clicks=clicks_dict.get('share', 0),
            favorite_button_clicks=clicks_dict.get('favorite', 0),
            institution_engagement_rate=round(engagement_rate, 2)
        )
    
    @staticmethod
    def get_daily_summary(
        db: Session,
        target_date: date = None
    ) -> Dict[str, Any]:
        """Get summary for a specific day."""
        if target_date is None:
            target_date = date.today()
        
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        # Search metrics
        searches = db.query(SearchEvent).filter(
            SearchEvent.created_at >= start,
            SearchEvent.created_at <= end
        ).count()
        
        unique_searchers = db.query(distinct(SearchEvent.session_id)).filter(
            SearchEvent.created_at >= start,
            SearchEvent.created_at <= end
        ).count()
        
        # Page views
        page_views = db.query(PageView).filter(
            PageView.created_at >= start,
            PageView.created_at <= end
        ).count()
        
        unique_visitors = db.query(distinct(PageView.session_id)).filter(
            PageView.created_at >= start,
            PageView.created_at <= end
        ).count()
        
        # Top searches of the day
        top_searches = db.query(
            SearchEvent.query,
            func.count(SearchEvent.id).label('count')
        ).filter(
            SearchEvent.created_at >= start,
            SearchEvent.created_at <= end
        ).group_by(SearchEvent.query).order_by(desc('count')).limit(5).all()
        
        # Top institutions of the day
        top_institutions = db.query(
            PageView.institution_id,
            PageView.institution_name,
            func.count(PageView.id).label('views')
        ).filter(
            PageView.created_at >= start,
            PageView.created_at <= end,
            PageView.institution_id != None
        ).group_by(PageView.institution_id, PageView.institution_name).order_by(
            desc('views')
        ).limit(5).all()
        
        return {
            "date": target_date.isoformat(),
            "searches": searches,
            "unique_searchers": unique_searchers,
            "page_views": page_views,
            "unique_visitors": unique_visitors,
            "top_searches": [{"query": q, "count": c} for q, c in top_searches],
            "top_institutions": [
                {"id": iid, "name": name, "views": v}
                for iid, name, v in top_institutions
            ]
        }
    
    @staticmethod
    def get_no_result_searches(
        db: Session,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get searches that returned no results."""
        noresults = db.query(NoResultSearch).order_by(
            desc(NoResultSearch.search_count)
        ).limit(limit).all()
        
        return [
            {
                "query": n.query,
                "search_count": n.search_count,
                "last_searched": n.last_searched_at.isoformat() if n.last_searched_at else None
            }
            for n in noresults
        ]
    
    @staticmethod
    def aggregate_daily(
        db: Session,
        target_date: date = None
    ) -> DailyAnalytics:
        """Aggregate and store daily analytics."""
        if target_date is None:
            target_date = date.today() - timedelta(days=1)
        
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        # Check if already exists
        existing = db.query(DailyAnalytics).filter(
            DailyAnalytics.date == start
        ).first()
        
        if existing:
            return existing
        
        # Calculate metrics
        total_searches = db.query(SearchEvent).filter(
            SearchEvent.created_at >= start,
            SearchEvent.created_at <= end
        ).count()
        
        unique_searchers = db.query(distinct(SearchEvent.session_id)).filter(
            SearchEvent.created_at >= start,
            SearchEvent.created_at <= end
        ).count()
        
        total_page_views = db.query(PageView).filter(
            PageView.created_at >= start,
            PageView.created_at <= end
        ).count()
        
        unique_visitors = db.query(distinct(PageView.session_id)).filter(
            PageView.created_at >= start,
            PageView.created_at <= end
        ).count()
        
        # Create daily record
        daily = DailyAnalytics(
            date=start,
            total_searches=total_searches,
            unique_searchers=unique_searchers,
            total_page_views=total_page_views,
            unique_visitors=unique_visitors
        )
        
        db.add(daily)
        db.commit()
        
        return daily


class AnalyticsDashboard:
    """Generate dashboard data for admin analytics view."""
    
    @staticmethod
    def get_overview(db: Session) -> Dict[str, Any]:
        """Get analytics overview for dashboard."""
        now = datetime.utcnow()
        today = now.date()
        
        # Today's metrics
        today_start = datetime.combine(today, datetime.min.time())
        
        today_searches = db.query(SearchEvent).filter(
            SearchEvent.created_at >= today_start
        ).count()
        
        today_views = db.query(PageView).filter(
            PageView.created_at >= today_start
        ).count()
        
        # Compare to yesterday
        yesterday = today - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        yesterday_end = datetime.combine(today, datetime.min.time())
        
        yesterday_searches = db.query(SearchEvent).filter(
            SearchEvent.created_at >= yesterday_start,
            SearchEvent.created_at < yesterday_end
        ).count()
        
        yesterday_views = db.query(PageView).filter(
            PageView.created_at >= yesterday_start,
            PageView.created_at < yesterday_end
        ).count()
        
        search_change = ((today_searches - yesterday_searches) / yesterday_searches * 100) if yesterday_searches > 0 else 0
        views_change = ((today_views - yesterday_views) / yesterday_views * 100) if yesterday_views > 0 else 0
        
        # Last 30 days metrics
        search_metrics = AnalyticsAggregator.get_search_metrics(db, days=30)
        page_metrics = AnalyticsAggregator.get_page_view_metrics(db, days=30)
        engagement = AnalyticsAggregator.get_engagement_metrics(db, days=30)
        
        # No-result searches (content gaps)
        content_gaps = AnalyticsAggregator.get_no_result_searches(db, limit=10)
        
        return {
            "today": {
                "searches": today_searches,
                "page_views": today_views,
                "search_change_percent": round(search_change, 1),
                "views_change_percent": round(views_change, 1)
            },
            "last_30_days": {
                "searches": {
                    "total": search_metrics.total_searches,
                    "unique_queries": search_metrics.unique_queries,
                    "click_through_rate": search_metrics.click_through_rate,
                    "no_result_rate": search_metrics.no_result_rate,
                    "top_queries": search_metrics.top_queries
                },
                "page_views": {
                    "total": page_metrics.total_views,
                    "unique_visitors": page_metrics.unique_visitors,
                    "bounce_rate": page_metrics.bounce_rate,
                    "device_breakdown": page_metrics.device_breakdown
                },
                "engagement": {
                    "total_clicks": engagement.total_clicks,
                    "compare_clicks": engagement.compare_button_clicks,
                    "contact_clicks": engagement.contact_button_clicks,
                    "engagement_rate": engagement.institution_engagement_rate
                }
            },
            "content_gaps": content_gaps,
            "trending_searches": search_metrics.trending_queries
        }
