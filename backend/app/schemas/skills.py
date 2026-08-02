"""Pydantic schemas for Predictive Skill Gap Analysis."""

from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


class SkillBase(BaseModel):
    name: str
    name_bn: Optional[str] = None
    category: str = "technical"
    subcategory: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    skill_level: str = "intermediate"
    is_active: bool = True


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------------------------------------------------------------------------
# Market demand
# ---------------------------------------------------------------------------


class MarketDemandCreate(BaseModel):
    skill_id: int
    year: int
    quarter: Optional[int] = None
    demand_score: Optional[float] = None
    postings_count: Optional[int] = None
    hiring_growth_pct: Optional[float] = None
    source: str = "job_portal"
    industry_sector: Optional[str] = None
    region: Optional[str] = None


class MarketDemandResponse(MarketDemandCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------------------------------------------------------------------------
# Skill gap analysis
# ---------------------------------------------------------------------------


class SkillRef(BaseModel):
    id: int
    name: str
    name_bn: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class SkillGapResponse(BaseModel):
    skill_id: int
    skill: SkillRef
    supply_score: Optional[float] = None
    demand_score: Optional[float] = None
    gap_score: Optional[float] = None
    forecast_demand: Optional[float] = None
    forecast_year: Optional[int] = None
    trend: Optional[str] = None
    status: Optional[str] = None
    methodology: Optional[str] = None
    computed_at: Optional[str] = None


class SkillGapReportResponse(BaseModel):
    items: List[SkillGapResponse]
    total: int


class AnalysisRunResponse(BaseModel):
    analyzed: int
    forecast_year: int
    computed_at: str


# ---------------------------------------------------------------------------
# Skill detail / institution / student
# ---------------------------------------------------------------------------


class DemandPoint(BaseModel):
    year: int
    quarter: Optional[int] = None
    demand_score: Optional[float] = None
    postings_count: Optional[int] = None
    hiring_growth_pct: Optional[float] = None
    source: Optional[str] = None


class SkillDetailResponse(BaseModel):
    id: int
    name: str
    name_bn: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: Optional[str] = None
    demand_series: List[DemandPoint]
    supply_institutions_count: int


class InstitutionSkillResponse(BaseModel):
    skill_id: int
    name: str
    category: Optional[str] = None
    derivation: Optional[str] = None
    confidence: Optional[float] = None
    demand_score: Optional[float] = None
    gap_score: Optional[float] = None
    status: Optional[str] = None
    trend: Optional[str] = None
