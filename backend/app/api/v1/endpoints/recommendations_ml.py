"""Machine-learning recommendation endpoints.

Implements the ML Recommendations Plan API surface on top of the Phase-1
rule-based recommendations:

- `/recommendations/me`            personalized institutions (hybrid CF + CB)
- `/recommendations/trending`      trend-based discovery (optional district)
- `/recommendations/popular`       globally popular institutions
- `/recommendations/institutions/{institution_id}/similar`
                                  content-based "more like this"
- `/recommendations/train`         (admin) retrain the ML models

Endpoints fall back gracefully to rule-based cold-start recommendations when
the ML engine has no trained data yet, preserving the existing API contract.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.ml_recommendations import (
    TrendingRecommender,
    get_ml_engine,
)

router = APIRouter()


@router.get("/recommendations/me")
def recommend_ml_institutions(
    limit: int = Query(10, ge=1, le=50),
    force_refit: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Personalized institution recommendations using the ML engine.

    Blends collaborative + content-based signals, or returns cold-start
    recommendations for users without history.
    """
    engine = get_ml_engine()
    return engine.recommend_for_user(
        db, user_id=current_user.id, limit=limit, force_refit=force_refit
    )


@router.get("/recommendations/trending")
def recommend_trending(
    district: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Trend-based discovery: institutions gaining traction recently."""
    return TrendingRecommender.trending(
        db, district=district, division=division, days=days, limit=limit
    )


@router.get("/recommendations/popular")
def recommend_popular(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Globally popular institutions by engagement."""
    return TrendingRecommender.popular(db, limit=limit)


@router.get("/recommendations/institutions/{institution_id}/similar")
def recommend_similar_institutions(
    institution_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Content-based 'more like this' recommendations."""
    engine = get_ml_engine()
    return engine.similar_institutions(db, institution_id=institution_id, limit=limit)


@router.post("/recommendations/train")
def train_ml_recommendations(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Retrain the ML recommendation models from current analytics data."""
    engine = get_ml_engine()
    ok = engine.fit(db)
    return {"success": ok, "fitted": engine.is_fitted}
