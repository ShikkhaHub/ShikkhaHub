"""Predictive Skill Gap Analysis entities.

Implements the skill gap analysis roadmap component:

- `Skill` - canonical skill catalog (technical / soft / domain skills).
- `MarketDemand` - demand-side signals collected from job portals,
  certification bodies and industry reports (per-skill, time-series).
- `InstitutionSkill` - supply-side: skills an institution teaches (derived
  from its curriculum / course catalog).
- `SkillGapAnalysis` - cached outputs of the analytical engine: gap score,
  demand forecast and trend classification per skill.

The analytical engine (`app.services.skill_gap`) writes `SkillGapAnalysis`
rows and reads from `MarketDemand` (demand) and `InstitutionSkill` (supply)
to flag deficits and emerging skill areas.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Skill(Base):
    """A skill in the national skills catalog.

    `category` groups skills (technical, soft_skill, domain, emerging) and
    `keywords` are the tokens used for NLP matching against curricula and
    job descriptions.
    """

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    name_bn = Column(String(200), nullable=True)
    category = Column(
        String(50), default="technical", index=True
    )  # technical, soft_skill, domain, emerging
    subcategory = Column(String(100), nullable=True)  # e.g. programming, design
    description = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)  # comma-separated matching tokens
    skill_level = Column(String(20), default="intermediate")  # beginner, intermediate, advanced
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    demand_signals = relationship(
        "MarketDemand", back_populates="skill", cascade="all, delete-orphan"
    )
    supply_links = relationship(
        "InstitutionSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    gap_analyses = relationship(
        "SkillGapAnalysis", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_skill_category", "category"),
        Index("idx_skill_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Skill {self.name}>"


class MarketDemand(Base):
    """Demand-side signal for a skill in a given year/quarter.

    `demand_score` is a normalized 0-100 index, `postings_count` the raw
    number of job postings observed, and `source` records where the signal
    came from (job_portal, certification, industry_report, government).
    """

    __tablename__ = "skill_market_demand"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=True)  # 1-4

    # Demand metrics
    demand_score = Column(Float, nullable=True)  # normalized 0-100
    postings_count = Column(Integer, nullable=True)
    hiring_growth_pct = Column(Float, nullable=True)  # YoY growth

    # Provenance
    source = Column(
        String(50), default="job_portal"
    )  # job_portal, certification, industry_report, government
    industry_sector = Column(String(100), nullable=True)  # it, garments, health, ...
    region = Column(String(100), nullable=True)  # dhaka, national, ...

    created_at = Column(DateTime, default=datetime.utcnow)

    skill = relationship("Skill", back_populates="demand_signals")

    __table_args__ = (
        UniqueConstraint("skill_id", "year", "quarter", name="uq_skill_demand_period"),
        Index("idx_demand_year", "year"),
        Index("idx_demand_source", "source"),
        Index("idx_demand_sector", "industry_sector"),
    )

    def __repr__(self) -> str:
        return f"<MarketDemand skill={self.skill_id} {self.year}Q{self.quarter}>"


class InstitutionSkill(Base):
    """Supply-side: a skill an institution teaches (derived or declared).

    `derivation` records how the link was established (curriculum_nlp,
    course_match, manual) and `graduates_estimate` approximates annual output
    used to size supply against demand.
    """

    __tablename__ = "institution_skills"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer, ForeignKey("institutions.id"), nullable=False, index=True
    )
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)

    derivation = Column(String(30), default="curriculum_nlp")
    confidence = Column(Float, default=0.5)
    graduates_estimate = Column(Integer, nullable=True)
    source_course_id = Column(Integer, nullable=True)  # matching course id if any

    created_at = Column(DateTime, default=datetime.utcnow)

    institution = relationship("Institution", back_populates="skill_links")
    skill = relationship("Skill", back_populates="supply_links")

    __table_args__ = (
        UniqueConstraint("institution_id", "skill_id", name="uq_institution_skill"),
        Index("idx_institution_skill_skill", "skill_id"),
    )

    def __repr__(self) -> str:
        return f"<InstitutionSkill inst={self.institution_id} skill={self.skill_id}>"


class SkillGapAnalysis(Base):
    """Cached output of the predictive skill gap engine.

    `gap_score` is positive when demand outstrips supply (a deficit), near
    zero when balanced, negative when supply exceeds demand (a surplus).
    `forecast_demand` is the projected demand score and `trend` classifies
    whether demand is rising, stable or falling.
    """

    __tablename__ = "skill_gap_analyses"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)

    # Scores
    supply_score = Column(Float, nullable=True)  # normalized 0-100
    demand_score = Column(Float, nullable=True)  # latest observed 0-100
    gap_score = Column(Float, nullable=True)  # demand - supply
    forecast_demand = Column(Float, nullable=True)
    forecast_year = Column(Integer, nullable=True)

    # Classification
    trend = Column(String(20), default="stable")  # rising, stable, falling
    status = Column(String(20), default="balanced")  # deficit, balanced, surplus

    # Provenance
    methodology = Column(String(100), default="trend_extrapolation")
    computed_at = Column(DateTime, default=datetime.utcnow, index=True)

    skill = relationship("Skill", back_populates="gap_analyses")

    __table_args__ = (
        Index("idx_gap_skill", "skill_id"),
        Index("idx_gap_status", "status"),
        Index("idx_gap_trend", "trend"),
        Index("idx_gap_computed", "computed_at"),
    )

    def __repr__(self) -> str:
        return f"<SkillGapAnalysis skill={self.skill_id} gap={self.gap_score} {self.trend}>"
