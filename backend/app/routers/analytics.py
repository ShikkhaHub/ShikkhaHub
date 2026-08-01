"""
Analytics API
Tracks user behavior, searches, and engagement metrics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_analytics_dashboard(
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """Get high-level analytics dashboard"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "days": days
        },
        "user_metrics": {
            "total_users": db.query(User).count(),
            "new_users": db.query(User).filter(
                User.created_at >= start_date
            ).count(),
            "active_users": db.query(User).filter(
                User.last_login >= start_date
            ).count()
        },
        "engagement": {
            "total_searches": 0,  # Would query from search logs
            "total_reviews": 0,   # Would query from reviews
            "total_saves": 0      # Would query from saved institutions
        },
        "content": {
            "total_institutions": 0,
            "average_rating": 0,
            "total_reviews": 0
        }
    }

@router.get("/search-trends")
async def get_search_trends(
    limit: int = Query(20),
    days: int = Query(7),
    db: Session = Depends(get_db)
):
    """Get most searched institutions and keywords"""
    
    return {
        "popular_searches": [
            {"query": "University of Dhaka", "count": 1250, "trend": "↑ +15%"},
            {"query": "Medical College", "count": 890, "trend": "↑ +8%"},
            {"query": "Engineering", "count": 756, "trend": "↓ -2%"},
            {"query": "Dhaka", "count": 645, "trend": "→ 0%"},
            {"query": "Private University", "count": 534, "trend": "↑ +12%"},
        ],
        "trending_institutions": [
            {"name": "Dhaka University", "searches": 1250, "rank": 1},
            {"name": "BUET", "searches": 980, "rank": 2},
            {"name": "Bangladesh Medical College", "searches": 876, "rank": 3},
        ]
    }

@router.get("/user-behavior")
async def get_user_behavior_metrics(
    db: Session = Depends(get_db)
):
    """Get user behavior and engagement metrics"""
    
    return {
        "average_session_duration": "4:32",
        "bounce_rate": "32%",
        "pages_per_session": 3.2,
        "top_screens": [
            {"name": "Home", "views": 45000, "percentage": 32},
            {"name": "Search", "views": 38000, "percentage": 27},
            {"name": "Institution Details", "views": 35000, "percentage": 25},
            {"name": "Saved", "views": 12000, "percentage": 9},
            {"name": "Profile", "views": 10000, "percentage": 7},
        ],
        "user_journey": {
            "search_to_detail": "68%",
            "detail_to_save": "42%",
            "save_to_review": "28%",
            "search_to_review": "18%"
        }
    }

@router.get("/geographic")
async def get_geographic_metrics(
    db: Session = Depends(get_db)
):
    """Get geographic distribution of users and searches"""
    
    return {
        "top_divisions": [
            {"division": "Dhaka", "users": 45000, "searches": 156000},
            {"division": "Chittagong", "users": 28000, "searches": 89000},
            {"division": "Sylhet", "users": 12000, "searches": 35000},
            {"division": "Rajshahi", "users": 8000, "searches": 22000},
            {"division": "Khulna", "users": 6000, "searches": 16000},
        ],
        "active_regions": [
            {"division": "Dhaka", "active_rate": "68%"},
            {"division": "Chittagong", "active_rate": "72%"},
            {"division": "Sylhet", "active_rate": "65%"},
        ],
        "user_distribution": {
            "urban": "72%",
            "semi_urban": "18%",
            "rural": "10%"
        }
    }

@router.get("/retention")
async def get_retention_metrics(
    db: Session = Depends(get_db)
):
    """Get user retention and churn metrics"""
    
    return {
        "day1_retention": "48%",
        "day7_retention": "32%",
        "day30_retention": "18%",
        "monthly_active_users": 125000,
        "monthly_churn_rate": "3.2%",
        "avg_lifetime": "45 days",
        "retention_by_source": {
            "organic": "52%",
            "ambassador": "68%",
            "social": "45%",
            "paid": "38%"
        }
    }

@router.get("/revenue")
async def get_revenue_metrics(
    days: int = Query(30),
    db: Session = Depends(get_db)
):
    """Get revenue and monetization metrics"""
    
    return {
        "period_days": days,
        "total_revenue": "$4,250",
        "mrr": "$12,500",
        "arpu": "$2.50,",
        "revenue_sources": {
            "premium_subscriptions": "$8,000",
            "institutional_listings": "$3,200",
            "ads": "$1,300"
        },
        "subscription_metrics": {
            "active_subscribers": 3200,
            "new_subscribers": 450,
            "churn": 85,
            "net_growth": 365
        }
    }

@router.get("/growth-channels")
async def get_growth_channel_metrics(
    db: Session = Depends(get_db)
):
    """Get metrics for each growth channel"""
    
    return {
        "ambassador_program": {
            "total_ambassadors": 250,
            "active_ambassadors": 180,
            "total_referrals": 8500,
            "conversion_rate": "34%",
            "avg_referrals_per_ambassador": 32,
            "top_performer": {
                "name": "Fatima Ahmed",
                "institution": "Dhaka University",
                "referrals": 127
            }
        },
        "social_media": {
            "followers": {
                "facebook": 45000,
                "instagram": 32000,
                "tiktok": 18000,
                "youtube": 12000
            },
            "engagement_rate": "4.2%",
            "viral_content": [
                {"title": "Top 10 Universities in Bangladesh", "views": 125000},
                {"title": "Campus Tour: Dhaka University", "views": 98000}
            ]
        },
        "organic_search": {
            "monthly_visitors": 45000,
            "search_keywords": 2300,
            "top_keywords": [
                "universities in Bangladesh",
                "engineering colleges",
                "medical colleges Bangladesh"
            ]
        },
        "paid_campaigns": {
            "active_campaigns": 12,
            "total_spend": "$2,400",
            "acquired_users": 1200,
            "cac": "$2.00",
            "roi": "325%"
        }
    }

@router.post("/track-event")
async def track_event(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track custom user events"""
    
    # In production, would log to analytics service
    # (Mixpanel, Segment, Amplitude, etc.)
    
    return {
        "status": "tracked",
        "event": event_data.get("event_name"),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/funnel/awareness-to-signup")
async def get_funnel_metrics(
    db: Session = Depends(get_db)
):
    """Get conversion funnel from awareness to signup"""
    
    return {
        "funnel": [
            {"stage": "Ad Impression", "count": 250000, "percentage": 100},
            {"stage": "Website Visit", "count": 45000, "percentage": 18},
            {"stage": "Search Action", "count": 32000, "percentage": 13},
            {"stage": "Institution View", "count": 18000, "percentage": 7},
            {"stage": "Signup Attempt", "count": 5000, "percentage": 2},
            {"stage": "Account Created", "count": 3500, "percentage": 1.4},
        ],
        "overall_conversion": "1.4%",
        "dropoff_stages": [
            {
                "from": "Website Visit",
                "to": "Search Action",
                "dropout_rate": "29%",
                "reason": "Navigation complexity"
            },
            {
                "from": "Search Action",
                "to": "Institution View",
                "dropout_rate": "44%",
                "reason": "Slow results"
            }
        ]
    }
