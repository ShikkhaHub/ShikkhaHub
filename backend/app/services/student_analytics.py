"""Student analytics service.

Implements the core of the ShikkhaHub Student Data Analytics Plan:
- Event tracking (every important platform action -> AnalyticsEvent)
- Student 360 profile management
- AI student profile generation (rule-based, cached on the profile)
- Student segmentation (dynamic groups)
- Learning analytics (time, streaks, quiz accuracy, subject performance)
- Behavioral analytics (global aggregates for admin/national insights)
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.models.analytics import SearchEvent, PageView
from app.models.institution import Institution
from app.models.student_analytics import (
    AnalyticsEvent,
    ConsentRecord,
    StudentProfile,
    StudySession,
)
from app.models.user import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event constants (mapped from the analytics plan)
# ---------------------------------------------------------------------------

EVENT_INSTITUTION_SEARCH = "search_query"
EVENT_INSTITUTION_VIEW = "institution_view"
EVENT_ADMISSION_VIEW = "admission_page_view"
EVENT_ADMISSION_INTEREST = "admission_interest"
EVENT_SAVE_INSTITUTION = "save_institution"
EVENT_COURSE_VIEW = "course_view"
EVENT_VIDEO_WATCH = "video_watch"
EVENT_PDF_READ = "pdf_read"
EVENT_AI_CHAT = "ai_chat"
EVENT_CAREER_ASSISTANT = "career_assistant_usage"
EVENT_BOOKMARK = "bookmark"
EVENT_DOWNLOAD = "download"
EVENT_SHARE = "share"
EVENT_COMMENT = "comment"
EVENT_REVIEW = "review"
EVENT_SCHOLARSHIP_VIEW = "scholarship_view"
EVENT_APPLY_CLICK = "apply_click"
EVENT_COURSE_COMPLETE = "course_complete"

# ---------------------------------------------------------------------------
# Student segments (from the plan)
# ---------------------------------------------------------------------------

SEGMENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "ssc_students": {
        "label": "SSC Students",
        "desc": "Students currently studying in secondary level",
        "match_levels": ["SSC", "Secondary"],
    },
    "hsc_students": {
        "label": "HSC Students",
        "desc": "Students currently studying in higher secondary level",
        "match_levels": ["HSC", "Higher Secondary"],
    },
    "university_students": {
        "label": "University Students",
        "desc": "Students enrolled in undergraduate or postgraduate programs",
        "match_levels": ["University", "Masters", "Honours"],
    },
    "admission_candidates": {
        "label": "Admission Candidates",
        "desc": "Students showing strong admission interest (views, saves, clicks)",
        "min_interest_events": 3,
    },
    "job_seekers": {
        "label": "Job Seekers",
        "desc": "Students focused on careers and employment",
        "sectors_any": [
            "IT",
            "Software",
            "Bank",
            "Government",
            "Job",
            "Finance",
            "Engineering",
        ],
    },
    "scholarship_seekers": {
        "label": "Scholarship Seekers",
        "desc": "Students interested in scholarships and financial aid",
        "flag": "scholarship_interest",
    },
    "engineering_aspirants": {
        "label": "Engineering Aspirants",
        "desc": "Students aspiring to engineering programs",
        "subjects_any": ["Engineering", "CSE", "EEE", "Mechanical", "Civil", "ECE"],
    },
    "medical_aspirants": {
        "label": "Medical Aspirants",
        "desc": "Students aspiring to medical programs",
        "subjects_any": ["Medical", "MBBS", "BDS", "Pharmacy", "Nursing"],
    },
    "bcs_aspirants": {
        "label": "BCS Aspirants",
        "desc": "Students preparing for the Bangladesh Civil Service",
        "careers_any": ["BCS", "Civil Service", "Government Officer"],
    },
    "study_abroad_students": {
        "label": "Study Abroad Students",
        "desc": "Students interested in studying abroad",
        "flag": "abroad_interest",
    },
}


# ---------------------------------------------------------------------------
# Behavioral analytics data classes
# ---------------------------------------------------------------------------


@dataclass
class BehavioralSnapshot:
    """Global behavioral analytics snapshot for a time period."""

    period_days: int
    most_viewed_institutions: List[Dict[str, Any]] = field(default_factory=list)
    popular_subjects: List[Dict[str, Any]] = field(default_factory=list)
    search_trends: List[Dict[str, Any]] = field(default_factory=list)
    peak_study_hours: List[Dict[str, Any]] = field(default_factory=list)
    most_active_districts: List[Dict[str, Any]] = field(default_factory=list)
    avg_session_duration_seconds: float = 0.0
    bounce_rate: float = 0.0
    return_rate: float = 0.0
    ai_usage_frequency: int = 0
    total_events: int = 0
    active_students: int = 0


class EventTracker:
    """Track generic analytics events with consent-aware privacy."""

    @staticmethod
    def track_event(
        db: Session,
        event_type: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        institution_id: Optional[int] = None,
        course_id: Optional[int] = None,
        subject: Optional[str] = None,
        page_path: Optional[str] = None,
        source: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AnalyticsEvent:
        """Record an analytics event.

        Privacy: if the student has not granted analytics consent, the event
        is stored as anonymous (not tied to a user identity) so that no
        personal data is retained without explicit consent.
        """
        is_anonymous = False
        if user_id is not None:
            profile = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .first()
            )
            if profile is None or not profile.analytics_consent:
                is_anonymous = True
                user_id = None

        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            institution_id=institution_id,
            course_id=course_id,
            subject=subject,
            page_path=page_path[:500] if page_path else None,
            source=source,
            event_data=json.dumps(event_data) if event_data else None,
            duration_seconds=duration_seconds,
            is_anonymous=is_anonymous,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def track_study_session(
        db: Session,
        user_id: int,
        subject: Optional[str] = None,
        course_id: Optional[int] = None,
        duration_minutes: int = 0,
        lessons_completed: int = 0,
        quiz_accuracy: Optional[float] = None,
        average_score: Optional[float] = None,
        content_type: Optional[str] = None,
    ) -> StudySession:
        """Record a study/learning session."""
        session = StudySession(
            user_id=user_id,
            subject=subject,
            course_id=course_id,
            session_date=date.today(),
            duration_minutes=duration_minutes,
            lessons_completed=lessons_completed,
            quiz_accuracy=quiz_accuracy,
            average_score=average_score,
            content_type=content_type,
            started_at=datetime.utcnow(),
            ended_at=datetime.utcnow(),
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


class ConsentService:
    """Manage and audit analytics consent (privacy governance)."""

    @staticmethod
    def set_consent(
        db: Session,
        user: User,
        granted: bool,
        consent_type: str = "analytics",
        consent_version: str = "1.0",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> StudentProfile:
        """Grant or revoke analytics consent and record the audit entry."""
        profile = StudentProfileService.get_or_create(db, user)

        if consent_type == "analytics":
            profile.analytics_consent = granted
            profile.analytics_consent_at = datetime.utcnow() if granted else None

        db.add(
            ConsentRecord(
                user_id=user.id,
                consent_type=consent_type,
                granted=granted,
                consent_version=consent_version,
                ip_address=ip_address,
                user_agent=user_agent[:500] if user_agent else None,
            )
        )
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_history(db: Session, user: User) -> List[Dict[str, Any]]:
        """Return the full consent history for a student."""
        records = (
            db.query(ConsentRecord)
            .filter(ConsentRecord.user_id == user.id)
            .order_by(ConsentRecord.created_at.desc())
            .all()
        )

        return [
            {
                "consent_type": r.consent_type,
                "granted": r.granted,
                "consent_version": r.consent_version,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]


class StudentProfileService:
    """Manage the Student 360 profile and AI profile generation."""

    @staticmethod
    def get_or_create(db: Session, user: User) -> StudentProfile:
        profile = (
            db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        )
        if profile is None:
            profile = StudentProfile(
                user_id=user.id,
                full_name=user.full_name,
                language_preference=user.preferred_language,
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update(db: Session, user: User, data: Dict[str, Any]) -> StudentProfile:
        """Update the student profile with any subset of allowed fields."""
        profile = StudentProfileService.get_or_create(db, user)
        json_fields = {
            "gpa_history",
            "academic_interests",
            "interested_sectors",
            "favorite_subjects",
            "weak_subjects",
            "completed_courses",
            "exam_preparation",
        }

        for key, value in data.items():
            if not hasattr(profile, key):
                continue
            if value is None:
                continue
            if key in json_fields and not isinstance(value, str):
                value = json.dumps(value)
            setattr(profile, key, value)

        # Mirror name to the user record when provided
        if data.get("full_name") and not user.full_name:
            parts = data["full_name"].split(" ", 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else None

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def _parse_json_list(value: Optional[str]) -> List[Any]:
        if not value:
            return []
        try:
            data = json.loads(value)
            if isinstance(data, list):
                return data
            return []
        except (ValueError, TypeError):
            return []

    @staticmethod
    def _parse_json_obj(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        try:
            data = json.loads(value)
            if isinstance(data, dict):
                return data
            return {}
        except (ValueError, TypeError):
            return {}

    @staticmethod
    def build_ai_profile(
        db: Session, user: User, force: bool = False
    ) -> StudentProfile:
        """Generate (or refresh) the AI student profile and cache it.

        Produces: student type, learning style, strong/weak subjects,
        interested universities, career goal, risk score and
        recommendation score. Rule-based so it works offline; designed
        to be replaced by an ML model in a later phase.
        """
        profile = StudentProfileService.get_or_create(db, user)
        if profile.ai_profile and not force:
            return profile

        events = (
            db.query(AnalyticsEvent)
            .filter(AnalyticsEvent.user_id == user.id)
            .order_by(AnalyticsEvent.created_at.desc())
            .limit(300)
            .all()
        )

        subjects_seen = Counter()
        universities_seen = Counter()
        event_types = Counter()
        for ev in events:
            event_types[ev.event_type] += 1
            if ev.subject:
                subjects_seen[ev.subject] += 1
            if ev.institution_id:
                inst = db.query(Institution).get(ev.institution_id)
                if inst:
                    universities_seen[inst.name_en] += 1

        # --- Student type ---
        student_type = StudentProfileService._infer_student_type(profile, event_types)

        # --- Learning style ---
        learning_style = profile.learning_style or "Visual Learner"

        # --- Strong / weak subjects ---
        favorites = StudentProfileService._parse_json_list(profile.favorite_subjects)
        weak = StudentProfileService._parse_json_list(profile.weak_subjects)
        strong_subjects = list(favorites) + [s for s, _ in subjects_seen.most_common(3)]
        # de-duplicate while preserving order
        strong_subjects = list(dict.fromkeys(strong_subjects))[:5]

        # --- Interested universities ---
        preferred = (
            [profile.preferred_university] if profile.preferred_university else []
        )
        interested_universities = list(
            dict.fromkeys(preferred + [u for u, _ in universities_seen.most_common(3)])
        )[:5]

        # --- Career goal ---
        career_goal = profile.dream_career or None

        # --- Risk score (rule-based heuristic) ---
        risk_score = StudentProfileService._compute_risk_score(profile, event_types)

        # --- Recommendation score (0-100 heuristic) ---
        recommendation_score = StudentProfileService._compute_recommendation_score(
            profile, event_types
        )

        ai_profile = {
            "student_type": student_type,
            "learning_style": learning_style,
            "strong_subjects": strong_subjects,
            "weak_subjects": weak,
            "interested_universities": interested_universities,
            "career_goal": career_goal,
            "risk_score": risk_score,
            "recommendation_score": recommendation_score,
        }

        profile.student_type = student_type
        profile.learning_style = learning_style
        profile.strong_subjects = json.dumps(strong_subjects)
        profile.interested_universities = json.dumps(interested_universities)
        profile.risk_score = risk_score
        profile.recommendation_score = recommendation_score
        profile.ai_profile = json.dumps(ai_profile)
        profile.ai_profile_generated_at = datetime.utcnow()

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def _infer_student_type(profile: StudentProfile, event_types: Counter) -> str:
        """Infer the primary student type from profile + behavior."""
        level = (profile.current_level or "").lower()
        level_map = {
            "ssc": "SSC Student",
            "secondary": "SSC Student",
            "hsc": "HSC Student",
            "higher secondary": "HSC Student",
            "diploma": "Diploma Student",
            "university": "University Student",
            "honours": "University Student",
            "masters": "University Student",
        }
        for key, label in level_map.items():
            if key in level:
                base_type = label
                break
        else:
            base_type = "General Learner"

        admission_signal = (
            event_types.get("admission_interest", 0)
            + event_types.get("admission_page_view", 0)
            + event_types.get("save_institution", 0)
        )
        profile_admission_signal = bool(
            profile.preferred_university
            or (profile.preferred_subject and profile.gpa_history)
        )
        if admission_signal >= 3 or profile_admission_signal:
            return "Admission Focused"

        career_signal = event_types.get("career_assistant_usage", 0)
        if career_signal >= 2 or profile.dream_career:
            return "Career Focused"

        study_signal = event_types.get("course_complete", 0) + event_types.get(
            "video_watch", 0
        )
        if study_signal >= 5:
            return "Active Learner"

        return base_type

    @staticmethod
    def _compute_risk_score(profile: StudentProfile, event_types: Counter) -> str:
        """Low/Medium/High risk of inactivity or poor outcomes."""
        total_engagement = sum(event_types.values())
        has_academic_data = bool(
            profile.current_level or profile.gpa_history or profile.current_institution
        )

        risk_points = 0
        # High study volume reduces risk
        if total_engagement < 3:
            risk_points += 2
        elif total_engagement < 10:
            risk_points += 1

        # Incomplete academic profile increases risk
        if not has_academic_data:
            risk_points += 1

        if risk_points >= 2:
            return "High"
        if risk_points == 1:
            return "Medium"
        return "Low"

    @staticmethod
    def _compute_recommendation_score(
        profile: StudentProfile, event_types: Counter
    ) -> float:
        """Heuristic 0-100 recommendation readiness score."""
        score = 40.0

        if profile.current_level:
            score += 10
        if profile.gpa_history:
            score += 10
        if profile.dream_career or profile.preferred_subject:
            score += 10
        if profile.preferred_university:
            score += 5
        if profile.scholarship_interest or profile.abroad_interest:
            score += 5

        # Engagement adds up to 20 points
        engagement = sum(event_types.values())
        score += min(20, engagement)

        return round(min(100, max(0, score)), 1)


class StudentSegmenter:
    """Dynamically group students into segments."""

    @staticmethod
    def _parse_json_list(value: Optional[str]) -> List[str]:
        if not value:
            return []
        try:
            data = json.loads(value)
            return [str(x) for x in data] if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @classmethod
    def segment(cls, db: Session, user: User) -> List[Dict[str, str]]:
        """Return all segments a student currently belongs to."""
        profile = StudentProfileService.get_or_create(db, user)
        segments: List[Dict[str, str]] = []

        level = (profile.current_level or "").lower()

        for key, definition in SEGMENT_DEFINITIONS.items():
            label = definition["label"]
            match = False

            if "match_levels" in definition:
                match = any(m.lower() in level for m in definition["match_levels"])

            if "flag" in definition:
                flag = definition["flag"]
                flag_value = getattr(profile, flag, False)
                if flag_value:
                    match = True

            if "min_interest_events" in definition:
                interest_events = (
                    db.query(AnalyticsEvent)
                    .filter(
                        AnalyticsEvent.user_id == user.id,
                        AnalyticsEvent.event_type.in_(
                            [
                                "admission_interest",
                                "admission_page_view",
                                "save_institution",
                            ]
                        ),
                    )
                    .count()
                )
                profile_signal = bool(
                    profile.preferred_university
                    or (profile.preferred_subject and profile.gpa_history)
                )
                if (
                    interest_events >= definition["min_interest_events"]
                    or profile_signal
                ):
                    match = True

            if "sectors_any" in definition:
                sectors = cls._parse_json_list(profile.interested_sectors)
                if any(
                    s.lower() in " ".join(sectors).lower()
                    for s in definition["sectors_any"]
                ):
                    match = True

            if "subjects_any" in definition:
                subjects = (
                    cls._parse_json_list(profile.academic_interests)
                    + cls._parse_json_list(profile.favorite_subjects)
                    + cls._parse_json_list(profile.strong_subjects)
                )
                if any(
                    s.lower() in " ".join(subjects).lower()
                    for s in definition["subjects_any"]
                ):
                    match = True

            if "careers_any" in definition:
                career = profile.dream_career or ""
                if any(c.lower() in career.lower() for c in definition["careers_any"]):
                    match = True

            if match:
                segments.append(
                    {"key": key, "label": label, "description": definition["desc"]}
                )

        return segments


class LearningAnalytics:
    """Aggregate learning behavior for a student."""

    @staticmethod
    def get_student_learning(db: Session, user: User, days: int = 30) -> Dict[str, Any]:
        """Learning analytics: time, lessons, accuracy, streak, subject breakdown."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        sessions = (
            db.query(StudySession)
            .filter(
                StudySession.user_id == user.id,
                StudySession.started_at >= cutoff,
            )
            .all()
        )

        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        total_lessons = sum(s.lessons_completed or 0 for s in sessions)

        accuracies = [s.quiz_accuracy for s in sessions if s.quiz_accuracy is not None]
        avg_accuracy = (
            round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0
        )

        scores = [s.average_score for s in sessions if s.average_score is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        # Subject performance
        subject_totals: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "minutes": 0,
                "lessons": 0,
                "sessions": 0,
                "accuracies": [],
                "scores": [],
            }
        )
        for s in sessions:
            subject = s.subject or "General"
            bucket = subject_totals[subject]
            bucket["minutes"] += s.duration_minutes or 0
            bucket["lessons"] += s.lessons_completed or 0
            bucket["sessions"] += 1
            if s.quiz_accuracy is not None:
                bucket["accuracies"].append(s.quiz_accuracy)
            if s.average_score is not None:
                bucket["scores"].append(s.average_score)

        subject_performance = []
        for subject, data in subject_totals.items():
            subject_performance.append(
                {
                    "subject": subject,
                    "minutes": data["minutes"],
                    "lessons": data["lessons"],
                    "sessions": data["sessions"],
                    "avg_accuracy": (
                        round(sum(data["accuracies"]) / len(data["accuracies"]), 1)
                        if data["accuracies"]
                        else 0.0
                    ),
                    "avg_score": (
                        round(sum(data["scores"]) / len(data["scores"]), 1)
                        if data["scores"]
                        else 0.0
                    ),
                }
            )
        subject_performance.sort(key=lambda x: x["minutes"], reverse=True)

        # Daily learning time for charting
        daily_minutes: Dict[str, int] = defaultdict(int)
        for s in sessions:
            day = s.session_date.isoformat()
            daily_minutes[day] += s.duration_minutes or 0

        return {
            "period_days": days,
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "total_lessons": total_lessons,
            "avg_quiz_accuracy": avg_accuracy,
            "avg_score": avg_score,
            "active_days": len(daily_minutes),
            "learning_streak": LearningAnalytics._compute_streak(db, user),
            "daily_minutes": [
                {"date": day, "minutes": mins}
                for day, mins in sorted(daily_minutes.items())
            ],
            "subject_performance": subject_performance,
        }

    @staticmethod
    def _compute_streak(db: Session, user: User) -> int:
        """Current consecutive-day learning streak."""
        days = (
            db.query(distinct(StudySession.session_date))
            .filter(StudySession.user_id == user.id)
            .order_by(StudySession.session_date.desc())
            .all()
        )
        if not days:
            return 0

        day_set = {d[0] for d in days}
        streak = 0
        current = date.today()
        # Allow today to count even if not yet completed
        if current not in day_set:
            current -= timedelta(days=1)
        while current in day_set:
            streak += 1
            current -= timedelta(days=1)
        return streak


