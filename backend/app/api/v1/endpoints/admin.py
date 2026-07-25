"""
Admin endpoints for data import, verification, moderation, monitoring and data quality.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add scraper to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../scraper'))

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_admin_user, get_current_super_admin
from app.core.rate_limit import admin_limit
from app.core.monitoring import metrics_collector, HealthChecker
from app.services.data_quality import DataQualityService
from app.services.backup import BackupService, BackupType, get_backup_service
from app.models.user import User, UserRole
from app.models.institution import Institution
from app.models.review import InstitutionReview, ReviewReport, ReviewStatus
from app.models.qa import Question, Answer, QuestionStatus, AnswerStatus
from app.models.comment import Comment, CommentStatus
from app.models.chat import ChatSession, ChatMessage

router = APIRouter()


@router.post("/import/csv")
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and import institutions from CSV file.
    
    Required columns: name_en
    Optional columns: name_bn, short_name, institution_type, division, district, 
                      upazila, address, phone, email, website, established_year,
                      education_level, education_board
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        from scraper.importers.csv_importer import CSVImporter
        
        content = await file.read()
        csv_content = content.decode('utf-8-sig')
        
        importer = CSVImporter()
        result = importer.import_from_string(csv_content, data_source=f"csv_upload:{file.filename}")
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Import completed",
                "filename": file.filename,
                "stats": result['import_stats']
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('error', 'Import failed'))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")


@router.get("/import/template")
def get_csv_template():
    """Download CSV template for manual data entry."""
    try:
        from scraper.importers.csv_importer import CSVImporter
        
        importer = CSVImporter()
        template = importer.generate_template()
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=template,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=institution_template.csv"}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template generation failed: {str(e)}")


@router.post("/trigger-scrape")
def trigger_scrape(
    background_tasks: BackgroundTasks,
    source: str = "ugc",
    db: Session = Depends(get_db)
):
    """
    Trigger data scraping from source (admin only in production).
    
    Sources: ugc, bmeb, bteb, board
    """
    if settings.ENVIRONMENT == "production":
        # TODO: Add authentication check
        raise HTTPException(status_code=403, detail="Scraping disabled in production")
    
    try:
        from scraper.run import run_scraper
        from scraper.scrapers import UGCScraper, BMEBScraper, BTEBScraper
        
        scrapers = {
            'ugc': UGCScraper,
            'bmeb': BMEBScraper,
            'bteb': BTEBScraper
        }
        
        scraper_class = scrapers.get(source)
        if not scraper_class:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
        
        # Run in background
        background_tasks.add_task(run_scraper, scraper_class, import_to_db=True)
        
        return {
            "success": True,
            "message": f"Scraping job started for {source}",
            "source": source
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


# Institution Verification Endpoints
@router.get("/institutions/pending")
@admin_limit()
def list_pending_institutions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List institutions pending verification."""
    query = db.query(Institution).filter(
        Institution.verification_status == "pending"
    ).order_by(desc(Institution.created_at))
    
    total = query.count()
    institutions = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_institution_to_dict(i) for i in institutions],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.post("/institutions/{institution_id}/verify")
