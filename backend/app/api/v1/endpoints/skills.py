"""Predictive Skill Gap Analysis API endpoints.

Exposes the analytics engine to end users and administrators:

- **Emerging skills** - skills with rising demand that institutions under-supply
- **Gap report** - full supply/demand gap ranking per skill
- **Skill detail** - demand time series + supply snapshot for one skill
- **Institution insights** - which skills an institution teaches + gaps to fill
- **Student guidance** - emerging add-on skills to boost employability
- **Admin** - create skills / demand signals, re-run the analysis engine

All public endpoints read from the cached `SkillGapAnalysis` output, so
response times stay fast; `POST /skills/analyze` recomputes the engine.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.models.institution import Institution
from app.models.skills import MarketDemand, Skill
from app.models.user import User
from app.schemas.skills import (
    AnalysisRunResponse,
    InstitutionSkillResponse,
    MarketDemandCreate,
    MarketDemandResponse,
    SkillCreate,
    SkillDetailResponse,
    SkillGapReportResponse,
    SkillGapResponse,
    SkillResponse,
)
from app.services import skill_gap

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Public: analytics output
# ---------------------------------------------------------------------------


@router.get("/gap-report", response_model=SkillGapReportResponse)
def gap_report(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Full supply-vs-demand gap ranking across all skills."""
    return skill_gap.get_gap_report(db, limit=limit)


@router.get("/emerging", response_model=List[SkillGapResponse])
def emerging_skills(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Skills with rising demand that institutions currently under-supply."""
    return skill_gap.get_emerging_skills(db, limit=limit)


@router.get("/skills/{skill_id}", response_model=SkillDetailResponse)
def skill_detail(skill_id: int, db: Session = Depends(get_db)):
    """Demand time series + supply snapshot for a single skill."""
    detail = skill_gap.get_skill_detail(db, skill_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return detail


# ---------------------------------------------------------------------------
# Public: institution & student guidance
# ---------------------------------------------------------------------------


@router.get(
    "/institutions/{institution_id}/skill-gaps",
    response_model=List[InstitutionSkillResponse],
)
def institution_skill_gaps(institution_id: int, db: Session = Depends(get_db)):
    """Skills an institution teaches, ranked by how much they lag demand."""
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if inst is None:
        raise HTTPException(status_code=404, detail="Institution not found")
    return skill_gap.get_institution_skills(db, institution_id)


@router.get("/student/add-on-skills", response_model=List[SkillGapResponse])
def student_add_on_skills(
    interests: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Emerging add-on skills students should pursue, optionally personalized.

    Pass `interests` as a comma-separated string of keywords (dream career,
    subjects, sectors) to rank recommendations by relevance.
    """
    return skill_gap.recommend_student_skills(db, interests, limit=limit)


# ---------------------------------------------------------------------------
# Admin: catalog management + engine
# ---------------------------------------------------------------------------


@router.post(
    "/admin/skills", response_model=SkillResponse, status_code=201
)
def create_skill(
    payload: SkillCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Register a canonical skill in the catalog (admin)."""
    existing = db.query(Skill).filter(Skill.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Skill already exists")
    skill = Skill(**payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.post(
    "/admin/market-demand",
    response_model=MarketDemandResponse,
    status_code=201,
)
def add_market_demand(
    payload: MarketDemandCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Record a demand-side signal (job postings / market score) (admin)."""
    skill = db.query(Skill).filter(Skill.id == payload.skill_id).first()
    if skill is None:
        raise HTTPException(status_code=404, detail="Skill not found")

    existing = (
        db.query(MarketDemand)
        .filter(
            MarketDemand.skill_id == payload.skill_id,
            MarketDemand.year == payload.year,
            MarketDemand.quarter == payload.quarter,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Signal already exists for this period")

    signal = MarketDemand(**payload.model_dump())
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


@router.post("/admin/analyze", response_model=AnalysisRunResponse)
def run_analysis(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Re-run the full skill-gap analysis engine (admin).

    Re-derives institution supply from the curriculum via NLP, forecasts
    demand with linear regression, and refreshes the cached gap report.
    """
    return skill_gap.run_full_analysis(db)
