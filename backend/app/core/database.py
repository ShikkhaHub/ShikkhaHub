from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.engine import Engine
from app.core.config import settings

# SQLite compatibility for testing (if needed)
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.DEBUG
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Session:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Recommended PostgreSQL extensions for the education knowledge graph.
# PostGIS = geospatial queries, pg_trgm = fuzzy search, unaccent = Bangla/Latin
# normalization, uuid-ossp = UUID generation.
POSTGRES_EXTENSIONS = ("postgis", "pg_trgm", "uuid-ossp", "unaccent")


def enable_postgres_extensions() -> None:
    """Enable required PostgreSQL extensions (best-effort, Postgres only).

    PostGIS can require superuser privileges on some managed providers, so each
    extension is created independently and failures are logged rather than
    aborting startup.
    """
    if not settings.DATABASE_URL.startswith("postgres"):
        return

    from sqlalchemy import text
    import logging

    logger = logging.getLogger(__name__)
    with engine.begin() as conn:
        for ext in POSTGRES_EXTENSIONS:
            try:
                conn.execute(text(f"CREATE EXTENSION IF NOT EXISTS \"{ext}\""))
                logger.info(f"Enabled PostgreSQL extension: {ext}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Could not enable PostgreSQL extension {ext}: {exc}")


def init_db() -> None:
    """Initialize database tables."""
    enable_postgres_extensions()
    Base.metadata.create_all(bind=engine)
