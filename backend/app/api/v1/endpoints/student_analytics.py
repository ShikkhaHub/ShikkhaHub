"""Student analytics API endpoints.

Implements the Student Data Analytics Plan API surface:
- Event tracking (generic + study sessions)
- Student 360 profile management
- AI student profile
- Learning analytics
- Segmentation
- Recommendations (institution / course / scholarship)
- Institutional analytics dashboards (admin / authorized)
- National education insights (admin)
- Behavioral analytics (admin)
- Consent & privacy management
"""

from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    get_current_user,
    get_current_user_optional,
    get_current_admin_user,
)
from app.models.user import User
from app.services.student_analytics import (
    BehavioralAnalytics,
    ConsentService,
    EventTracker,
    LearningAnalytics,
    StudentProfileService,
    StudentSegmenter,
)
from app.services.recommendations import (
    CourseRecommender,
    InstitutionRecommender,
    ScholarshipRecommender,
)
from app.services.institutional_analytics import InstitutionAnalytics, NationalInsights

router = APIRouter()


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class StudentProfileUpdate(BaseModel):
    """Any subset of student profile fields (see StudentProfile model)."""

    full_name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    profile_picture_url: Optional[str] = None

    current_level: Optional[str] = None
    education_board: Optional[str] = None
    current_institution: Optional[str] = None
    department: Optional[str] = None
    session: Optional[str] = None
    expected_graduation: Optional[str] = None
    gpa_history: Optional[List[Dict[str, Any]]] = None
    academic_interests: Optional[List[str]] = None

    division: Optional[str] = None
    district: Optional[str] = None
    upazila: Optional[str] = None
    area: Optional[str] = None
    current_location: Optional[str] = None

    dream_career: Optional[str] = None
    interested_sectors: Optional[List[str]] = None
    preferred_university: Optional[str] = None
    preferred_subject: Optional[str] = None
    expected_salary: Optional[int] = None
    abroad_interest: Optional[bool] = None
    scholarship_interest: Optional[bool] = None
    annual_income: Optional[int] = None
    disability: Optional[str] = None

    favorite_subjects: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None
    completed_courses: Optional[List[str]] = None
    study_hours_per_week: Optional[int] = None
    learning_style: Optional[str] = None
    language_preference: Optional[str] = None
    exam_preparation: Optional[Dict[str, Any]] = None
    weekly_study_target_minutes: Optional[int] = None


class TrackEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    session_id: Optional[str] = None
    institution_id: Optional[int] = None
    course_id: Optional[int] = None
    subject: Optional[str] = None
    page_path: Optional[str] = None
    source: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None
    duration_seconds: Optional[int] = None


class TrackStudyRequest(BaseModel):
    subject: Optional[str] = None
    course_id: Optional[int] = None
    duration_minutes: int = 0
    lessons_completed: int = 0
    quiz_accuracy: Optional[float] = Field(None, ge=0, le=100)
    average_score: Optional[float] = Field(None, ge=0, le=100)
    content_type: Optional[str] = None


class ConsentRequest(BaseModel):
    granted: bool
    consent_type: str = "analytics"
    consent_version: str = "1.0"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_session_id(request: Request) -> str:
    """Get or generate a session ID."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        import hashlib

        data = f"{get_client_ip(request)}:{request.headers.get('user-agent', '')}"
        session_id = hashlib.md5(data.encode()).hexdigest()[:16]
    return session_id


def _serialize_profile(profile) -> Dict[str, Any]:
    """Serialize a StudentProfile into a JSON-friendly dict."""
    data = {}
    for col in profile.__table__.columns:
        value = getattr(profile, col.name)
        if isinstance(value, (date,)):
            data[col.name] = value.isoformat()
        else:
            data[col.name] = value
    # Decode JSON fields for the API
    for field_name in [
        "gpa_history",
        "academic_interests",
        "interested_sectors",
        "favorite_subjects",
        "weak_subjects",
        "completed_courses",
        "exam_preparation",
        "strong_subjects",
        "interested_universities",
        "ai_profile",
    ]:
        if isinstance(data.get(field_name), str):
            try:
                import json

                data[field_name] = json.loads(data[field_name])
            except (ValueError, TypeError):
                pass
    return data


# ---------------------------------------------------------------------------
# Consent & privacy
# ---------------------------------------------------------------------------


@router.post("/students/consent")
def set_consent(
    data: ConsentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Grant or revoke analytics consent (privacy governance)."""
    profile = ConsentService.set_consent(
        db=db,
        user=current_user,
        granted=data.granted,
        consent_type=data.consent_type,
        consent_version=data.consent_version,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "success": True,
        "analytics_consent": profile.analytics_consent,
        "history": ConsentService.get_history(db, current_user),
    }


@router.get("/students/consent/history")
def consent_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the student's consent history."""
    return {"history": ConsentService.get_history(db, current_user)}


# ---------------------------------------------------------------------------
# Student profile & 360 dashboard
# ---------------------------------------------------------------------------


