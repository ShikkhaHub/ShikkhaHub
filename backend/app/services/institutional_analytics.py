"""Institutional analytics dashboard and national education insights.

Implements the "Institutional Analytics Dashboard" and "National Education
Insights" sections of the Student Data Analytics Plan.

Privacy: reports are built from anonymous event aggregates only. Institution
dashboards never expose student-identifiable data.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.student_analytics import AnalyticsEvent, StudentProfile, StudySession

logger = logging.getLogger(__name__)


class InstitutionAnalytics:
    """Per-institution analytics dashboard."""

    @staticmethod
    def get_dashboard(
        db: Session,
        institution_id: int,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Aggregate student interest and geographic/academic insights."""
        inst = db.query(Institution).get(institution_id)
        if inst is None:
            return {"error": "Institution not found"}

        cutoff = datetime.utcnow() - timedelta(days=days)

        events = (
            db.query(AnalyticsEvent)
            .filter(
                AnalyticsEvent.institution_id == institution_id,
                AnalyticsEvent.created_at >= cutoff,
            )
            .all()
        )

        # ---- Student interest breakdown ----
        event_types = Counter(ev.event_type for ev in events)
        interest = {
            "profile_views": event_types.get("institution_view", 0),
            "admission_clicks": event_types.get("admission_interest", 0)
            + event_types.get("admission_page_view", 0),
            "bookmarks": event_types.get("save_institution", 0)
            + event_types.get("bookmark", 0),
            "application_intent": event_types.get("apply_click", 0),
            "total_events": len(events),
        }
        if interest["profile_views"]:
            interest["admission_ctr"] = round(
                interest["admission_clicks"] / interest["profile_views"] * 100, 1
            )
        else:
            interest["admission_ctr"] = 0.0

        # ---- Daily interest trend ----
        daily: Dict[str, int] = defaultdict(int)
        for ev in events:
            daily[ev.created_at.date().isoformat()] += 1
        interest["daily_interest"] = [
            {"date": d, "events": c} for d, c in sorted(daily.items())
        ]

        # ---- Monthly trend (last N months) ----
        monthly = defaultdict(int)
        for ev in events:
            monthly[ev.created_at.strftime("%Y-%m")] += 1
        interest["monthly_trend"] = [
            {"month": m, "events": c} for m, c in sorted(monthly.items())
        ]

        # ---- Geographic interest (from anonymous student events) ----
        event_user_ids = list({ev.user_id for ev in events if ev.user_id is not None})
        by_division: Counter = Counter()
        by_district: Counter = Counter()
        by_upazila: Counter = Counter()
        if event_user_ids:
            profiles = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id.in_(event_user_ids))
                .all()
            )
            for p in profiles:
                if p.division:
                    by_division[p.division] += 1
                if p.district:
                    by_district[p.district] += 1
                if p.upazila:
                    by_upazila[p.upazila] += 1

        geography = {
            "by_division": [
                {"division": d, "students": c} for d, c in by_division.most_common(10)
            ],
            "by_district": [
                {"district": d, "students": c} for d, c in by_district.most_common(10)
            ],
            "by_upazila": [
                {"upazila": u, "students": c} for u, c in by_upazila.most_common(10)
            ],
        }

        # ---- Academic interest ----
        subjects = Counter(ev.subject for ev in events if ev.subject)
        popular_departments = [
            {"subject": s, "count": c} for s, c in subjects.most_common(10)
        ]

        # GPA distribution and preferred careers from interested students
        gpa_distribution: Dict[str, int] = defaultdict(int)
        preferred_careers: Counter = Counter()
        if event_user_ids:
            for p in profiles:  # type: ignore[name-defined]
                gpas = InstitutionAnalytics._extract_gpas(p.gpa_history)
                for gpa in gpas:
                    bucket = InstitutionAnalytics._gpa_bucket(gpa)
                    gpa_distribution[bucket] += 1
                if p.dream_career:
                    preferred_careers[p.dream_career] += 1

        academic = {
            "popular_departments": popular_departments,
            "popular_programs": popular_departments,
            "gpa_distribution": [
                {"bucket": b, "students": c}
                for b, c in sorted(gpa_distribution.items())
            ],
            "preferred_careers": [
                {"career": c, "students": n}
                for c, n in preferred_careers.most_common(10)
            ],
        }

        return {
            "institution_id": institution_id,
            "institution_name": inst.name_en,
            "period_days": days,
            "interest": interest,
            "geography": geography,
            "academic_interest": academic,
        }

    @staticmethod
    def _extract_gpas(gpa_history: Optional[str]) -> List[float]:
        if not gpa_history:
            return []
        try:
            data = json.loads(gpa_history)
        except (ValueError, TypeError):
            return []
        gpas = []
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    try:
                        gpas.append(float(entry.get("gpa")))
                    except (TypeError, ValueError):
                        pass
        return gpas

    @staticmethod
    def _gpa_bucket(gpa: float) -> str:
        if gpa >= 4.5:
            return "4.5+"
        if gpa >= 4.0:
            return "4.0-4.49"
        if gpa >= 3.5:
            return "3.5-3.99"
        if gpa >= 3.0:
            return "3.0-3.49"
        return "<3.0"


