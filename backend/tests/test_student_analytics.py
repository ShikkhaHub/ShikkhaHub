"""Tests for the ShikkhaHub Student Data Analytics implementation.

Covers:
- Student 360 profile CRUD
- Consent & privacy governance
- Event tracking (with anonymous fallback)
- AI student profile generation
- Learning analytics
- Segmentation
- Recommendations
- Institutional analytics dashboard
- National insights

Note: the shared test conftest uses a persistent in-memory SQLite DB
(StaticPool), so every fixture uses unique identifiers to avoid collisions.
"""

import json
from types import SimpleNamespace

import pytest

from app.core.security import create_access_token
from app.models.institution import Institution, InstitutionType, InstitutionRequirement
from app.models.student_analytics import AnalyticsEvent, StudentProfile, StudySession
from app.models.user import User, UserRole

_counter = {"user": 0, "inst": 0}


def _next_user_key():
    _counter["user"] += 1
    return _counter["user"]


def _next_inst_key():
    _counter["inst"] += 1
    return _counter["inst"]


def _make_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student(db_session):
    """Create a unique student user + full profile + auth headers."""
    key = _next_user_key()
    user = User(
        email=f"student{key}@example.com",
        username=f"student{key}",
        hashed_password="hash",
        first_name="Rahim",
        last_name="Uddin",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = StudentProfile(
        user_id=user.id,
        full_name="Rahim Uddin",
        age=19,
        gender="male",
        current_level="HSC",
        education_board="Dhaka",
        current_institution="Dhaka College",
        department="Science",
        expected_graduation="2027",
        gpa_history=json.dumps(
            [
                {"level": "SSC", "gpa": 5.0},
                {"level": "HSC", "gpa": 4.8},
            ]
        ),
        academic_interests=json.dumps(["Engineering", "CSE", "ICT"]),
        division="Dhaka",
        district="Dhaka",
        upazila="Dhanmondi",
        dream_career="Software Engineer",
        interested_sectors=json.dumps(["IT", "Software"]),
        preferred_university="Dhaka University",
        preferred_subject="CSE",
        expected_salary=60000,
        abroad_interest=True,
        scholarship_interest=True,
        annual_income=300000,
        favorite_subjects=json.dumps(["Math", "ICT"]),
        weak_subjects=json.dumps(["Physics"]),
        study_hours_per_week=20,
        learning_style="Visual",
        analytics_consent=True,
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return _make_headers(user), user.id, profile.id


@pytest.fixture
def student_without_consent(db_session):
    """Student user with NO analytics consent."""
    key = _next_user_key()
    user = User(
        email=f"noconsent{key}@example.com",
        username=f"noconsent{key}",
        hashed_password="hash",
        role=UserRole.USER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return _make_headers(user), user.id


@pytest.fixture
def admin(db_session):
    """Create a unique admin user + auth headers."""
    key = _next_user_key()
    user = User(
        email=f"admin{key}@example.com",
        username=f"admin{key}",
        hashed_password="hash",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return _make_headers(user), user.id


@pytest.fixture
def institution(db_session):
    """Create a unique institution with admission + scholarship requirements."""
    key = _next_inst_key()
    inst_type = db_session.query(InstitutionType).filter_by(name="university").first()
    if inst_type is None:
        inst_type = InstitutionType(name="university", category="higher_education")
        db_session.add(inst_type)
        db_session.flush()

    inst = Institution(
        name_en=f"Dhaka University {key}",
        short_name="DU",
        slug=f"dhaka-university-{key}",
        type_id=inst_type.id,
        description="A top public university offering Engineering, Science and Business programs",
        keywords="engineering, science, business, cse, medical",
        is_active=True,
        view_count=100,
    )
    db_session.add(inst)
    db_session.flush()

    db_session.add(
        InstitutionRequirement(
            institution_id=inst.id,
            requirement_type="admission",
            level="undergraduate",
            min_gpa=4.0,
        )
    )
    db_session.add(
        InstitutionRequirement(
            institution_id=inst.id,
            requirement_type="scholarship",
            level="undergraduate",
            min_gpa=4.5,
            application_process="Apply online",
        )
    )
    db_session.commit()
    db_session.refresh(inst)
    return SimpleNamespace(id=inst.id, name=inst.name_en)


# ---------------------------------------------------------------------------
# Student profile
# ---------------------------------------------------------------------------


class TestStudentProfile:
    def test_update_and_get_profile(self, client, student):
        headers, user_id, _ = student
        resp = client.post(
            "/api/v1/students/profile",
            headers=headers,
            json={
                "full_name": "Karim Ahmed",
                "age": 20,
                "current_level": "University",
                "dream_career": "Doctor",
                "gpa_history": [{"level": "SSC", "gpa": 5.0}],
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["profile"]["current_level"] == "University"
        assert body["profile"]["dream_career"] == "Doctor"
        assert body["profile"]["gpa_history"] == [{"level": "SSC", "gpa": 5.0}]

        resp = client.get("/api/v1/students/me/profile", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["profile"]["user_id"] == user_id

    def test_profile_requires_auth(self, client):
        assert client.get("/api/v1/students/me/profile").status_code == 401

    def test_student_360_dashboard(self, client, student):
        headers, user_id, _ = student
        resp = client.get("/api/v1/students/me", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["profile"]["user_id"] == user_id
        assert "ai_profile" in body
        assert "segments" in body
        assert "learning" in body
        assert body["analytics_consent"] is True


# ---------------------------------------------------------------------------
# Consent & privacy
# ---------------------------------------------------------------------------


class TestConsent:
    def test_grant_and_revoke_consent(self, client, student_without_consent):
        headers, user = student_without_consent
        resp = client.post(
            "/api/v1/students/consent",
            headers=headers,
            json={
                "granted": True,
                "consent_type": "analytics",
                "consent_version": "1.0",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["analytics_consent"] is True
        assert len(resp.json()["history"]) == 1

        resp = client.post(
            "/api/v1/students/consent",
            headers=headers,
            json={
                "granted": False,
                "consent_type": "analytics",
                "consent_version": "1.0",
            },
        )
        assert resp.json()["analytics_consent"] is False
        assert len(resp.json()["history"]) == 2

        resp = client.get("/api/v1/students/consent/history", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()["history"]) == 2


# ---------------------------------------------------------------------------
# Event tracking
# ---------------------------------------------------------------------------


class TestEventTracking:
    def test_track_event_with_consent(self, client, db_session, institution, student):
        headers, user_id, _ = student
        resp = client.post(
            "/api/v1/analytics/track/event",
            headers=headers,
            json={
                "event_type": "institution_view",
                "institution_id": institution.id,
                "subject": "Engineering",
                "event_data": {"query": "Dhaka University"},
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["is_anonymous"] is False

        event = (
            db_session.query(AnalyticsEvent)
            .filter(AnalyticsEvent.user_id == user_id)
            .first()
        )
        assert event is not None
        assert event.event_type == "institution_view"
        assert event.institution_id == institution.id

    def test_track_event_without_consent_is_anonymous(
        self, client, db_session, student_without_consent
    ):
        headers, user = student_without_consent
        resp = client.post(
            "/api/v1/analytics/track/event",
            headers=headers,
            json={"event_type": "institution_view", "subject": "Math"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["is_anonymous"] is True

        event = (
            db_session.query(AnalyticsEvent).order_by(AnalyticsEvent.id.desc()).first()
        )
        assert event.user_id is None
        assert event.is_anonymous is True

    def test_track_event_public(self, client, db_session):
        resp = client.post(
            "/api/v1/analytics/track/event",
            json={"event_type": "institution_view", "subject": "Physics"},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_track_study_session(self, client, db_session, student):
        headers, user_id, _ = student
        resp = client.post(
            "/api/v1/analytics/track/study",
            headers=headers,
            json={
                "subject": "Math",
                "duration_minutes": 45,
                "lessons_completed": 3,
                "quiz_accuracy": 85.0,
                "average_score": 78.0,
                "content_type": "video",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True

        session = (
            db_session.query(StudySession)
            .filter(StudySession.user_id == user_id)
            .first()
        )
        assert session is not None
        assert session.duration_minutes == 45
        assert session.quiz_accuracy == 85.0


# ---------------------------------------------------------------------------
# AI profile, learning, segments
# ---------------------------------------------------------------------------


class TestAIProfileAndLearning:
    def test_ai_profile_generation(self, client, student):
        headers, _, _ = student
        resp = client.get("/api/v1/students/me/ai-profile", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["student_type"] == "Admission Focused"
        assert body["risk_score"] in ["Low", "Medium", "High"]
        assert 0 <= body["recommendation_score"] <= 100
        assert "Math" in body["strong_subjects"]
        assert "Dhaka University" in body["interested_universities"]

    def test_segmentation(self, client, student):
        headers, _, _ = student
        resp = client.get("/api/v1/students/me/segments", headers=headers)
        assert resp.status_code == 200
        labels = [s["label"] for s in resp.json()["segments"]]
        assert "HSC Students" in labels
        assert "Engineering Aspirants" in labels
        assert "Study Abroad Students" in labels
        assert "Scholarship Seekers" in labels
        assert "Admission Candidates" in labels

    def test_learning_analytics(self, client, student):
        headers, _, _ = student
        resp = client.get("/api/v1/students/me/learning", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "total_minutes" in body
        assert "avg_quiz_accuracy" in body
        assert "learning_streak" in body
        assert "subject_performance" in body


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class TestRecommendations:
    def test_institution_recommendations(self, client, institution, student):
        headers, _, _ = student
        resp = client.get(
            "/api/v1/students/me/recommendations/institutions", headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        for tier in ["best_matches", "safety", "competitive", "dream"]:
            assert tier in body
        all_recs = (
            body["best_matches"] + body["safety"] + body["competitive"] + body["dream"]
        )
        assert any(r["institution_id"] == institution.id for r in all_recs)

    def test_course_recommendations(self, client, student):
        headers, _, _ = student
        resp = client.get(
            "/api/v1/students/me/recommendations/courses", headers=headers
        )
        assert resp.status_code == 200
        assert "courses" in resp.json()

    def test_scholarship_recommendations(self, client, institution, student):
        headers, _, _ = student
        resp = client.get(
            "/api/v1/students/me/recommendations/scholarships", headers=headers
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "scholarships" in body
        assert any(s["institution_id"] == institution.id for s in body["scholarships"])

    def test_all_recommendations(self, client, institution, student):
        headers, _, _ = student
        resp = client.get("/api/v1/students/me/recommendations", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert {"institutions", "courses", "scholarships"} <= set(body.keys())


# ---------------------------------------------------------------------------
# Institutional dashboard & national insights
# ---------------------------------------------------------------------------


class TestInstitutionalAndNational:
    def test_institution_analytics_dashboard(self, client, institution, admin):
        headers, _ = admin
        resp = client.get(
            f"/api/v1/institutions/{institution.id}/analytics",
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["institution_id"] == institution.id
        assert "interest" in body
        assert "geography" in body
        assert "academic_interest" in body

    def test_institution_analytics_requires_admin(self, client, institution, student):
        headers, _, _ = student
        resp = client.get(
            f"/api/v1/institutions/{institution.id}/analytics",
            headers=headers,
        )
        assert resp.status_code == 403

    def test_national_insights(self, client, admin):
        headers, _ = admin
        resp = client.get("/api/v1/admin/analytics/national-insights", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        for key in [
            "most_searched_universities",
            "fastest_growing_subjects",
            "regional_demand",
            "career_trends",
            "digital_learning",
        ]:
            assert key in body

    def test_behavioral_analytics(self, client, admin):
        headers, _ = admin
        resp = client.get("/api/v1/admin/analytics/behavioral", headers=headers)
        assert resp.status_code == 200
        body = resp.json()["snapshot"]
        for key in [
            "most_viewed_institutions",
            "popular_subjects",
            "search_trends",
            "peak_study_hours",
            "avg_session_duration_seconds",
            "bounce_rate",
            "ai_usage_frequency",
        ]:
            assert key in body
