"""Recommendation engine for the ShikkhaHub Student Data Analytics Plan.

Provides:
- InstitutionRecommendation: best match / safety / competitive / dream universities
- CourseRecommendation: based on history, interests, career, learning behavior
- ScholarshipRecommendation: based on income, academics, location, gender, disability, merit

Phase 1 uses interpretable rule/weight-based scoring that can be replaced by
machine-learned models in Phase 3 while keeping the same API contract.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.institution import Institution, InstitutionRequirement
from app.models.student_analytics import AnalyticsEvent, StudentProfile
from app.models.user import User

logger = logging.getLogger(__name__)


class ProfileReader:
    """Helper to safely read JSON/typed fields from a student profile."""

    @staticmethod
    def json_list(value: Optional[str]) -> List[str]:
        if not value:
            return []
        try:
            data = json.loads(value)
            return [str(x) for x in data] if isinstance(data, list) else []
        except (ValueError, TypeError):
            return []

    @staticmethod
    def json_obj(value: Optional[str]) -> Dict[str, Any]:
        if not value:
            return {}
        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else {}
        except (ValueError, TypeError):
            return {}


class InstitutionRecommender:
    """Recommend institutions based on the student's profile and behavior."""

    # Subject -> keyword hints used to match institutions
    SUBJECT_KEYWORDS: Dict[str, List[str]] = {
        "Engineering": [
            "engineering",
            "cse",
            "computer",
            "eee",
            "mechanical",
            "civil",
            "ece",
            "textile",
        ],
        "CSE": ["cse", "computer science", "computer", "it", "ict"],
        "EEE": ["eee", "electrical", "electronics"],
        "Medical": ["medical", "mbbs", "bds", "dental", "pharmacy", "nursing"],
        "Business": ["business", "bba", "mba", "management", "commerce", "accounting"],
        "Law": ["law", "legal"],
        "Agriculture": ["agriculture", "agri"],
        "Arts": ["arts", "liberal", "humanities", "bangla", "english literature"],
        "Science": ["science", "physics", "chemistry", "math", "biology"],
    }

    @staticmethod
    def _get_user_gpa(profile: StudentProfile, level: str) -> Optional[float]:
        """Extract GPA for a given level (SSC/HSC) from gpa_history JSON."""
        history = ProfileReader.json_list(profile.gpa_history)
        for entry in history:
            if isinstance(entry, dict) and entry.get("level"):
                if level.lower() in str(entry.get("level")).lower():
                    try:
                        return float(entry.get("gpa"))
                    except (TypeError, ValueError):
                        return None
        return None

    @staticmethod
    def _extract_subject_keywords(profile: StudentProfile) -> List[str]:
        """Gather subject keywords from interests, career, and favorite subjects."""
        keywords = []
        interests = ProfileReader.json_list(
            profile.academic_interests
        ) + ProfileReader.json_list(profile.favorite_subjects)
        if profile.dream_career:
            interests.append(profile.dream_career)
        if profile.preferred_subject:
            interests.append(profile.preferred_subject)

        for interest in interests:
            lowered = interest.lower()
            for subject, hints in InstitutionRecommender.SUBJECT_KEYWORDS.items():
                if subject.lower() in lowered or any(h in lowered for h in hints):
                    keywords.extend(hints)
        return list(set(keywords))

    @classmethod
    def recommend(
        cls,
        db: Session,
        user: User,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Recommend institutions split into safety / competitive / dream tiers.

        Inputs (from profile): location, SSC/HSC GPA, preferred subject,
        career goal. Heuristic tiering uses the institution's minimum GPA
        requirement (when present) and the student's admission readiness.
        """
        profile = (
            db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        )
        if profile is None:
            return {"best_matches": [], "safety": [], "competitive": [], "dream": []}

        ssc_gpa = cls._get_user_gpa(profile, "SSC") or 4.5
        hsc_gpa = cls._get_user_gpa(profile, "HSC") or ssc_gpa
        base_gpa = (ssc_gpa + hsc_gpa) / 2.0

        subject_keywords = cls._extract_subject_keywords(profile)
        location = (profile.district or profile.division or "").lower()

        institutions = (
            db.query(Institution).filter(Institution.is_active.is_(True)).all()
        )

        scored: List[Dict[str, Any]] = []
        for inst in institutions:
            score, reason = cls._score_institution(inst, subject_keywords, location)
            if score <= 0:
                continue

            min_gpa = cls._get_min_gpa(db, inst)
            # Tier based on GPA fit vs. student's GPA
            if min_gpa is not None and min_gpa > base_gpa + 0.5:
                tier = "dream"
            elif min_gpa is not None and min_gpa > base_gpa:
                tier = "competitive"
            else:
                tier = "safety"

            scored.append(
                {
                    "institution_id": inst.id,
                    "name_en": inst.name_en,
                    "name_bn": inst.name_bn,
                    "short_name": inst.short_name,
                    "slug": inst.slug,
                    "type": inst.type.name if inst.type else None,
                    "score": round(score, 1),
                    "tier": tier,
                    "match_reasons": reason,
                    "min_gpa_requirement": min_gpa,
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)

        best_matches = scored[:limit]
        safety = [s for s in scored if s["tier"] == "safety"][:limit]
        competitive = [s for s in scored if s["tier"] == "competitive"][:limit]
        dream = [s for s in scored if s["tier"] == "dream"][:limit]

        return {
            "best_matches": best_matches,
            "safety": safety,
            "competitive": competitive,
            "dream": dream,
        }

    @staticmethod
    def _get_min_gpa(db: Session, inst: Institution) -> Optional[float]:
        """Find the lowest min_gpa among the institution's requirements."""
        reqs = (
            db.query(InstitutionRequirement)
            .filter(
                InstitutionRequirement.institution_id == inst.id,
                InstitutionRequirement.min_gpa.isnot(None),
            )
            .all()
        )
        if not reqs:
            return None
        return min(r.min_gpa for r in reqs)

    @staticmethod
    def _score_institution(
        inst: Institution,
        subject_keywords: List[str],
        location: str,
    ) -> tuple:
        """Score an institution (0-100) against the student's preferences."""
        score = 10.0
        reasons: List[str] = []

        haystack = " ".join(
            filter(
                None,
                [
                    inst.name_en,
                    inst.name_bn,
                    inst.short_name,
                    inst.description,
                    inst.keywords,
                    inst.search_vector,
                ],
            )
        ).lower()

        # Subject match
        for kw in subject_keywords:
            if kw in haystack:
                score += 20
                reasons.append(f"Offers {kw}")
                break

        # Location match
        inst_location = " ".join(
            filter(
                None,
                [
                    inst.address,
                    inst.upazila.name_en if inst.upazila else None,
                    (
                        inst.upazila.district.name_en
                        if inst.upazila and inst.upazila.district
                        else None
                    ),
                    (
                        inst.upazila.district.division.name_en
                        if inst.upazila
                        and inst.upazila.district
                        and inst.upazila.district.division
                        else None
                    ),
                ],
            )
        ).lower()
        if location and location in inst_location:
            score += 15
            reasons.append("Close to your location")

        # Popularity signal (view count)
        score += min(15, inst.view_count or 0) * 0.05

        return round(min(100, score), 1), reasons


class CourseRecommender:
    """Recommend courses based on history, interests, career and behavior."""

    @classmethod
    def recommend(
        cls,
        db: Session,
        user: User,
        limit: int = 10,
    ) -> Dict[str, Any]:
        profile = (
            db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        )

        interest_subjects: List[str] = []
        if profile:
            interest_subjects = ProfileReader.json_list(
                profile.academic_interests
            ) + ProfileReader.json_list(profile.favorite_subjects)
            if profile.preferred_subject:
                interest_subjects.append(profile.preferred_subject)
            if profile.dream_career:
                interest_subjects.append(profile.dream_career)

        # Behavior: most-viewed / bookmarked subjects from events
        event_subjects = (
            db.query(
                AnalyticsEvent.subject, func.count(AnalyticsEvent.id).label("count")
            )
            .filter(
                AnalyticsEvent.user_id == user.id,
                AnalyticsEvent.subject.isnot(None),
            )
            .group_by(AnalyticsEvent.subject)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(10)
            .all()
        )
        behavior_subjects = [s for s, _ in event_subjects]

        all_interests = list(dict.fromkeys(interest_subjects + behavior_subjects))

        # Pull courses from institutions matching interest keywords
        from app.models.course import Course

        courses = db.query(Course).limit(500).all()
        recommendations = []
        for course in courses:
            course_text = " ".join(
                filter(None, [course.name, course.description])
            ).lower()
            score = 0.0
            reasons = []
            for interest in all_interests:
                if interest and interest.lower() in course_text:
                    score += 30
                    reasons.append(interest)
                    break
            if score > 0:
                inst = db.query(Institution).get(course.institution_id)
                recommendations.append(
                    {
                        "course_id": course.id,
                        "name": course.name,
                        "degree_awarded": course.degree_awarded,
                        "duration": course.duration,
                        "institution_id": course.institution_id,
                        "institution_name": inst.name_en if inst else None,
                        "score": round(score, 1),
                        "match_reasons": reasons,
                    }
                )

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return {"courses": recommendations[:limit], "interest_signals": all_interests}


class ScholarshipRecommender:
    """Recommend scholarships based on financial need, merit and eligibility.

    Phase 1 uses a rule-based matcher against institution requirements flagged
    as scholarship. Scholarship-specific data can be attached via the
    InstitutionRequirement table (requirement_type == 'scholarship').
    """

    @classmethod
    def recommend(
        cls,
        db: Session,
        user: User,
        limit: int = 10,
    ) -> Dict[str, Any]:
        profile = (
            db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        )
        if profile is None:
            return {"scholarships": []}

        ssc_gpa = InstitutionRecommender._get_user_gpa(profile, "SSC")
        hsc_gpa = InstitutionRecommender._get_user_gpa(profile, "HSC")
        best_gpa = max([g for g in [ssc_gpa, hsc_gpa] if g], default=0.0)

        has_need = (profile.annual_income or 0) > 0 and (
            profile.annual_income or 0
        ) < 600000
        merit = best_gpa >= 4.5
        has_disability = bool(profile.disability)

        from app.models.institution import Institution

        requirements = (
            db.query(InstitutionRequirement)
            .filter(
                InstitutionRequirement.requirement_type == "scholarship",
                InstitutionRequirement.level.in_(["hsc", "undergraduate", "graduate"]),
            )
            .limit(500)
            .all()
        )

        results = []
        for req in requirements:
            score = 0.0
            reasons = []
            inst = db.query(Institution).get(req.institution_id)
            inst_name = inst.name_en if inst else "Unknown Institution"

            min_gpa = req.min_gpa or 0.0
            if merit and best_gpa >= min_gpa:
                score += 40
                reasons.append("Meets merit GPA requirement")
            if has_need:
                score += 35
                reasons.append("Financial need")
            if has_disability:
                score += 25
                reasons.append("Disability support")

            if score <= 0:
                continue

            results.append(
                {
                    "scholarship_id": req.id,
                    "institution_id": req.institution_id,
                    "institution_name": inst_name,
                    "level": req.level,
                    "min_gpa": req.min_gpa,
                    "application_process": req.application_process,
                    "details": req.admission_test_details,
                    "score": round(score, 1),
                    "match_reasons": reasons,
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return {"scholarships": results[:limit]}


def get_all_recommendations(db: Session, user: User) -> Dict[str, Any]:
    """Convenience: all recommendation types for the student 360 dashboard."""
    return {
        "institutions": InstitutionRecommender.recommend(db, user),
        "courses": CourseRecommender.recommend(db, user),
        "scholarships": ScholarshipRecommender.recommend(db, user),
    }