@admin_limit()
def verify_institution(
    institution_id: int,
    verification_notes: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Verify an institution."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    institution.verification_status = "verified"
    # Could add verification_notes field to model
    db.commit()
    
    return {"message": "Institution verified successfully", "institution_id": institution_id}


@router.post("/institutions/{institution_id}/reject")
@admin_limit()
def reject_institution(
    institution_id: int,
    reason: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reject an institution."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    institution.verification_status = "rejected"
    db.commit()
    
    return {"message": "Institution rejected", "institution_id": institution_id, "reason": reason}


@router.post("/institutions/{institution_id}/flag")
@admin_limit()
def flag_institution(
    institution_id: int,
    reason: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Flag an institution for review."""
    institution = db.query(Institution).filter(Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    institution.verification_status = "flagged"
    db.commit()
    
    return {"message": "Institution flagged for review", "institution_id": institution_id}


# Content Moderation Endpoints
@router.get("/moderation/reviews/pending")
@admin_limit()
def list_pending_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List reviews pending approval."""
    query = db.query(InstitutionReview).filter(
        InstitutionReview.status == ReviewStatus.PENDING
    ).order_by(desc(InstitutionReview.created_at))
    
    total = query.count()
    reviews = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_review_to_dict(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/moderation/reviews/flagged")
@admin_limit()
def list_flagged_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List flagged reviews."""
    query = db.query(InstitutionReview).filter(
        InstitutionReview.status == ReviewStatus.FLAGGED
    ).order_by(desc(InstitutionReview.created_at))
    
    total = query.count()
    reviews = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_review_to_dict(r) for r in reviews],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/moderation/reports")
@admin_limit()
def list_reports(
    status: str = Query("pending", enum=["pending", "resolved"]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List content reports."""
    is_resolved = status == "resolved"
    
    query = db.query(ReviewReport).filter(
        ReviewReport.is_resolved == is_resolved
    ).order_by(desc(ReviewReport.created_at))
    
    total = query.count()
    reports = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_report_to_dict(r) for r in reports],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.post("/moderation/reports/{report_id}/resolve")
@admin_limit()
def resolve_report(
    report_id: int,
    action: str,  # "dismiss", "remove_content", "warn_user"
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Resolve a content report."""
    report = db.query(ReviewReport).filter(ReviewReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report.is_resolved = True
    report.resolved_by = current_user.id
    report.resolved_at = datetime.utcnow()
    report.resolution = action
    
    # Take action based on resolution
    if action == "remove_content":
        review = db.query(InstitutionReview).filter(InstitutionReview.id == report.review_id).first()
        if review:
            review.status = ReviewStatus.REJECTED
    elif action == "warn_user":
        # Could implement user warning system
        pass
    
    db.commit()
    
    return {"message": "Report resolved", "action": action}


# Dashboard Stats API
@router.get("/dashboard/stats")
@admin_limit()
def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics."""
    
    # Institution stats
    total_institutions = db.query(Institution).count()
    verified_institutions = db.query(Institution).filter(
        Institution.verification_status == "verified"
    ).count()
    pending_institutions = db.query(Institution).filter(
        Institution.verification_status == "pending"
    ).count()
    flagged_institutions = db.query(Institution).filter(
        Institution.verification_status == "flagged"
    ).count()
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    new_users_today = db.query(User).filter(
        User.created_at >= datetime.utcnow().date()
    ).count()
    
    # Review stats
    total_reviews = db.query(InstitutionReview).count()
    pending_reviews = db.query(InstitutionReview).filter(
        InstitutionReview.status == ReviewStatus.PENDING
    ).count()
    flagged_reviews = db.query(InstitutionReview).filter(
        InstitutionReview.status == ReviewStatus.FLAGGED
    ).count()
    
    # Q&A stats
    total_questions = db.query(Question).count()
    unanswered_questions = db.query(Question).filter(
        Question.status == QuestionStatus.OPEN
    ).count()
    total_answers = db.query(Answer).count()
    
    # Chat stats
    total_chat_sessions = db.query(ChatSession).count()
    total_messages = db.query(ChatMessage).count()
    
    # Pending reports
    pending_reports = db.query(ReviewReport).filter(
        ReviewReport.is_resolved == False
    ).count()
    
    return {
        "institutions": {
            "total": total_institutions,
            "verified": verified_institutions,
            "pending": pending_institutions,
            "flagged": flagged_institutions
        },
        "users": {
            "total": total_users,
            "active": active_users,
            "new_today": new_users_today
        },
        "reviews": {
            "total": total_reviews,
            "pending": pending_reviews,
            "flagged": flagged_reviews
        },
        "qa": {
            "total_questions": total_questions,
            "unanswered": unanswered_questions,
            "total_answers": total_answers
        },
        "chat": {
            "total_sessions": total_chat_sessions,
            "total_messages": total_messages
        },
        "moderation": {
            "pending_reports": pending_reports
        }
    }


@router.get("/dashboard/top-institutions")
@admin_limit()
def get_top_institutions(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get top institutions by view count."""
    institutions = db.query(Institution).order_by(
        desc(Institution.view_count)
    ).limit(limit).all()
    
    return {
        "items": [
            {
                "id": i.id,
                "name": i.name_en,
                "view_count": i.view_count,
                "type": i.type.name if i.type else None,
                "verification_status": i.verification_status
            }
            for i in institutions
        ]
    }


@router.get("/dashboard/recent-activity")
@admin_limit()
def get_recent_activity(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get recent platform activity."""
    
    # Recent reviews
    recent_reviews = db.query(InstitutionReview).order_by(
        desc(InstitutionReview.created_at)
    ).limit(limit // 4).all()
    
    # Recent questions
    recent_questions = db.query(Question).order_by(
        desc(Question.created_at)
    ).limit(limit // 4).all()
    
    # Recent users
    recent_users = db.query(User).order_by(
        desc(User.created_at)
    ).limit(limit // 4).all()
    
    # Recent reports
    recent_reports = db.query(ReviewReport).filter(
        ReviewReport.is_resolved == False
    ).order_by(desc(ReviewReport.created_at)).limit(limit // 4).all()
    
    activity = []
    
    for review in recent_reviews:
        activity.append({
            "type": "review",
            "description": f"New review on {review.institution.name_en if review.institution else 'Unknown'}",
            "user": review.user.full_name if review.user else "Anonymous",
            "timestamp": review.created_at.isoformat() if review.created_at else None,
            "status": review.status.value
        })
    
    for question in recent_questions:
        activity.append({
            "type": "question",
            "description": question.title,
            "user": question.user.full_name if question.user else "Anonymous",
            "timestamp": question.created_at.isoformat() if question.created_at else None,
            "status": question.status.value
        })
    
    for user in recent_users:
        activity.append({
            "type": "user",
            "description": f"New user registered: {user.email}",
            "user": user.full_name,
            "timestamp": user.created_at.isoformat() if user.created_at else None,
            "status": "active" if user.is_active else "inactive"
        })
    
    for report in recent_reports:
        activity.append({
            "type": "report",
            "description": f"Report on review: {report.reason}",
            "user": report.reporter.full_name if report.reporter else "Anonymous",
            "timestamp": report.created_at.isoformat() if report.created_at else None,
            "status": "pending"
        })
    
    # Sort by timestamp
    activity.sort(key=lambda x: x["timestamp"] if x["timestamp"] else "", reverse=True)
    
    return {"items": activity[:limit]}


# User Management Endpoints
@router.get("/users")
@admin_limit()
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, enum=["user", "admin", "super_admin", "moderator"]),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": [_user_to_dict(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size
    }


@router.get("/users/{user_id}")
@admin_limit()
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return _user_to_dict(user, include_stats=True)


@router.put("/users/{user_id}/role")
@admin_limit()
def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db)
):
    """Update user role (super admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user.role = role
    db.commit()
    
    return {"message": "User role updated", "user_id": user_id, "new_role": role}


@router.post("/users/{user_id}/deactivate")
@admin_limit()
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate a user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated", "user_id": user_id}


@router.post("/users/{user_id}/activate")
@admin_limit()
def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Reactivate a user account (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated", "user_id": user_id}


# Helper functions
def _institution_to_dict(institution: Institution) -> dict:
    """Convert institution to dict."""
    return {
        "id": institution.id,
        "name_en": institution.name_en,
        "name_bn": institution.name_bn,
        "slug": institution.slug,
        "type": institution.type.name if institution.type else None,
        "verification_status": institution.verification_status,
        "view_count": institution.view_count,
        "created_at": institution.created_at.isoformat() if institution.created_at else None,
        "data_source": institution.data_source
    }


def _review_to_dict(review: InstitutionReview) -> dict:
    """Convert review to dict."""
    return {
        "id": review.id,
        "institution_id": review.institution_id,
        "institution_name": review.institution.name_en if review.institution else "Unknown",
        "user_id": review.user_id,
        "user_name": review.user.full_name if review.user else "Anonymous",
        "overall_rating": review.overall_rating,
        "title": review.title,
        "content": review.content[:200] + "..." if len(review.content) > 200 else review.content,
        "status": review.status.value,
        "created_at": review.created_at.isoformat() if review.created_at else None
    }


def _report_to_dict(report: ReviewReport) -> dict:
    """Convert report to dict."""
    return {
        "id": report.id,
        "review_id": report.review_id,
        "reporter_id": report.reporter_id,
        "reporter_name": report.reporter.full_name if report.reporter else "Anonymous",
        "reason": report.reason,
        "description": report.description,
        "is_resolved": report.is_resolved,
        "created_at": report.created_at.isoformat() if report.created_at else None
    }


# ============================================
# MONITORING ENDPOINTS
# ============================================

@router.get("/monitoring/metrics")
def get_application_metrics(
    admin: User = Depends(get_current_admin_user)
):
    """
    Get application performance metrics.
    
    Returns:
    - Request rates and response times
    - Error rates
    - System resource usage
    - Slowest endpoints
    """
    return metrics_collector.get_all_metrics()


@router.get("/monitoring/health")
def get_detailed_health(
    admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed health status of all system components.
    
    Checks:
    - Database connectivity
    - Redis connectivity
    - Elasticsearch cluster health
    """
    return HealthChecker.get_all_checks()


@router.get("/monitoring/slow-endpoints")
def get_slow_endpoints(
    limit: int = Query(10, ge=1, le=50),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get the slowest API endpoints by average response time.
    """
    return {
        "slowest_endpoints": metrics_collector.get_slowest_endpoints(limit),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/monitoring/errors")
def get_error_summary(
    limit: int = Query(10, ge=1, le=50),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get summary of most common errors.
    """
    return {
        "top_errors": metrics_collector.get_error_summary(limit),
        "error_rate_5m": metrics_collector.get_error_rate(5),
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================
# DATA QUALITY ENDPOINTS
# ============================================

@router.get("/data-quality/summary")
def get_data_quality_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get overall data quality summary.
    
    Includes:
    - Verification status breakdown
    - Data source distribution
    - Data freshness statistics
    """
    service = DataQualityService(db)
    return service.get_overall_quality_summary()


@router.get("/data-quality/institution/{institution_id}")
def get_institution_quality_report(
    institution_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed data quality report for a specific institution.
    
    Includes:
    - Overall quality score (0-100)
    - Freshness score
    - Completeness score
    - Accuracy score
    - List of validation issues
    """
    service = DataQualityService(db)
    report = service.generate_institution_report(institution_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    return {
        "institution_id": report.institution_id,
        "institution_name": report.institution_name,
        "overall_score": report.overall_score,
        "freshness_score": report.freshness_score,
        "completeness_score": report.completeness_score,
        "accuracy_score": report.accuracy_score,
        "issues": [
            {
                "field": issue.field,
                "type": issue.issue_type,
                "message": issue.message,
                "severity": issue.severity
            }
            for issue in report.issues
        ]
    }


@router.post("/data-quality/validate-all")
def validate_all_institutions(
    institution_type_id: Optional[int] = None,
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Run validation on all institutions.
    
    Returns summary of:
    - Average quality scores
    - Issues by type
    - Institutions with errors/warnings
    """
    service = DataQualityService(db)
    return service.validate_all_institutions(institution_type_id, limit)


@router.get("/data-quality/duplicates")
def find_duplicate_institutions(
    institution_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Find potential duplicate institutions.
    
    Uses similarity matching on:
    - Institution names (English and Bengali)
    - Short names
    - Location
    - Phone numbers
    
    Returns matches with confidence levels (high/medium/low).
    """
    service = DataQualityService(db)
    duplicates = service.find_duplicates(institution_type_id)
    
    return {
        "total_potential_duplicates": len(duplicates),
        "matches": [
            {
                "institution_1": {
                    "id": dup.institution_id_1,
                    "name": dup.institution_name_1
                },
                "institution_2": {
                    "id": dup.institution_id_2,
                    "name": dup.institution_name_2
                },
                "similarity_score": round(dup.similarity_score, 3),
                "matching_fields": dup.matching_fields,
                "confidence": dup.confidence
            }
            for dup in duplicates
        ],
        "threshold_used": settings.DUPLICATE_SIMILARITY_THRESHOLD
    }


@router.get("/data-quality/stale-data")
def find_stale_data(
    institution_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Find institutions with stale (outdated) data.
    
    Staleness determined by:
    - Last update timestamp
    - Configured freshness threshold (default: 90 days)
    
    Returns institutions sorted by age (oldest first).
    """
    service = DataQualityService(db)
    stale = service.find_stale_data(institution_type_id)
    
    return {
        "stale_data_count": len(stale),
        "freshness_threshold_days": settings.DATA_FRESHNESS_DAYS,
        "institutions": stale
    }


@router.get("/data-quality/freshness-summary")
def get_freshness_summary(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get data freshness summary statistics.
    
    Categories:
    - Fresh: Updated within last 30 days
    - Aging: Updated within 30-90 days
    - Stale: Updated 90-180 days ago
    - Very Stale: Not updated for 180+ days
    """
    service = DataQualityService(db)
    return service.freshness_checker.get_freshness_summary(db)


# ============================================
# BACKUP & RECOVERY ENDPOINTS
# ============================================

@router.get("/backups")
def list_backups(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    admin: User = Depends(get_current_admin_user)
):
    """
    List all database backups.
    
    Query params:
    - status: Filter by status (pending, completed, failed, verified)
    - limit: Maximum number of backups to return
    """
    backup_service = get_backup_service()
    backups = backup_service.list_backups(status=status, limit=limit)
    
    return {
        "backups": [b.to_dict() for b in backups],
        "count": len(backups)
    }


@router.post("/backups/create")
def create_backup(
    backup_type: str = Query("full", enum=["full", "data_only", "schema_only"]),
    compress: bool = Query(True),
    verify: bool = Query(True),
    admin: User = Depends(get_current_admin_user)
):
    """
    Create a new database backup.
    
    Types:
    - full: Complete database backup (default)
    - data_only: Data without schema
    - schema_only: Schema without data
    """
    backup_service = get_backup_service()
    
    try:
        backup_type_enum = BackupType(backup_type)
        
        metadata = backup_service.create_backup(
            backup_type=backup_type_enum,
            compress=compress
        )
        
        # Verify if requested
        if verify and metadata.status == "completed":
            backup_service.verify_backup(metadata.id)
            # Reload metadata to get verification status
            metadata = backup_service._load_metadata(metadata.id)
        
        return {
            "success": True,
            "backup": metadata.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/backups/{backup_id}")
def get_backup_details(
    backup_id: str,
    admin: User = Depends(get_current_admin_user)
):
    """
    Get detailed information about a specific backup.
    """
    backup_service = get_backup_service()
    metadata = backup_service._load_metadata(backup_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return metadata.to_dict()


@router.post("/backups/{backup_id}/verify")
def verify_backup(
    backup_id: str,
    admin: User = Depends(get_current_admin_user)
):
    """
    Verify backup integrity by checking checksum and structure.
    
    Returns verification result and updates backup status.
    """
    backup_service = get_backup_service()
    
    metadata = backup_service._load_metadata(backup_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    is_valid = backup_service.verify_backup(backup_id)
    
    # Reload to get updated status
    metadata = backup_service._load_metadata(backup_id)
    
    return {
        "backup_id": backup_id,
        "valid": is_valid,
        "verification_status": metadata.verification_status if metadata else None,
        "verified_at": metadata.verified_at.isoformat() if metadata and metadata.verified_at else None
    }


@router.post("/backups/{backup_id}/restore")
def restore_backup(
    backup_id: str,
    force: bool = Query(False, description="Must be True to confirm restore"),
    admin: User = Depends(get_current_super_admin)  # Super admin only
):
    """
    Restore database from backup.
    
    WARNING: This will overwrite the current database!
    Requires force=True to proceed.
    
    Only super admins can perform restores.
    """
    if not force:
        raise HTTPException(
            status_code=400,
            detail="Restore requires force=True. This will overwrite existing data!"
        )
    
    backup_service = get_backup_service()
    
    metadata = backup_service._load_metadata(backup_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if metadata.status not in ["completed", "verified"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot restore backup with status: {metadata.status}"
        )
    
    success = backup_service.restore_backup(backup_id, force=True)
    
    if not success:
        raise HTTPException(status_code=500, detail="Restore failed")
    
    return {
        "success": True,
        "message": f"Database restored from backup {backup_id}",
        "backup_id": backup_id,
        "restored_at": datetime.utcnow().isoformat()
    }


@router.delete("/backups/{backup_id}")
def delete_backup(
    backup_id: str,
    admin: User = Depends(get_current_admin_user)
):
    """
    Delete a backup and its metadata.
    """
    backup_service = get_backup_service()
    
    metadata = backup_service._load_metadata(backup_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    success = backup_service.delete_backup(backup_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete backup")
    
    return {
        "success": True,
        "message": f"Backup {backup_id} deleted",
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.post("/backups/cleanup")
def cleanup_old_backups(
    admin: User = Depends(get_current_admin_user)
):
    """
    Remove backups older than retention period.
    
    Default retention: 30 days (configurable via BACKUP_RETENTION_DAYS)
    """
    backup_service = get_backup_service()
    deleted_count = backup_service.cleanup_old_backups()
    
    return {
        "success": True,
        "deleted_count": deleted_count,
        "retention_days": settings.BACKUP_RETENTION_DAYS,
        "cleaned_at": datetime.utcnow().isoformat()
    }


@router.get("/backups/stats")
def get_backup_statistics(
    admin: User = Depends(get_current_admin_user)
):
    """
    Get backup statistics and storage information.
    
    Returns:
    - Total number of backups
    - Status breakdown
    - Total storage used
    - Oldest/newest backup dates
    - Retention policy
    """
    backup_service = get_backup_service()
    stats = backup_service.get_backup_stats()
    
    return stats


@router.get("/backups/status")
def get_backup_system_status(
    admin: User = Depends(get_current_admin_user)
):
    """
    Get overall backup system status.
    
    Returns configuration and latest backup information.
    """
    backup_service = get_backup_service()
    
    # Get latest backup
    backups = backup_service.list_backups(limit=1)
    latest_backup = backups[0].to_dict() if backups else None
    
    # Check if backups are enabled
    backups_enabled = settings.BACKUP_ENABLED
    
    return {
        "enabled": backups_enabled,
        "schedule": settings.BACKUP_SCHEDULE if backups_enabled else None,
        "retention_days": settings.BACKUP_RETENTION_DAYS,
        "compression_enabled": settings.BACKUP_COMPRESS,
        "verify_after_create": settings.BACKUP_VERIFY_AFTER_CREATE,
        "storage_local_path": settings.BACKUP_LOCAL_PATH,
        "storage_s3_bucket": settings.BACKUP_S3_BUCKET,
        "latest_backup": latest_backup,
        "next_scheduled_backup": _get_next_scheduled_backup() if backups_enabled else None
    }


def _get_next_scheduled_backup() -> Optional[str]:
    """Calculate next scheduled backup time based on cron schedule."""
    try:
        from croniter import croniter
        cron = settings.BACKUP_SCHEDULE
        iter = croniter(cron, datetime.utcnow())
        next_time = iter.get_next(datetime)
        return next_time.isoformat()
    except:
        return None


def _user_to_dict(user: User, include_stats: bool = False) -> dict:
    """Convert user to dict."""
    result = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
    
    if include_stats:
        result["stats"] = {
            "review_count": len(user.institution_reviews) if hasattr(user, 'institution_reviews') else 0,
            "question_count": len(user.questions) if hasattr(user, 'questions') else 0,
            "answer_count": len(user.answers) if hasattr(user, 'answers') else 0
        }
    
    return result
