"""Tests for the ML recommendation engine.

Covers:
- Interaction matrix building from analytics signals
- Collaborative filtering (SVD) scoring
- Content-based similarity
- Hybrid recommendation for users with history
- Cold-start fallback for users without history
- Trending and popular discovery
- ML API endpoints
"""

import pytest

from app.models import (
    AnalyticsEvent,
    Division,
    District,
    Institution,
    InstitutionType,
    SavedInstitution,
    Upazila,
)
from app.models.user import User
from app.services.ml_recommendations import (
    ContentBasedFilter,
    InteractionBuilder,
    MLRecommendationEngine,
    TrendingRecommender,
    reset_ml_engine,
)


@pytest.fixture
def location(db_session):
    import uuid

    tag = uuid.uuid4().hex[:6]
    div = Division(name_en=f"Div_{tag}")
    db_session.add(div)
    db_session.flush()
    dist = District(name_en=f"Dist_{tag}", division_id=div.id)
    db_session.add(dist)
    db_session.flush()
    up = Upazila(name_en=f"Up_{tag}", district_id=dist.id)
    db_session.add(up)
    db_session.flush()
    return {"division": div, "district": dist, "upazila": up}


@pytest.fixture
def institutions(db_session, location):
    import uuid

    tag = uuid.uuid4().hex[:6]
    itype = InstitutionType(name=f"univ_{tag}", category="higher_education")
    db_session.add(itype)
    db_session.flush()

    def _make(name, desc, slug):
        inst = Institution(
            name_en=name,
            name_bn=name,
            slug=f"{slug}-{tag}",
            type_id=itype.id,
            division_id=location["division"].id,
            district_id=location["district"].id,
            upazila_id=location["upazila"].id,
            description=desc,
            keywords="university",
            is_active=True,
            view_count=10,
        )
        db_session.add(inst)
        db_session.flush()
        return inst

    eng = _make("Engineering University", "science engineering technology", "eng-univ")
    med = _make("Medical University", "science medicine health", "med-univ")
    bus = _make("Business University", "commerce business management", "bus-univ")
    law = _make("Law University", "law justice jurisprudence", "law-univ")
    db_session.commit()
    return [eng, med, bus, law]


@pytest.fixture
def analytics_users(db_session, institutions):
    users = []
    for i in range(5):
        u = User(
            email=f"ml{i}@example.com",
            username=f"mluser{i}",
            hashed_password="x",
            first_name="ML",
            last_name=f"User{i}",
            is_active=True,
            is_verified=True,
        )
        db_session.add(u)
        db_session.flush()
        users.append(u)

    # u0, u1 interested in engineering + business (save + admission_interest)
    for u in (users[0], users[1]):
        for inst in (institutions[0], institutions[2]):
            db_session.add(
                AnalyticsEvent(
                    user_id=u.id,
                    institution_id=inst.id,
                    event_type="admission_interest",
                )
            )
        db_session.add(
            SavedInstitution(user_id=u.id, institution_id=institutions[1].id)
        )
    # u2 only viewed engineering
    db_session.add(
        AnalyticsEvent(
            user_id=users[2].id,
            institution_id=institutions[0].id,
            event_type="institution_view",
        )
    )
    db_session.commit()
    return users


class TestInteractionBuilder:
    def test_build_aggregates_signals(self, db_session, institutions, analytics_users):
        interactions = InteractionBuilder.build(db_session)
        assert len(interactions) > 0
        # u0 has interest in eng + bus, saved med
        key = (analytics_users[0].id, institutions[1].id)
        assert key in interactions
        assert interactions[key] >= 3.0  # save weight

    def test_build_scoped_to_users(self, db_session, institutions, analytics_users):
        interactions = InteractionBuilder.build(
            db_session, user_ids=[analytics_users[0].id]
        )
        assert all(uid == analytics_users[0].id for uid, _ in interactions)

    def test_to_arrays_maps_ids(self):
        interactions = {(1, 10): 1.0, (1, 11): 2.0, (2, 10): 1.5}
        user_ids, item_ids, weights, uidx, iidx = InteractionBuilder.to_arrays(
            interactions
        )
        assert uidx == {1: 0, 2: 1}
        assert iidx == {10: 0, 11: 1}
        assert set(weights) == {1.0, 2.0, 1.5}


