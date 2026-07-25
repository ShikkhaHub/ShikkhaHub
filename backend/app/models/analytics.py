"""Analytics models for tracking user behavior and search patterns."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class SearchEvent(Base):
    """Track search queries for analytics."""
    __tablename__ = "search_events"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Search context
    filters_used = Column(Text, nullable=True)  # JSON of applied filters
    results_count = Column(Integer, default=0)
    clicked_result = Column(Boolean, default=False)  # Did user click any result?
    clicked_institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    
    # Response time
    search_duration_ms = Column(Float, nullable=True)
    
    # User agent info
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    referrer = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="search_events")
    clicked_institution = relationship("Institution")
    
    __table_args__ = (
        Index('idx_search_query_time', 'query', 'created_at'),
        Index('idx_search_user', 'user_id', 'created_at'),
        Index('idx_search_session', 'session_id', 'created_at'),
        Index('idx_search_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<SearchEvent '{self.query[:50]}...'>"


class PageView(Base):
    """Track page views for analytics."""
    __tablename__ = "page_views"
    
    id = Column(Integer, primary_key=True, index=True)
    path = Column(String(500), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Page context
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    institution_name = Column(String(300), nullable=True)  # Denormalized for performance
    
    # Engagement metrics
    time_on_page_seconds = Column(Integer, nullable=True)  # Updated on next page view
    scroll_depth_percent = Column(Integer, nullable=True)  # Max scroll depth
    
    # Source
    referrer = Column(String(500), nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(200), nullable=True)
    
    # User agent
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    device_type = Column(String(20), nullable=True)  # mobile, desktop, tablet
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="page_views")
    institution = relationship("Institution")
    
    __table_args__ = (
        Index('idx_pageview_path_time', 'path', 'created_at'),
        Index('idx_pageview_institution', 'institution_id', 'created_at'),
        Index('idx_pageview_user', 'user_id', 'created_at'),
        Index('idx_pageview_session', 'session_id', 'created_at'),
        Index('idx_pageview_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PageView {self.path[:50]}...>"


class ClickEvent(Base):
    """Track click events for understanding user behavior."""
    __tablename__ = "click_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # compare, favorite, share, contact, apply
    element_id = Column(String(100), nullable=True)  # DOM element identifier
    element_text = Column(String(200), nullable=True)
    
    # Context
    page_path = Column(String(500), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    
    # Additional data
    metadata = Column(Text, nullable=True)  # JSON with event-specific data
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="click_events")
    institution = relationship("Institution")
    
    __table_args__ = (
        Index('idx_click_type_time', 'event_type', 'created_at'),
        Index('idx_click_institution', 'institution_id', 'created_at'),
        Index('idx_click_session', 'session_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ClickEvent {self.event_type}>"


class PopularSearch(Base):
    """Aggregated popular searches for caching."""
    __tablename__ = "popular_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, unique=True)
    search_count = Column(Integer, default=1)
    result_count = Column(Integer, default=0)
    click_through_rate = Column(Float, default=0.0)  # Percentage of searches with clicks
    last_searched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_popular_search_count', 'search_count'),
    )
    
    def __repr__(self):
        return f"<PopularSearch '{self.query[:50]}...' ({self.search_count})>"


class NoResultSearch(Base):
    """Track searches that returned no results for content gap analysis."""
    __tablename__ = "no_result_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, index=True)
    search_count = Column(Integer, default=1)
    last_searched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_noresult_count', 'search_count'),
        Index('idx_noresult_query', 'query'),
    )
    
    def __repr__(self):
        return f"<NoResultSearch '{self.query[:50]}...' ({self.search_count})>"


class DailyAnalytics(Base):
    """Pre-aggregated daily analytics for dashboard performance."""
    __tablename__ = "daily_analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Search metrics
    total_searches = Column(Integer, default=0)
    unique_searchers = Column(Integer, default=0)
    avg_results_per_search = Column(Float, default=0.0)
    searches_with_clicks = Column(Integer, default=0)
    click_through_rate = Column(Float, default=0.0)
    no_result_searches = Column(Integer, default=0)
    
    # Page view metrics
    total_page_views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_time_on_page = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)  # Single page view sessions
    
    # Institution engagement
    institution_views = Column(Integer, default=0)
    compare_button_clicks = Column(Integer, default=0)
    contact_button_clicks = Column(Integer, default=0)
    
    # Device breakdown (stored as JSON)
    device_breakdown = Column(Text, nullable=True)
    top_searches = Column(Text, nullable=True)  # JSON list
    top_institutions = Column(Text, nullable=True)  # JSON list
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_daily_date', 'date'),
    )
    
    def __repr__(self):
        return f"<DailyAnalytics {self.date.date()}>"