class BehavioralAnalytics:
    """Aggregate anonymous behavioral analytics across the platform."""

    @staticmethod
    def get_snapshot(db: Session, days: int = 30) -> BehavioralSnapshot:
        """Platform-wide behavioral snapshot for admin/national insights."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # ---- Most viewed institutions ----
        views = (
            db.query(
                AnalyticsEvent.institution_id,
                func.count(AnalyticsEvent.id).label("count"),
            )
            .filter(
                AnalyticsEvent.event_type == EVENT_INSTITUTION_VIEW,
                AnalyticsEvent.created_at >= cutoff,
                AnalyticsEvent.institution_id.isnot(None),
            )
            .group_by(AnalyticsEvent.institution_id)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(10)
            .all()
        )

        most_viewed = []
        for inst_id, count in views:
            inst = db.query(Institution).get(inst_id)
            most_viewed.append(
                {
                    "institution_id": inst_id,
                    "name": inst.name_en if inst else "Unknown",
                    "views": count,
                }
            )

        # ---- Popular subjects ----
        subjects = (
            db.query(
                AnalyticsEvent.subject, func.count(AnalyticsEvent.id).label("count")
            )
            .filter(
                AnalyticsEvent.created_at >= cutoff,
                AnalyticsEvent.subject.isnot(None),
            )
            .group_by(AnalyticsEvent.subject)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(10)
            .all()
        )
        popular_subjects = [{"subject": s, "count": c} for s, c in subjects]

        # ---- Search trends ----
        searches = (
            db.query(SearchEvent.query, func.count(SearchEvent.id).label("count"))
            .filter(
                SearchEvent.created_at >= cutoff,
            )
            .group_by(SearchEvent.query)
            .order_by(func.count(SearchEvent.id).desc())
            .limit(10)
            .all()
        )
        search_trends = [{"query": q, "count": c} for q, c in searches]

        # ---- Peak study hours (portable across SQLite & Postgres) ----
        hours = (
            db.query(
                func.extract("hour", StudySession.started_at).label("hour"),
                func.count(StudySession.id).label("count"),
            )
            .filter(
                StudySession.started_at >= cutoff,
            )
            .group_by("hour")
            .order_by(func.count(StudySession.id).desc())
            .limit(8)
            .all()
        )
        peak_study_hours = [{"hour": h, "count": c} for h, c in hours]

        # ---- Most active districts (from student profiles) ----
        districts = (
            db.query(
                StudentProfile.district, func.count(StudentProfile.id).label("count")
            )
            .filter(
                StudentProfile.district.isnot(None),
            )
            .group_by(StudentProfile.district)
            .order_by(func.count(StudentProfile.id).desc())
            .limit(10)
            .all()
        )
        most_active_districts = [{"district": d, "students": c} for d, c in districts]

        # ---- Session duration / bounce / return ----
        page_views = db.query(PageView).filter(PageView.created_at >= cutoff).all()
        sessions = Counter(pv.session_id for pv in page_views if pv.session_id)

        avg_duration = 0.0
        durations = [
            pv.time_on_page_seconds for pv in page_views if pv.time_on_page_seconds
        ]
        if durations:
            avg_duration = round(sum(durations) / len(durations), 1)

        single_view_sessions = sum(1 for c in sessions.values() if c == 1)
        bounce_rate = (
            round(single_view_sessions / len(sessions) * 100, 1) if sessions else 0.0
        )

        return_rate = 0.0
        if sessions:
            returning = sum(1 for c in sessions.values() if c > 1)
            return_rate = round(returning / len(sessions) * 100, 1)

        # ---- AI usage ----
        ai_usage = (
            db.query(AnalyticsEvent)
            .filter(
                AnalyticsEvent.event_type.in_([EVENT_AI_CHAT, EVENT_CAREER_ASSISTANT]),
                AnalyticsEvent.created_at >= cutoff,
            )
            .count()
        )

        total_events = (
            db.query(AnalyticsEvent)
            .filter(
                AnalyticsEvent.created_at >= cutoff,
            )
            .count()
        )

        active_students = (
            db.query(distinct(AnalyticsEvent.user_id))
            .filter(
                AnalyticsEvent.created_at >= cutoff,
                AnalyticsEvent.user_id.isnot(None),
            )
            .count()
        )

        return BehavioralSnapshot(
            period_days=days,
            most_viewed_institutions=most_viewed,
            popular_subjects=popular_subjects,
            search_trends=search_trends,
            peak_study_hours=peak_study_hours,
            most_active_districts=most_active_districts,
            avg_session_duration_seconds=avg_duration,
            bounce_rate=bounce_rate,
            return_rate=return_rate,
            ai_usage_frequency=ai_usage,
            total_events=total_events,
            active_students=active_students,
        )