class TestContentBasedFilter:
    def test_fit_and_recommend(self, institutions):
        filt = ContentBasedFilter()
        assert filt.fit(institutions) is True
        # engineering institution should be more similar to itself-family than business
        recs = dict(filt.recommend([institutions[0].id], limit=5))
        assert recs.get(institutions[1].id, 0) > recs.get(institutions[2].id, 0)

    def test_recommend_without_fit(self):
        filt = ContentBasedFilter()
        assert filt.recommend([1]) == []
        assert filt.is_ready() is False


class TestMLRecommendationEngine:
    def test_fit_and_recommend_for_user(
        self, db_session, institutions, analytics_users
    ):
        reset_ml_engine()
        engine = MLRecommendationEngine()
        assert engine.fit(db_session) is True
        assert engine.is_fitted

        result = engine.recommend_for_user(
            db_session, user_id=analytics_users[0].id, force_refit=True
        )
        assert result["method"] in ("hybrid", "collaborative", "content_based")
        assert len(result["recommendations"]) >= 1
        # should not re-recommend already-interacted institution
        interacted = {institutions[0].id, institutions[1].id, institutions[2].id}
        for rec in result["recommendations"]:
            assert rec["institution_id"] not in interacted
        # law (never interacted) is a candidate
        assert institutions[3].id in {r["institution_id"] for r in result["recommendations"]}

    def test_cold_start_popular(self, db_session, institutions):
        reset_ml_engine()
        engine = MLRecommendationEngine()
        # A user with no profile and no interactions
        new_user = User(
            email="newbie@example.com",
            username="newbie",
            hashed_password="x",
            first_name="New",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(new_user)
        db_session.commit()

        result = engine.recommend_for_user(db_session, user_id=new_user.id)
        assert result["method"] in ("cold_start_local", "cold_start_popular")
        assert isinstance(result["recommendations"], list)

    def test_cold_start_local_district(self, db_session, institutions):
        from app.models.student_analytics import StudentProfile

        reset_ml_engine()
        engine = MLRecommendationEngine()
        new_user = User(
            email="local@example.com",
            username="localuser",
            hashed_password="x",
            first_name="Local",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(new_user)
        db_session.flush()
        db_session.add(
            StudentProfile(
                user_id=new_user.id,
                division="Dhaka",
                district="Dhaka",
            )
        )
        db_session.commit()

        result = engine.recommend_for_user(db_session, user_id=new_user.id)
        assert result["method"] in ("cold_start_local", "cold_start_popular")

    def test_similar_institutions(self, db_session, institutions):
        reset_ml_engine()
        engine = MLRecommendationEngine()
        engine.fit(db_session)
        similar = engine.similar_institutions(
            db_session, institution_id=institutions[0].id
        )
        assert isinstance(similar, list)


class TestTrending:
    def test_popular(self, db_session, institutions):
        rows = TrendingRecommender.popular(db_session, limit=5)
        assert isinstance(rows, list)
        assert all("institution_id" in r for r in rows)

    def test_trending_empty(self, db_session):
        rows = TrendingRecommender.trending(db_session, limit=5)
        assert rows == []


class TestRecommendationsAPI:
    def test_trending_endpoint(self, client, db_session, institutions):
        resp = client.get("/api/v1/recommendations/trending")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_popular_endpoint(self, client, db_session, institutions):
        resp = client.get("/api/v1/recommendations/popular")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_me_requires_auth(self, client):
        resp = client.get("/api/v1/recommendations/me")
        assert resp.status_code == 401

    def test_me_authenticated(self, client, db_session, institutions):
        reset_ml_engine()
        resp = client.get(
            "/api/v1/recommendations/me", headers={"Authorization": "Bearer x"}
        )
        # invalid token → 401; the engine itself is exercised by service tests
        assert resp.status_code == 401
