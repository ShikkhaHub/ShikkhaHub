"""Natural Language Query Processing (NLQP) endpoints.

Users type free-text queries and the system translates them into structured
filters over the education directory.

Example: GET /search/natural?q=private universities with scholarships in Dhaka
returns parsed entities, a human-readable summary of what was understood, and
matching institutions.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.nlqp import natural_language_search

router = APIRouter()


@router.get("/natural")
def natural_language_query(
    q: str = Query(..., min_length=2, description="Natural language search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search the education directory using natural language.

    Parses intent and entities from the query, then executes the mapped
    database query. The response includes `query_summary` (what the system
    understood) and `filters_applied` for transparency.
    """
    return natural_language_search(db, q, page=page, page_size=page_size)
