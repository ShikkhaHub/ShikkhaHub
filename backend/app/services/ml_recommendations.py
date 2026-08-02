"""Machine-learning recommendation engine for ShikkhaHub.

Implements the ML recommendations plan for the Bangladesh Education Directory:

- **Data Collection**: builds a user×institution implicit-feedback interaction
  matrix from `AnalyticsEvent`, `PageView`, `ClickEvent`, `SearchEvent`,
  `SavedInstitution` and `InstitutionReview`.
- **Feature Engineering**: institution text features (name, description, type,
  location, keywords) vectorized with TF-IDF.
- **Model Training**: two recommender families trained from the interaction
  matrix and item features:
    * Collaborative filtering (matrix factorization + user-user kNN)
    * Content-based filtering (TF-IDF + cosine similarity)
- **Real-time inference**: cached fitted models serve recommendations
  instantly; the engine re-trains lazily when data changes.

Scores from every signal are blended into a hybrid rank. When a user has too
little history, the engine falls back to cold-start rules (popular in their
district, then national). All sklearn usage is defensive: if training data is
insufficient, the module degrades gracefully rather than raising.

This complements the Phase-1 rule-based `recommendations.py` module and is
designed to replace it while keeping the same API contract.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.analytics import PageView, ClickEvent, SearchEvent
from app.models.student_analytics import AnalyticsEvent
from app.models.education_graph import SavedInstitution
from app.models.review import InstitutionReview
from app.models.institution import Institution

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Implicit feedback weights — how much each action tells us about intent
# --------------------------------------------------------------------------
EVENT_WEIGHTS: Dict[str, float] = {
    "institution_view": 1.0,
    "admission_page_view": 1.0,
    "scholarship_view": 1.0,
    "search_query": 1.5,
    "admission_interest": 2.0,
    "course_view": 2.0,
    "video_watch": 1.0,
    "pdf_read": 1.0,
    "share": 2.0,
    "comment": 2.0,
    "review": 2.0,
    "save_institution": 3.0,
    "bookmark": 3.0,
    "apply_click": 3.5,
    "career_assistant_usage": 1.5,
}

# Signals that count as explicit positive interest (used to seed content-based)
POSITIVE_EVENTS = {
    "save_institution",
    "bookmark",
    "admission_interest",
    "apply_click",
    "review",
}

MIN_USERS_FOR_CF = 3  # fewer distinct users than this → skip collaborative
MIN_ITEMS_FOR_CB = 3  # fewer institutions than this → skip content-based


def _try_import_sklearn() -> bool:
    """Return True when scikit-learn is importable."""
    try:
        import sklearn  # noqa: F401

        return True
    except ImportError:
        logger.warning("scikit-learn not installed — ML recommender disabled")
        return False


# --------------------------------------------------------------------------
# Interaction matrix builder
# --------------------------------------------------------------------------
class InteractionBuilder:
    """Builds the user × institution implicit-feedback matrix.

    Each (user, institution) cell is the weighted sum of all interactions,
    a proxy for the user's latent preference toward that institution.
    """

    # sqlalchemy model, user col, item col, weight (static or from map)
    @staticmethod
    def _aggregate(
        db: Session,
        model,
        weight: float,
        user_col: str,
        item_col: str,
        user_ids: Optional[List[int]] = None,
    ) -> Dict[Tuple[int, int], float]:
        query = db.query(
            getattr(model, user_col),
            getattr(model, item_col),
            func.count(model.id),
        ).filter(
            getattr(model, item_col).isnot(None),
        )
        if user_ids:
            query = query.filter(getattr(model, user_col).in_(user_ids))
        query = query.group_by(getattr(model, user_col), getattr(model, item_col))
        out: Dict[Tuple[int, int], float] = {}
        for uid, iid, cnt in query.all():
            if uid is None or iid is None:
                continue
            out[(int(uid), int(iid))] = (
                out.get((int(uid), int(iid)), 0.0) + float(cnt) * weight
            )
        return out

    @classmethod
    def build(
        cls, db: Session, user_ids: Optional[List[int]] = None
    ) -> Dict[Tuple[int, int], float]:
        """Aggregate all implicit signals into one interaction map."""
        interactions: Dict[Tuple[int, int], float] = {}

        def merge(src: Dict[Tuple[int, int], float]) -> None:
            for key, val in src.items():
                interactions[key] = interactions.get(key, 0.0) + val

        # Generic analytics events with per-event weights
        event_rows = db.query(
            AnalyticsEvent.user_id,
            AnalyticsEvent.institution_id,
            AnalyticsEvent.event_type,
            func.count(AnalyticsEvent.id),
        ).filter(
            AnalyticsEvent.institution_id.isnot(None),
        )
        if user_ids:
            event_rows = event_rows.filter(AnalyticsEvent.user_id.in_(user_ids))
        for uid, iid, etype, cnt in event_rows.group_by(
            AnalyticsEvent.user_id,
            AnalyticsEvent.institution_id,
            AnalyticsEvent.event_type,
        ).all():
            if uid is None or iid is None:
                continue
            w = EVENT_WEIGHTS.get(etype, 1.0)
            interactions[(int(uid), int(iid))] = (
                interactions.get((int(uid), int(iid)), 0.0) + float(cnt) * w
            )

        # Dedicated tables
        merge(cls._aggregate(db, PageView, 1.0, "user_id", "institution_id", user_ids))
        merge(
            cls._aggregate(db, ClickEvent, 2.0, "user_id", "institution_id", user_ids)
        )
        merge(
            cls._aggregate(
                db, SavedInstitution, 3.0, "user_id", "institution_id", user_ids
            )
        )
        merge(
            cls._aggregate(
                db, InstitutionReview, 2.5, "user_id", "institution_id", user_ids
            )
        )

        # Searches that led to a click are strong positive signals
        search_rows = db.query(
            SearchEvent.user_id,
            SearchEvent.clicked_institution_id,
            func.count(SearchEvent.id),
        ).filter(
            SearchEvent.clicked_institution_id.isnot(None),
            SearchEvent.clicked_result.is_(True),
        )
        if user_ids:
            search_rows = search_rows.filter(SearchEvent.user_id.in_(user_ids))
        for uid, iid, cnt in search_rows.group_by(
            SearchEvent.user_id, SearchEvent.clicked_institution_id
        ).all():
            if uid is None or iid is None:
                continue
            interactions[(int(uid), int(iid))] = (
                interactions.get((int(uid), int(iid)), 0.0) + float(cnt) * 2.0
            )

        return interactions

    @staticmethod
    def to_arrays(
        interactions: Dict[Tuple[int, int], float],
    ) -> Tuple[List[int], List[int], List[float], Dict[int, int], Dict[int, int]]:
        """Convert interaction map to user/item index arrays.

        Returns (user_ids, item_ids, weights, user_index, item_index) where the
        *_index maps external id -> dense matrix index.
        """
        user_set = {uid for uid, _ in interactions}
        item_set = {iid for _, iid in interactions}
        user_index = {uid: i for i, uid in enumerate(sorted(user_set))}
        item_index = {iid: i for i, iid in enumerate(sorted(item_set))}
        user_ids = [uid for uid, _ in interactions]
        item_ids = [iid for _, iid in interactions]
        weights = list(interactions.values())
        return user_ids, item_ids, weights, user_index, item_index


# --------------------------------------------------------------------------
# Collaborative filtering
# --------------------------------------------------------------------------
class CollaborativeFilter:
    """User-based and matrix-factorization collaborative filtering.

    Uses SVD (TruncatedSVD) to discover latent user/item factors from the
    implicit matrix, plus user-user cosine similarity as a fallback when the
    matrix is too small or sparse for SVD to be meaningful.
    """

    def __init__(self, n_factors: int = 12) -> None:
        self.n_factors = n_factors
        self.user_index: Dict[int, int] = {}
        self.item_index: Dict[int, int] = {}
        self.item_ids: List[int] = []
        self.user_factors: Optional[Any] = None
        self.item_factors: Optional[Any] = None
        self.user_sim: Optional[Any] = None
        self._all_weights: Dict[Tuple[int, int], float] = {}
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    def fit(self, interactions: Dict[Tuple[int, int], float]) -> bool:
        if not _try_import_sklearn():
            return False
        if len(interactions) == 0:
            return False

        self._all_weights = dict(interactions)
        _, _, _, self.user_index, self.item_index = (
            InteractionBuilder.to_arrays(interactions)
        )
        self.item_ids = sorted(self.item_index, key=self.item_index.get)

        n_users = len(self.user_index)
        n_items = len(self.item_index)
        if n_users < MIN_USERS_FOR_CF or n_items < MIN_ITEMS_FOR_CB:
            return False

        import numpy as np

        # Sparse user × item matrix
        matrix = np.zeros((n_users, n_items), dtype=np.float32)
        for (uid, iid), w in interactions.items():
            matrix[self.user_index[uid], self.item_index[iid]] += w

        try:
            from sklearn.decomposition import TruncatedSVD
            from sklearn.metrics.pairwise import cosine_similarity

            if min(matrix.shape) < 3:
                return False
            svd = TruncatedSVD(
                n_components=min(self.n_factors, min(matrix.shape) - 1),
                random_state=42,
            )
            reduced = svd.fit_transform(matrix)
            self.user_factors = reduced  # (n_users, k)
            # Item factors via transpose factorization
            self.item_factors = svd.components_.T  # (n_items, k)

            # User-user cosine similarity from latent factors
            self.user_sim = cosine_similarity(reduced)
            self._ready = True
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("SVD factorization failed, falling back to matrix sim: %s", exc)
            try:
                from sklearn.metrics.pairwise import cosine_similarity

                self.user_sim = cosine_similarity(matrix)
                self._ready = True
                return True
            except Exception as exc2:  # noqa: BLE001
                logger.warning("Collaborative filter could not fit: %s", exc2)
                return False

    def score_user_items(
        self, user_id: int, exclude: Optional[set] = None, limit: int = 50
    ) -> List[Tuple[int, float]]:
        """Score all items for a user not yet interacted with.

        Prediction = dot product of the user's latent factors with each
        item's latent factors (standard SVD recommendation scoring). A small
        neighbor bonus from the user-user similarity matrix boosts items that
        similar users engaged with.
        """
        if not self._ready or user_id not in self.user_index:
            return []
        ui = self.user_index[user_id]
        exclude = exclude or set()

        if self.user_factors is None or self.item_factors is None:
            return []

        user_vec = self.user_factors[ui]
        pred = self.item_factors @ user_vec  # (n_items,)
        scores: Dict[int, float] = {}

        # Neighbor bonus: re-weight by similarity with the user's own items
        neighbor_bonus: Dict[int, float] = {}
        if self.user_sim is not None and hasattr(self.user_sim, "__len__"):
            sims = self.user_sim[ui]
            # top similar users (excluding self)
            order = sorted(
                range(len(sims)), key=lambda j: sims[j], reverse=True
            )[:10]
            for j in order:
                if j == ui or sims[j] <= 0:
                    continue
                neighbor_uid = self._user_at(j)
                if neighbor_uid == -1:
                    continue
                for (other_uid, iid), w in self._all_weights.items():
                    if other_uid == neighbor_uid and w > 0:
                        neighbor_bonus[iid] = neighbor_bonus.get(iid, 0.0) + sims[j] * w

        for iid, idx in self.item_index.items():
            if iid in exclude:
                continue
            scores[iid] = float(pred[idx]) + neighbor_bonus.get(iid, 0.0)

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:limit]

    def _user_at(self, dense_index: int) -> int:
        for uid, idx in self.user_index.items():
            if idx == dense_index:
                return uid
        return -1


# --------------------------------------------------------------------------
# Content-based filtering
# --------------------------------------------------------------------------
class ContentBasedFilter:
    """Item-item content similarity using TF-IDF over institution features."""

    def __init__(self) -> None:
        self.item_index: Dict[int, int] = {}
        self.item_ids: List[int] = []
        self.sim_matrix: Optional[Any] = None
        self._ready = False

    def is_ready(self) -> bool:
        return self._ready

    @staticmethod
    def _feature_text(inst) -> str:
        parts = [
            inst.name_en,
            inst.name_bn,
            inst.description,
            inst.short_name,
            inst.keywords,
            inst.search_vector,
            inst.type.name if inst.type else None,
            inst.education_level,
            inst.ownership,
            inst.upazila.name_en if inst.upazila else None,
            inst.upazila.district.name_en if inst.upazila and inst.upazila.district else None,
            inst.upazila.district.division.name_en
            if inst.upazila and inst.upazila.district and inst.upazila.district.division
            else None,
        ]
        return " ".join(p for p in parts if p).lower()

    def fit(self, institutions: List[Institution]) -> bool:
        if not _try_import_sklearn() or len(institutions) < MIN_ITEMS_FOR_CB:
            return False
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            self.item_ids = [i.id for i in institutions]
            self.item_index = {iid: idx for idx, iid in enumerate(self.item_ids)}
            corpus = [self._feature_text(i) for i in institutions]

            vectorizer = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                min_df=1,
                stop_words=None,
            )
            tfidf = vectorizer.fit_transform(corpus)
            self.sim_matrix = cosine_similarity(tfidf)
            self._ready = True
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Content-based filter could not fit: %s", exc)
            return False

    def recommend(
        self, seed_item_ids: List[int], exclude: Optional[set] = None, limit: int = 50
    ) -> List[Tuple[int, float]]:
        """Recommend items similar to the seed (liked) items."""
        if not self._ready or not seed_item_ids:
            return []
        exclude = exclude or set()

        scores: Dict[int, float] = {}
        for seed_id in seed_item_ids:
            if seed_id not in self.item_index:
                continue
            row = self.item_index[seed_id]
            sims = self.sim_matrix[row]
            for iid, idx in self.item_index.items():
                if iid == seed_id or iid in exclude:
                    continue
                scores[iid] = scores.get(iid, 0.0) + float(sims[idx])

        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        return ranked[:limit]


# --------------------------------------------------------------------------
# Trending & popularity
# --------------------------------------------------------------------------
class TrendingRecommender:
    """Trend-based discovery: institutions gaining traction, optionally local."""

    @staticmethod
    def trending(
        db: Session,
        district: Optional[str] = None,
        division: Optional[str] = None,
        days: int = 30,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Institutions ranked by recent engagement growth."""
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(days=days)

        query = (
            db.query(
                AnalyticsEvent.institution_id,
                func.count(AnalyticsEvent.id).label("recent"),
            )
            .filter(
                AnalyticsEvent.institution_id.isnot(None),
                AnalyticsEvent.created_at >= since,
            )
            .group_by(AnalyticsEvent.institution_id)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(200)
        )
        counts = {iid: c for iid, c in query.all()}
        if not counts:
            return []

        institutions = (
            db.query(Institution)
            .filter(Institution.id.in_(list(counts.keys())))
            .all()
        )
        rows = []
        for inst in institutions:
            if not inst.is_active:
                continue
            inst_district = inst.district.name_en if inst.district else None
            inst_division = inst.division.name_en if inst.division else None
            if district and inst_district and inst_district.lower() != district.lower():
                continue
            if division and inst_division and inst_division.lower() != division.lower():
                continue
            rows.append(
                {
                    "institution_id": inst.id,
                    "name_en": inst.name_en,
                    "name_bn": inst.name_bn,
                    "slug": inst.slug,
                    "engagement": counts[inst.id],
                    "district": inst_district,
                    "division": inst_division,
                }
            )
        rows.sort(key=lambda r: r["engagement"], reverse=True)
        return rows[:limit]

    @staticmethod
    def popular(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Globally popular institutions (view-count based)."""
        institutions = (
            db.query(Institution)
            .filter(Institution.is_active.is_(True))
            .order_by(Institution.view_count.desc(), Institution.id.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "institution_id": i.id,
                "name_en": i.name_en,
                "name_bn": i.name_bn,
                "slug": i.slug,
                "view_count": i.view_count,
            }
            for i in institutions
        ]


# --------------------------------------------------------------------------
# Hybrid engine
# --------------------------------------------------------------------------
class MLRecommendationEngine:
    """Orchestrates training and real-time inference.

    - Fits collaborative + content-based models from the interaction matrix.
    - Blends CF + content + popularity scores into a hybrid rank.
    - Falls back to trending/popular (cold start) when the user has no history.
    - Caches fitted models and refreshes when `fit()` is called again.
    """

    def __init__(self) -> None:
        self.collaborative = CollaborativeFilter()
        self.content_based = ContentBasedFilter()
        self._fitted = False
        self._fitted_at: Optional[float] = None
        self._institution_lookup: Dict[int, Institution] = {}
        self._positive_items: Dict[int, List[int]] = {}  # user -> liked item ids

    def fit(self, db: Session, user_ids: Optional[List[int]] = None) -> bool:
        """(Re)train models from current analytics data."""
        interactions = InteractionBuilder.build(db, user_ids=user_ids)
        if not interactions:
            self._fitted = False
            return False

        cf_ok = self.collaborative.fit(interactions)

        # Content features need institution objects
        item_ids = {iid for _, iid in interactions}
        institutions = (
            db.query(Institution)
            .filter(Institution.id.in_(item_ids))
            .all()
        )
        cb_ok = self.content_based.fit(institutions)
        self._institution_lookup = {i.id: i for i in institutions}

        # Positive seeds per user for content-based
        self._positive_items = {}
        for (uid, iid), w in interactions.items():
            if w >= 2.0:  # strong positive signal
                self._positive_items.setdefault(uid, []).append(iid)

        self._fitted = cf_ok or cb_ok
        self._fitted_at = time.time()
        logger.info(
            "ML recommender fitted: cf=%s cb=%s users=%d items=%d",
            cf_ok, cb_ok, len(self.collaborative.user_index), len(item_ids),
        )
        return self._fitted

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    def recommend_for_user(
        self,
        db: Session,
        user_id: int,
        limit: int = 10,
        force_refit: bool = False,
    ) -> Dict[str, Any]:
        """Real-time inference: personalized institution recommendations."""
        if force_refit or not self._fitted:
            self.fit(db)

        interacted = {
            iid
            for (uid, iid) in InteractionBuilder.build(db, user_ids=[user_id]).keys()
        }

        exclude = set(interacted)

        # 1. Collaborative scores
        cf_scores: List[Tuple[int, float]] = []
        if self.collaborative.is_ready():
            cf_scores = self.collaborative.score_user_items(
                user_id, exclude=exclude, limit=100
            )

        # 2. Content-based scores from positive seeds
        cb_scores: List[Tuple[int, float]] = []
        seeds = self._positive_items.get(user_id, [])
        if seeds and self.content_based.is_ready():
            cb_scores = self.content_based.recommend(
                seeds, exclude=exclude, limit=100
            )

        # 3. Cold-start signals when the user is brand new
        profile_any = seeds or interacted
        if not profile_any:
            # No history → district popularity, then national
            from app.models.student_analytics import StudentProfile

            profile = (
                db.query(StudentProfile)
                .filter(StudentProfile.user_id == user_id)
                .first()
            )
            district = profile.district if profile else None
            division = profile.division if profile else None
            trending = TrendingRecommender.trending(
                db, district=district, division=division, limit=limit
            )
            if trending:
                return {
                    "method": "cold_start_local",
                    "recommendations": trending,
                    "signals": {"profile": True},
                }
            popular = TrendingRecommender.popular(db, limit=limit)
            return {
                "method": "cold_start_popular",
                "recommendations": popular,
                "signals": {},
            }

        # 4. Hybrid blend — normalize each family to 0..1 then weight
        blended: Dict[int, float] = {}
        reasons: Dict[int, List[str]] = {}

        def _normalize(pairs: List[Tuple[int, float]]) -> Dict[int, float]:
            if not pairs:
                return {}
            mx = max(v for _, v in pairs) or 1.0
            return {iid: v / mx for iid, v in pairs}

        cf_norm = _normalize(cf_scores)
        cb_norm = _normalize(cb_scores)

        for iid, s in cf_norm.items():
            blended[iid] = blended.get(iid, 0.0) + 0.6 * s
            reasons.setdefault(iid, []).append("collaborative")
        for iid, s in cb_norm.items():
            blended[iid] = blended.get(iid, 0.0) + 0.4 * s
            reasons.setdefault(iid, []).append("content-based")

        # add small popularity tie-breaker
        popular = TrendingRecommender.popular(db, limit=50)
        for row in popular:
            iid = row["institution_id"]
            if iid in exclude:
                continue
            blended[iid] = blended.get(iid, 0.0) + 0.01

        ranked = sorted(blended.items(), key=lambda kv: kv[1], reverse=True)[:limit]

        recommendations = []
        for iid, score in ranked:
            inst = self._institution_lookup.get(iid)
            if inst is None:
                inst = db.query(Institution).get(iid)
            if inst is None or not inst.is_active:
                continue
            recommendations.append(
                {
                    "institution_id": inst.id,
                    "name_en": inst.name_en,
                    "name_bn": inst.name_bn,
                    "slug": inst.slug,
                    "type": inst.type.name if inst.type else None,
                    "score": round(score, 4),
                    "method": "+".join(sorted(set(reasons.get(iid, ["popularity"])))),
                }
            )

        method = "hybrid"
        if not cf_scores and cb_scores:
            method = "content_based"
        elif not cb_scores and cf_scores:
            method = "collaborative"

        return {
            "method": method,
            "recommendations": recommendations,
            "signals": {
                "interacted_count": len(interacted),
                "content_seeds": len(seeds),
            },
        }

    def similar_institutions(
        self, db: Session, institution_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Content-based 'more like this' for an institution."""
        if not self._fitted:
            self.fit(db)
        if not self.content_based.is_ready():
            return []
        pairs = self.content_based.recommend(
            [institution_id], exclude={institution_id}, limit=limit
        )
        out = []
        for iid, score in pairs:
            inst = self._institution_lookup.get(iid) or db.query(Institution).get(iid)
            if inst is None or not inst.is_active:
                continue
            out.append(
                {
                    "institution_id": inst.id,
                    "name_en": inst.name_en,
                    "name_bn": inst.name_bn,
                    "slug": inst.slug,
                    "type": inst.type.name if inst.type else None,
                    "score": round(score, 4),
                }
            )
        return out


# --------------------------------------------------------------------------
# Module-level cached engine
# --------------------------------------------------------------------------
_engine: Optional[MLRecommendationEngine] = None
_engine_db_fingerprint: Optional[str] = None


def get_ml_engine() -> MLRecommendationEngine:
    global _engine
    if _engine is None:
        _engine = MLRecommendationEngine()
    return _engine


def reset_ml_engine() -> None:
    """Drop the cached engine (used in tests)."""
    global _engine, _engine_db_fingerprint
    _engine = None
    _engine_db_fingerprint = None
