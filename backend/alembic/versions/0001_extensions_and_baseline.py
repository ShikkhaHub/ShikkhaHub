"""initial baseline + extensions

Revision ID: 0001_extensions_and_baseline
Revises:
Create Date: 2026-08-02

This migration bootstraps ShikkhaHub from a `create_all`-managed schema into
Alembic-managed migrations:

1. Enables the recommended PostgreSQL extensions (PostGIS, pg_trgm,
   uuid-ossp, unaccent).
2. Creates the full normalized schema from the SQLAlchemy metadata
   (`Base.metadata.create_all`), which is a safe, one-time baseline.
3. Seeds the base RBAC roles used across the platform.

Subsequent schema changes should be authored with `alembic revision
--autogenerate`.
"""
from alembic import op
import sqlalchemy as sa

import app.models  # noqa: F401  (registers all tables on Base.metadata)
from app.core.database import Base

# revision identifiers, used by Alembic.
revision = "0001_extensions_and_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import text

    # 1. PostgreSQL extensions (best-effort; PostGIS may need privileges)
    for ext in ("postgis", "pg_trgm", "uuid-ossp", "unaccent"):
        try:
            bind.execute(text(f'CREATE EXTENSION IF NOT EXISTS "{ext}"'))
        except Exception:  # noqa: BLE001
            op.get_context().log.info(f"Skipping extension {ext}")

    # 2. Full normalized schema baseline from SQLAlchemy metadata
    Base.metadata.create_all(bind=bind)

    # 3. Seed base roles (idempotent)
    roles_table = sa.table(
        "roles",
        sa.column("name", sa.String),
        sa.column("is_system", sa.Boolean),
        sa.column("description", sa.String),
    )
    bind.execute(
        sa.insert(roles_table),
        [
            {
                "name": "super_admin",
                "is_system": True,
                "description": "Full platform control",
            },
            {
                "name": "admin",
                "is_system": True,
                "description": "Platform administration",
            },
            {
                "name": "verifier",
                "is_system": True,
                "description": "Reviews and verifies institution data",
            },
            {
                "name": "moderator",
                "is_system": True,
                "description": "Moderates community content",
            },
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