class NationalInsights:
    """Aggregate anonymous national education insights for administrators."""

    @staticmethod
    def get_overview(db: Session, days: int = 30) -> Dict[str, Any]:
        """National-level education intelligence dashboard."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        # ---- Most searched universities ----
        searches = (
            db.query(
                AnalyticsEvent.event_data,
            )
            .filter(
                AnalyticsEvent.event_type == "search_query",
                AnalyticsEvent.created_at >= cutoff,
                AnalyticsEvent.event_data.isnot(None),
            )
            .all()
        )

        search_texts: Counter = Counter()
        for (event_data,) in searches:
            try:
                data = json.loads(event_data)
                query = data.get("query")
                if query:
                    search_texts[str(query)] += 1
            except (ValueError, TypeError):
                continue

        most_searched = [
            {"query": q, "count": c} for q, c in search_texts.most_common(10)
        ]

        # ---- Fastest growing subjects (vs previous period) ----
        recent = (
            db.query(
                AnalyticsEvent.subject, func.count(AnalyticsEvent.id).label("count")
            )
            .filter(
                AnalyticsEvent.created_at >= cutoff,
                AnalyticsEvent.subject.isnot(None),
            )
            .group_by(AnalyticsEvent.subject)
            .all()
        )

        previous_start = cutoff - timedelta(days=days)
        previous = (
            db.query(
                AnalyticsEvent.subject, func.count(AnalyticsEvent.id).label("count")
            )
            .filter(
                AnalyticsEvent.created_at >= previous_start,
                AnalyticsEvent.created_at < cutoff,
                AnalyticsEvent.subject.isnot(None),
            )
            .group_by(AnalyticsEvent.subject)
            .all()
        )

        prev_map = {s: c for s, c in previous}
        growing = []
        for subject, count in recent:
            prev_count = prev_map.get(subject, 0)
            if prev_count > 0 and count >= 3:
                growth = (count - prev_count) / prev_count * 100
                growing.append(
                    {
                        "subject": subject,
                        "current_count": count,
                        "previous_count": prev_count,
                        "growth_percent": round(growth, 1),
                    }
                )
        growing.sort(key=lambda x: x["growth_percent"], reverse=True)
        fastest_growing_subjects = growing[:10]

        # ---- Regional education demand ----
        students = (
            db.query(StudentProfile)
            .filter(
                StudentProfile.district.isnot(None),
            )
            .all()
        )
        regional = Counter(p.district for p in students if p.district)

        regional_demand = [
            {"district": d, "students": c} for d, c in regional.most_common(10)
        ]

        # ---- Career trends ----
        careers: Counter = Counter()
        scholarship_seekers = 0
        abroad_seekers = 0
        gender_count: Counter = Counter()
        for p in students:
            if p.dream_career:
                careers[p.dream_career] += 1
            if p.scholarship_interest:
                scholarship_seekers += 1
            if p.abroad_interest:
                abroad_seekers += 1
            if p.gender:
                gender_count[p.gender] += 1

        career_trends = [
            {"career": c, "students": n} for c, n in careers.most_common(10)
        ]

        # ---- Digital learning adoption ----
        total_minutes = (
            db.query(func.coalesce(func.sum(StudySession.duration_minutes), 0))
            .filter(
                StudySession.started_at >= cutoff,
            )
            .scalar()
            or 0
        )

        learning_students = (
            db.query(func.count(func.distinct(StudySession.user_id)))
            .filter(
                StudySession.started_at >= cutoff,
            )
            .scalar()
            or 0
        )

        # ---- Gender participation ----
        gender_participation = [
            {"gender": g, "students": c} for g, c in gender_count.items()
        ]

        total_students = len(students)

        return {
            "period_days": days,
            "most_searched_universities": most_searched,
            "fastest_growing_subjects": fastest_growing_subjects,
            "regional_demand": regional_demand,
            "career_trends": career_trends,
            "scholarship_demand": scholarship_seekers,
            "abroad_interest": abroad_seekers,
            "digital_learning": {
                "active_learners": learning_students,
                "total_study_minutes": total_minutes,
            },
            "gender_participation": gender_participation,
            "total_student_profiles": total_students,
        }
