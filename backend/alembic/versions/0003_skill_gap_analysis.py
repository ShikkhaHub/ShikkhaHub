"""skill gap analysis tables

Revision ID: 0003_skill_gap_analysis
Revises: 0002_ar_campus_tours
Create Date: 2026-08-02

Adds the Predictive Skill Gap Analysis schema:
- skills: canonical skill catalog
- skill_market_demand: demand-side time series (job postings / scores)
- institution_skills: supply-side (skills taught by an institution)
- skill_gap_analyses: cached engine output (gap score, forecast, trend)
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_skill_gap_analysis"
down_revision = "0002_ar_campus_tours"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("name_bn", sa.String(200), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", sa.Text(), nullable=True),
        sa.Column("skill_level", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("idx_skill_active", "skills", ["is_active"])
    op.create_index("idx_skill_category", "skills", ["category"])

    op.create_table(
        "skill_market_demand",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("quarter", sa.Integer(), nullable=True),
        sa.Column("demand_score", sa.Float(), nullable=True),
        sa.Column("postings_count", sa.Integer(), nullable=True),
        sa.Column("hiring_growth_pct", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("industry_sector", sa.String(100), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.UniqueConstraint(
            "skill_id", "year", "quarter", name="uq_skill_demand_period"
        ),
    )
    op.create_index("idx_demand_sector", "skill_market_demand", ["industry_sector"])
    op.create_index("idx_demand_source", "skill_market_demand", ["source"])
    op.create_index("idx_demand_year", "skill_market_demand", ["year"])

    op.create_table(
        "institution_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("derivation", sa.String(30), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("graduates_estimate", sa.Integer(), nullable=True),
        sa.Column("source_course_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.UniqueConstraint("institution_id", "skill_id", name="uq_institution_skill"),
    )
    op.create_index(
        "idx_institution_skill_skill", "institution_skills", ["skill_id"]
    )

    op.create_table(
        "skill_gap_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("supply_score", sa.Float(), nullable=True),
        sa.Column("demand_score", sa.Float(), nullable=True),
        sa.Column("gap_score", sa.Float(), nullable=True),
        sa.Column("forecast_demand", sa.Float(), nullable=True),
        sa.Column("forecast_year", sa.Integer(), nullable=True),
        sa.Column("trend", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("methodology", sa.String(100), nullable=True),
        sa.Column("computed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
    )
    op.create_index("idx_gap_computed", "skill_gap_analyses", ["computed_at"])
    op.create_index("idx_gap_skill", "skill_gap_analyses", ["skill_id"])
    op.create_index("idx_gap_status", "skill_gap_analyses", ["status"])
    op.create_index("idx_gap_trend", "skill_gap_analyses", ["trend"])


def downgrade() -> None:
    op.drop_index("idx_gap_trend", table_name="skill_gap_analyses")
    op.drop_index("idx_gap_status", table_name="skill_gap_analyses")
    op.drop_index("idx_gap_skill", table_name="skill_gap_analyses")
    op.drop_index("idx_gap_computed", table_name="skill_gap_analyses")
    op.drop_table("skill_gap_analyses")
    op.drop_index("idx_institution_skill_skill", table_name="institution_skills")
    op.drop_table("institution_skills")
    op.drop_index("idx_demand_year", table_name="skill_market_demand")
    op.drop_index("idx_demand_source", table_name="skill_market_demand")
    op.drop_index("idx_demand_sector", table_name="skill_market_demand")
    op.drop_table("skill_market_demand")
    op.drop_index("idx_skill_category", table_name="skills")
    op.drop_index("idx_skill_active", table_name="skills")
    op.drop_table("skills")
