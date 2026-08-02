"""Predictive Skill Gap Analysis service.

Implements the analytical engine behind the skill gap roadmap component:

1. **Data integration** - merges demand-side signals (`MarketDemand`) with
   supply-side data derived from the directory's curriculum (institution
   courses / subjects / program text) via NLP keyword matching.
2. **Trend extrapolation** - fits a linear regression over the demand time
   series to forecast future demand and classify each skill's trend.
3. **Gap scoring** - computes supply vs demand per skill and flags deficits
   (gap > 0 = unfulfilled market demand), surpluses, and emerging skills.

Outputs feed actionable insights for institutions (which skills to teach),
students (emerging add-on skills), and policymakers (where more training is
needed).
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.education_graph import InstitutionCourse
from app.models.institution import Institution
from app.models.skills import (
    InstitutionSkill,
    MarketDemand,
    Skill,
    SkillGapAnalysis,
)
from app.models.subject import Subject

logger = logging.getLogger(__name__)

FORECAST_YEARS = 2  # how many years ahead to project demand


def _tokens(text: Optional[str]) -> str:
    """Lowercase text for matching."""
    return (text or "").lower()


def _skill_keywords(skill: Skill) -> List[str]:
    """Extract matching tokens from a skill (name + keywords)."""
    tokens = []
    if skill.name:
        tokens.append(skill.name.lower())
    if skill.keywords:
        for kw in skill.keywords.split(","):
            kw = kw.strip().lower()
            if kw:
                tokens.append(kw)
    return tokens


def _text_contains(text: str, token: str) -> bool:
    """Whole-token containment test for a phrase in text."""
    token = token.strip().lower()
    if not token:
        return False
    if " " in token:
        return token in text
    return re.search(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", text) is not None


def _course_text(course: Course) -> str:
    """Concatenate all text fields of a course for NLP matching."""
    return " ".join(
        [
            _tokens(course.name_en),
            _tokens(course.name_bn),
            _tokens(course.description),
            _tokens(course.keywords),
            _tokens(course.career_prospects),
            _tokens(course.required_subjects),
            _tokens(course.curriculum_outline),
            _tokens(course.course_type.name) if course.course_type else "",
        ]
    )


def _subject_text(subject: Subject) -> str:
    return " ".join(
        [
            _tokens(subject.name_en),
            _tokens(subject.name_bn),
            _tokens(subject.description),
            _tokens(subject.topics_covered),
            _tokens(subject.category),
        ]
    )


def supply_from_curriculum(db: Session) -> Dict[int, Dict[str, Any]]:
    """Derive which skills each institution teaches from its course catalog.

    Returns {institution_id: {"skill_ids": [...], "matched_course_ids": {...}}}.
    Skills are matched against course + subject text using keyword tokens.
    """
    institutions = db.query(Institution).filter(Institution.is_active.is_(True)).all()
    skills = db.query(Skill).filter(Skill.is_active.is_(True)).all()

    # Pre-fetch courses per institution (via offerings or direct link)
    offerings = db.query(InstitutionCourse).all()
    course_ids = {o.course_id for o in offerings}
    direct_courses = (
        db.query(Course)
        .filter(Course.institution_id.isnot(None), Course.is_active.is_(True))
        .all()
    )
    courses_by_id: Dict[int, Course] = {c.id: c for c in direct_courses}
    course_ids.update(courses_by_id.keys())
    courses_by_id.update(
        {c.id: c for c in db.query(Course).filter(Course.id.in_(course_ids)).all()}
    )

    # Subjects keyed by course
    subjects = db.query(Subject).all()
    subjects_by_course: Dict[int, List[Subject]] = {}
    for s in subjects:
        if s.course_id:
            subjects_by_course.setdefault(s.course_id, []).append(s)

    inst_courses: Dict[int, List[int]] = {}
    for o in offerings:
        inst_courses.setdefault(o.institution_id, []).append(o.course_id)
    for c in direct_courses:
        if c.institution_id:
            inst_courses.setdefault(c.institution_id, []).append(c.id)

    result: Dict[int, Dict[str, Any]] = {}
    for inst in institutions:
        course_ids_for_inst = set(inst_courses.get(inst.id, []))
        inst_skills: List[int] = []
        matched: Dict[int, int] = {}
        for skill in skills:
            tokens = _skill_keywords(skill)
            if not tokens:
                continue
            hit = None
            for cid in course_ids_for_inst:
                course = courses_by_id.get(cid)
                if course is None:
                    continue
                text = _course_text(course)
                for subj in subjects_by_course.get(cid, []):
                    text += " " + _subject_text(subj)
                for tok in tokens:
                    if _text_contains(text, tok):
                        hit = cid
                        break
                if hit:
                    break
            if hit is not None:
                inst_skills.append(skill.id)
                matched[skill.id] = hit

        if inst_skills:
            result[inst.id] = {
                "skill_ids": inst_skills,
                "matched_course_ids": matched,
            }
    return result


def sync_institution_skills(db: Session) -> Dict[str, Any]:
    """Persist derived institution→skill supply links (idempotent)."""
    derived = supply_from_curriculum(db)
    created = 0
    updated = 0
    for inst_id, payload in derived.items():
        for skill_id in payload["skill_ids"]:
            existing = (
                db.query(InstitutionSkill)
                .filter(
                    InstitutionSkill.institution_id == inst_id,
                    InstitutionSkill.skill_id == skill_id,
                )
                .first()
            )
            if existing:
                existing.derivation = "curriculum_nlp"
                existing.confidence = 0.7
                updated += 1
            else:
                db.add(
                    InstitutionSkill(
                        institution_id=inst_id,
                        skill_id=skill_id,
                        derivation="curriculum_nlp",
                        confidence=0.7,
                        source_course_id=payload["matched_course_ids"].get(skill_id),
                    )
                )
                created += 1
    db.commit()
    logger.info("InstitutionSkill sync: %d created, %d updated", created, updated)
    return {"created": created, "updated": updated}


def compute_supply_scores(db: Session) -> Dict[int, float]:
    """Normalized supply score per skill: how many institutions teach it."""
    rows = (
        db.query(InstitutionSkill.skill_id, func.count(InstitutionSkill.id))
        .group_by(InstitutionSkill.skill_id)
        .all()
    )
    counts = {sid: cnt for sid, cnt in rows}
    if not counts:
        return {}
    max_count = max(counts.values()) or 1
    return {sid: round(cnt / max_count * 100, 2) for sid, cnt in counts.items()}


def compute_demand_scores(db: Session) -> Dict[int, float]:
    """Latest demand score per skill (most recent signal per skill)."""
    rows = (
        db.query(
            MarketDemand.skill_id,
            func.max(MarketDemand.year).label("max_year"),
        )
        .group_by(MarketDemand.skill_id)
        .all()
    )
    result: Dict[int, float] = {}
    for skill_id, max_year in rows:
        signal = (
            db.query(MarketDemand)
            .filter(MarketDemand.skill_id == skill_id, MarketDemand.year == max_year)
            .order_by(MarketDemand.quarter.desc().nullslast())
            .first()
        )
        if signal and signal.demand_score is not None:
            result[skill_id] = signal.demand_score
    return result


def forecast_demand(
    db: Session, skill_id: int, years: int = FORECAST_YEARS
) -> Tuple[Optional[float], Optional[str]]:
    """Linear-regression forecast of future demand for a skill.

    Uses scikit-learn LinearRegression on the (year -> demand_score) series.
    Returns (forecast_value, trend) where trend is rising / stable / falling.
    """
    signals = (
        db.query(MarketDemand)
        .filter(MarketDemand.skill_id == skill_id, MarketDemand.demand_score.isnot(None))
        .order_by(MarketDemand.year, MarketDemand.quarter)
        .all()
    )
    # Aggregate per year (mean score) for a clean series
    by_year: Dict[int, List[float]] = {}
    for s in signals:
        by_year.setdefault(s.year, []).append(s.demand_score)
    if not by_year:
        return None, "stable"

    sample_years = sorted(by_year)
    series = [sum(by_year[y]) / len(by_year[y]) for y in sample_years]
    if len(series) < 2:
        forecast = series[0]
        return round(forecast, 2), "stable"

    try:
        from sklearn.linear_model import LinearRegression

        import numpy as np

        X = np.array(sample_years, dtype=float).reshape(-1, 1)
        y = np.array(series, dtype=float)
        model = LinearRegression().fit(X, y)
        last_year = sample_years[-1]
        target_year = last_year + years  # years ahead
        forecast = float(model.predict([[target_year]])[0])
        forecast = max(0.0, min(100.0, forecast))

        slope = model.coef_[0]
        span = max(1.0, max(series) - min(series))
        rate = slope / span if span else 0.0
        if rate > 0.1:
            trend = "rising"
        elif rate < -0.1:
            trend = "falling"
        else:
            trend = "stable"
        return round(forecast, 2), trend
    except Exception as exc:  # noqa: BLE001
        logger.warning("Forecast failed for skill %s: %s", skill_id, exc)
        last = series[-1]
        return round(last, 2), "stable"


def classify_status(gap: float) -> str:
    """Classify a gap score into deficit / balanced / surplus."""
    if gap > 15:
        return "deficit"
    if gap < -15:
        return "surplus"
    return "balanced"


def run_full_analysis(db: Session) -> Dict[str, Any]:
    """Compute and persist gap analyses for every active skill.

    - sync supply links from the curriculum
    - forecast each skill's demand
    - compute gap = demand - supply
    - persist SkillGapAnalysis rows (replacing stale ones)
    """
    sync_institution_skills(db)
    supply = compute_supply_scores(db)
    demand = compute_demand_scores(db)

    skills = db.query(Skill).filter(Skill.is_active.is_(True)).all()
    now = datetime.utcnow()

    # Remove previous analyses for recomputation
    db.query(SkillGapAnalysis).delete()
    db.flush()

    analyses = []
    for skill in skills:
        demand_score = demand.get(skill.id)
        if demand_score is None:
            continue  # no demand signal yet — skip
        supply_score = supply.get(skill.id, 0.0)
        forecast, trend = forecast_demand(db, skill.id)
        gap = round(demand_score - supply_score, 2)

        analyses.append(
            SkillGapAnalysis(
                skill_id=skill.id,
                supply_score=supply_score,
                demand_score=demand_score,
                gap_score=gap,
                forecast_demand=forecast,
                forecast_year=datetime.utcnow().year + FORECAST_YEARS,
                trend=trend,
                status=classify_status(gap),
                methodology="trend_extrapolation+supply_curriculum",
                computed_at=now,
            )
        )
    db.add_all(analyses)
    db.commit()

    return {
        "analyzed": len(analyses),
        "forecast_year": now.year + FORECAST_YEARS,
        "computed_at": now.isoformat(),
    }


def get_gap_report(db: Session, limit: int = 50) -> Dict[str, Any]:
    """Latest persisted gap analyses, ranked by gap magnitude."""
    analyses = (
        db.query(SkillGapAnalysis)
        .order_by(SkillGapAnalysis.computed_at.desc(), SkillGapAnalysis.gap_score.desc())
        .limit(limit)
        .all()
    )
    return {
        "items": [_serialize_analysis(a) for a in analyses],
        "total": len(analyses),
    }


def get_emerging_skills(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """Skills with rising demand that institutions under-supply (the 'gap').

    Emerging = trend rising AND status deficit, ordered by gap magnitude.
    """
    latest = (
        db.query(SkillGapAnalysis)
        .order_by(SkillGapAnalysis.computed_at.desc())
        .first()
    )
    if latest is None:
        return []
    analyses = (
        db.query(SkillGapAnalysis)
        .filter(
            SkillGapAnalysis.computed_at >= latest.computed_at,
            SkillGapAnalysis.trend == "rising",
            SkillGapAnalysis.status == "deficit",
        )
        .order_by(SkillGapAnalysis.gap_score.desc())
        .limit(limit)
        .all()
    )
    return [_serialize_analysis(a) for a in analyses]


def get_skill_detail(db: Session, skill_id: int) -> Optional[Dict[str, Any]]:
    """Detailed view of one skill: demand series + supply + forecast."""
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if skill is None:
        return None

    demand_series = (
        db.query(MarketDemand)
        .filter(MarketDemand.skill_id == skill_id)
        .order_by(MarketDemand.year, MarketDemand.quarter)
        .all()
    )
    supply_count = (
        db.query(func.count(InstitutionSkill.id))
        .filter(InstitutionSkill.skill_id == skill_id)
        .scalar()
        or 0
    )

    return {
        "id": skill.id,
        "name": skill.name,
        "name_bn": skill.name_bn,
        "category": skill.category,
        "subcategory": skill.subcategory,
        "description": skill.description,
        "demand_series": [
            {
                "year": d.year,
                "quarter": d.quarter,
                "demand_score": d.demand_score,
                "postings_count": d.postings_count,
                "hiring_growth_pct": d.hiring_growth_pct,
                "source": d.source,
            }
            for d in demand_series
        ],
        "supply_institutions_count": supply_count,
    }


def get_institution_skills(
    db: Session, institution_id: int
) -> List[Dict[str, Any]]:
    """Skills taught at an institution, with their gap status where known."""
    links = (
        db.query(InstitutionSkill)
        .filter(InstitutionSkill.institution_id == institution_id)
        .all()
    )
    skill_ids = [link.skill_id for link in links]
    if not skill_ids:
        return []

    skills = {s.id: s for s in db.query(Skill).filter(Skill.id.in_(skill_ids)).all()}
    latest = (
        db.query(SkillGapAnalysis)
        .order_by(SkillGapAnalysis.computed_at.desc())
        .first()
    )
    gaps: Dict[int, SkillGapAnalysis] = {}
    if latest is not None:
        gap_rows = (
            db.query(SkillGapAnalysis)
            .filter(
                SkillGapAnalysis.computed_at >= latest.computed_at,
                SkillGapAnalysis.skill_id.in_(skill_ids),
            )
            .all()
        )
        gaps = {g.skill_id: g for g in gap_rows}

    out = []
    for link in links:
        skill = skills.get(link.skill_id)
        if skill is None:
            continue
        gap = gaps.get(link.skill_id)
        out.append(
            {
                "skill_id": skill.id,
                "name": skill.name,
                "category": skill.category,
                "derivation": link.derivation,
                "confidence": link.confidence,
                "demand_score": gap.demand_score if gap else None,
                "gap_score": gap.gap_score if gap else None,
                "status": gap.status if gap else None,
                "trend": gap.trend if gap else None,
            }
        )
    out.sort(key=lambda r: (r["status"] == "deficit"), reverse=True)
    return out


def recommend_student_skills(
    db: Session, student_profile: Any = None, limit: int = 10
) -> List[Dict[str, Any]]:
    """Emerging skills a student should add on to their degree.

    Uses the student's academic interests when available; otherwise returns
    the top emerging deficit skills nationally.
    """
    emerging = get_emerging_skills(db, limit=limit)

    # Try to personalize from interests / dream career keywords
    interests = ""
    if student_profile is not None:
        for attr in (
            "academic_interests",
            "interested_sectors",
            "dream_career",
            "favorite_subjects",
        ):
            val = getattr(student_profile, attr, None)
            if val:
                interests += " " + _tokens(str(val))

    if interests:
        ranked = []
        for item in emerging:
            skill_name = _tokens(item["skill"]["name"])
            score = 1.0 if any(tok in interests for tok in skill_name.split()) else 0.0
            ranked.append((score, item))
        ranked.sort(key=lambda x: x[0], reverse=True)
        items = [item for _, item in ranked[:limit]]
        return items

    return emerging


def _serialize_analysis(a: SkillGapAnalysis) -> Dict[str, Any]:
    return {
        "skill_id": a.skill_id,
        "skill": {
            "id": a.skill.id,
            "name": a.skill.name,
            "name_bn": a.skill.name_bn,
            "category": a.skill.category,
            "subcategory": a.skill.subcategory,
        },
        "supply_score": a.supply_score,
        "demand_score": a.demand_score,
        "gap_score": a.gap_score,
        "forecast_demand": a.forecast_demand,
        "forecast_year": a.forecast_year,
        "trend": a.trend,
        "status": a.status,
        "methodology": a.methodology,
        "computed_at": a.computed_at.isoformat() if a.computed_at else None,
    }
