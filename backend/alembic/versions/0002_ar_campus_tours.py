"""AR campus tour tables

Revision ID: 0002_ar_campus_tours
Revises: 0001_extensions_and_baseline
Create Date: 2026-08-02

Adds the Augmented Reality campus tour schema:
- ar_assets: lightweight AR overlay assets for POIs
- ar_pois: geolocated points of interest (spatial data for AR anchoring)
- ar_tours: curated walking tours
- ar_tour_stops: ordered POIs within a tour (wayfinding route)

These tables power the AR Campus Tours roadmap component and depend on the
existing `campuses` and `institutions` tables from the baseline migration.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_ar_campus_tours"
down_revision = "0001_extensions_and_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ar_pois",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("name_en", sa.String(300), nullable=False),
        sa.Column("name_bn", sa.String(300), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("altitude_m", sa.Float(), nullable=True),
        sa.Column("heading_deg", sa.Float(), nullable=True),
        sa.Column("radius_m", sa.Float(), nullable=True),
        sa.Column("marker_type", sa.String(20), nullable=True),
        sa.Column("marker_image_url", sa.String(500), nullable=True),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("info_tags", sa.Text(), nullable=True),
        sa.Column("department_summary", sa.Text(), nullable=True),
        sa.Column("opening_hours", sa.String(200), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"]),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )
    op.create_index("idx_ar_poi_active", "ar_pois", ["is_active"])
    op.create_index("idx_ar_poi_campus", "ar_pois", ["campus_id"])
    op.create_index("idx_ar_poi_category", "ar_pois", ["category"])
    op.create_index("idx_ar_poi_institution", "ar_pois", ["institution_id"])

    op.create_table(
        "ar_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("poi_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(20), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("size_kb", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(20), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["poi_id"], ["ar_pois.id"]),
    )
    op.create_index("idx_ar_asset_poi", "ar_assets", ["poi_id"])
    op.create_index("idx_ar_asset_type", "ar_assets", ["asset_type"])

    op.create_table(
        "ar_tours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campus_id", sa.Integer(), nullable=False),
        sa.Column("institution_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("title_bn", sa.String(300), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("distance_m", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"]),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"]),
    )
    op.create_index("idx_ar_tour_active", "ar_tours", ["is_active"])
    op.create_index("idx_ar_tour_campus", "ar_tours", ["campus_id"])
    op.create_index("idx_ar_tour_institution", "ar_tours", ["institution_id"])

    op.create_table(
        "ar_tour_stops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tour_id", sa.Integer(), nullable=False),
        sa.Column("poi_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("narration", sa.Text(), nullable=True),
        sa.Column("dwell_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["poi_id"], ["ar_pois.id"]),
        sa.ForeignKeyConstraint(["tour_id"], ["ar_tours.id"]),
        sa.UniqueConstraint("tour_id", "poi_id", name="uq_tour_stop_poi"),
    )
    op.create_index("idx_tour_stop_position", "ar_tour_stops", ["tour_id", "position"])


def downgrade() -> None:
    op.drop_index("idx_tour_stop_position", table_name="ar_tour_stops")
    op.drop_table("ar_tour_stops")
    op.drop_index("idx_ar_tour_institution", table_name="ar_tours")
    op.drop_index("idx_ar_tour_campus", table_name="ar_tours")
    op.drop_index("idx_ar_tour_active", table_name="ar_tours")
    op.drop_table("ar_tours")
    op.drop_index("idx_ar_asset_type", table_name="ar_assets")
    op.drop_index("idx_ar_asset_poi", table_name="ar_assets")
    op.drop_table("ar_assets")
    op.drop_index("idx_ar_poi_institution", table_name="ar_pois")
    op.drop_index("idx_ar_poi_category", table_name="ar_pois")
    op.drop_index("idx_ar_poi_campus", table_name="ar_pois")
    op.drop_index("idx_ar_poi_active", table_name="ar_pois")
    op.drop_table("ar_pois")