@router.post("/students/profile")
def update_student_profile(
    data: StudentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update the student's 360 profile."""
    profile = StudentProfileService.update(
        db, current_user, data.model_dump(exclude_none=True)
    )
    return {"success": True, "profile": _serialize_profile(profile)}


@router.get("/students/me/profile")
def get_student_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the student's profile (creates it if missing)."""
    profile = StudentProfileService.get_or_create(db, current_user)
    return {"profile": _serialize_profile(profile)}


@router.get("/students/me")
def get_student_360(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Student 360 dashboard: profile + AI profile + segments + learning."""
    profile = StudentProfileService.build_ai_profile(db, current_user)
    segments = StudentSegmenter.segment(db, current_user)
    learning = LearningAnalytics.get_student_learning(db, current_user, days=30)

    return {
        "profile": _serialize_profile(profile),
        "ai_profile": {
            "student_type": profile.student_type,
            "learning_style": profile.learning_style,
            "strong_subjects": StudentProfileService._parse_json_list(
                profile.strong_subjects
            ),
            "weak_subjects": StudentProfileService._parse_json_list(
                profile.weak_subjects
            ),
            "interested_universities": StudentProfileService._parse_json_list(
                profile.interested_universities
            ),
            "career_goal": profile.dream_career,
            "risk_score": profile.risk_score,
            "recommendation_score": profile.recommendation_score,
        },
        "segments": segments,
        "learning": learning,
        "analytics_consent": profile.analytics_consent,
    }


@router.get("/students/me/segments")
def get_student_segments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the dynamic segments the student belongs to."""
    return {"segments": StudentSegmenter.segment(db, current_user)}


@router.get("/students/me/learning")
def get_learning_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Learning analytics for the current student."""
    return LearningAnalytics.get_student_learning(db, current_user, days=days)


@router.get("/students/me/ai-profile")
def get_ai_profile(
    refresh: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the AI-generated student profile."""
    profile = StudentProfileService.build_ai_profile(db, current_user, force=refresh)
    return _serialize_profile(profile)


# ---------------------------------------------------------------------------
# Event tracking
# ---------------------------------------------------------------------------


@router.post("/analytics/track/event")
def track_event(
    data: TrackEventRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    user_agent: Optional[str] = Header(None),
):
    """Track a generic platform event (e.g. search_query, institution_view).

    Events from students without analytics consent are stored anonymously.
    """
    try:
        event = EventTracker.track_event(
            db=db,
            event_type=data.event_type,
            user_id=current_user.id if current_user else None,
            session_id=data.session_id or get_session_id(request),
            institution_id=data.institution_id,
            course_id=data.course_id,
            subject=data.subject,
            page_path=data.page_path,
            source=data.source,
            event_data=data.event_data,
            duration_seconds=data.duration_seconds,
            ip_address=get_client_ip(request),
            user_agent=user_agent,
        )
        return {
            "success": True,
            "event_id": event.id,
            "is_anonymous": event.is_anonymous,
        }
    except Exception as e:  # noqa: BLE001 - analytics must never break UX
        return {"success": False, "error": str(e)}


@router.post("/analytics/track/study")
def track_study_session(
    data: TrackStudyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track a completed study/learning session."""
    session = EventTracker.track_study_session(
        db=db,
        user_id=current_user.id,
        subject=data.subject,
        course_id=data.course_id,
        duration_minutes=data.duration_minutes,
        lessons_completed=data.lessons_completed,
        quiz_accuracy=data.quiz_accuracy,
        average_score=data.average_score,
        content_type=data.content_type,
    )
    return {"success": True, "study_session_id": session.id}


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


@router.get("/students/me/recommendations/institutions")
def recommend_institutions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized institution recommendations (safety/competitive/dream)."""
    return InstitutionRecommender.recommend(db, current_user)


@router.get("/students/me/recommendations/courses")
def recommend_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized course recommendations."""
    return CourseRecommender.recommend(db, current_user)


@router.get("/students/me/recommendations/scholarships")
def recommend_scholarships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get personalized scholarship recommendations."""
    return ScholarshipRecommender.recommend(db, current_user)


@router.get("/students/me/recommendations")
def get_all_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all recommendation types for the student 360 dashboard."""
    return {
        "institutions": InstitutionRecommender.recommend(db, current_user),
        "courses": CourseRecommender.recommend(db, current_user),
        "scholarships": ScholarshipRecommender.recommend(db, current_user),
    }


# ---------------------------------------------------------------------------
# Institutional dashboards & national insights (admin / authorized)
# ---------------------------------------------------------------------------


@router.get("/institutions/{institution_id}/analytics")
def get_institution_analytics(
    institution_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Institution analytics dashboard (admin only in Phase 1)."""
    dashboard = InstitutionAnalytics.get_dashboard(db, institution_id, days=days)
    if "error" in dashboard:
        raise HTTPException(status_code=404, detail=dashboard["error"])
    return dashboard


@router.get("/admin/analytics/national-insights")
def get_national_insights(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """National education insights (admin)."""
    return NationalInsights.get_overview(db, days=days)


@router.get("/admin/analytics/behavioral")
def get_behavioral_analytics(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Platform-wide behavioral analytics (admin)."""
    return {"snapshot": BehavioralAnalytics.get_snapshot(db, days=days).__dict__}
