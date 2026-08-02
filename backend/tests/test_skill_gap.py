"""Tests for Predictive Skill Gap Analysis."""

import uuid

import pytest

from app.models import (
    Division,
    District,
    Institution,
    InstitutionType,
    Upazila,
)
from app.models.course import Course, CourseType
from app.models.skills import (
    InstitutionSkill,
    MarketDemand,
    Skill,
    SkillGapAnalysis,
)
from app.models.user import User, UserRole
from app.core.security import create_access_token, get_password_hash
from app.services import skill_gap


def _admin_auth(db_session):
    """Create a unique admin user and mint a token directly.

    Avoids the shared `admin_headers` fixture whose fixed email collides
    across tests in the session-scoped test DB.
    """
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    admin = User(
        email=email,
        username=f"admin_{uuid.uuid4().hex[:6]}",
        hashed_password=get_password_hash("pw123456"),
        first_name="A",
        last_name="U",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    token = create_access_token({"sub": str(admin.id)})
    return {"Authorization": f"Bearer {token}"}


def _unique(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:6]}"


def sample_institution(db):
    tag = uuid.uuid4().hex[:6]
    div = Division(name_en=f"Div_{tag}")
    db.add(div)
    db.flush()
    dist = District(name_en=f"Dist_{tag}", division_id=div.id)
    db.add(dist)
    db.flush()
    up = Upazila(name_en=f"Up_{tag}", district_id=dist.id)
    db.add(up)
    db.flush()
    itype = InstitutionType(name=f"univ_{tag}", category="higher_education")
    db.add(itype)
    db.flush()
    inst = Institution(
        name_en=f"Skill University {tag}",
        slug=f"skill-univ-{tag}",
        type_id=itype.id,
        division_id=div.id,
        district_id=dist.id,
        upazila_id=up.id,
        is_active=True,
        view_count=1,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _skill(db, name=None):
    name = name or _unique("Skill")
    s = Skill(
        name=name,
        name_bn=f"{name}_bn",
        category="technical",
        subcategory="data",
        description="test skill",
        keywords=f"{name}, data, analytics",
        skill_level="intermediate",
        is_active=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _demand(db, skill, year, score, quarter=None):
    d = MarketDemand(
        skill_id=skill.id,
        year=year,
        quarter=quarter,
        demand_score=score,
        postings_count=int(score * 10),
        hiring_growth_pct=5.0,
        source="test",
        industry_sector="it",
        region="national",
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


def _link(db, institution, skill, course_id=None):
    link = InstitutionSkill(
        institution_id=institution.id,
        skill_id=skill.id,
        derivation="curriculum_nlp",
        confidence=0.7,
        source_course_id=course_id,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


# ---------------------------------------------------------------------------
# Forecast / scoring unit tests
# ---------------------------------------------------------------------------


def test_classify_status(db_session):
    assert skill_gap.classify_status(20) == "deficit"
    assert skill_gap.classify_status(0) == "balanced"
    assert skill_gap.classify_status(-20) == "surplus"


def test_forecast_rising_trend(db_session):
    s = _skill(db_session)
    for year, score in ((2022, 40), (2023, 55), (2024, 70), (2025, 85)):
        _demand(db_session, s, year, score)
    forecast, trend = skill_gap.forecast_demand(db_session, s.id)
    assert trend == "rising"
    assert forecast is not None
    assert forecast >= 85


def test_forecast_single_point_stable(db_session):
    s = _skill(db_session)
    _demand(db_session, s, 2025, 60)
    forecast, trend = skill_gap.forecast_demand(db_session, s.id)
    assert trend == "stable"
    assert forecast == 60.0


def test_forecast_no_data_stable(db_session):
    s = _skill(db_session)
    forecast, trend = skill_gap.forecast_demand(db_session, s.id)
    assert trend == "stable"
    assert forecast is None


def test_supply_scores_normalize(db_session):
    inst1 = sample_institution(db_session)
    inst2 = sample_institution(db_session)
    s1 = _skill(db_session)
    s2 = _skill(db_session)
    _link(db_session, inst1, s1)
    _link(db_session, inst2, s1)
    _link(db_session, inst1, s2)
    scores = skill_gap.compute_supply_scores(db_session)
    assert scores[s1.id] == 100.0
    assert scores[s2.id] == 50.0


def test_demand_scores_latest_signal(db_session):
    s = _skill(db_session)
    _demand(db_session, s, 2023, 50)
    _demand(db_session, s, 2024, 80)
    scores = skill_gap.compute_demand_scores(db_session)
    assert scores[s.id] == 80.0


# ---------------------------------------------------------------------------
# Curriculum NLP derivation
# ---------------------------------------------------------------------------


def test_supply_from_curriculum_matches_keyword(db_session):
    inst = sample_institution(db_session)
    ctype = CourseType(name=_unique("CourseType"), category="undergraduate")
    db_session.add(ctype)
    db_session.commit()
    db_session.refresh(ctype)
    course = Course(
        name_en=_unique("CourseName"),
        slug=_unique("course-slug"),
        institution_id=inst.id,
        course_type_id=ctype.id,
        description="Covers data analytics and business intelligence in depth.",
        is_active=True,
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    s = _skill(db_session, name=_unique("DataAnalytics"))
    s.keywords = "data analytics"
    db_session.commit()

    derived = skill_gap.supply_from_curriculum(db_session)
    payload = derived.get(inst.id)
    assert payload is not None
    assert s.id in payload["skill_ids"]
    assert payload["matched_course_ids"][s.id] == course.id


def test_sync_institution_skills_no_duplicate(db_session):
    inst = sample_institution(db_session)
    s = _skill(db_session)
    _link(db_session, inst, s)
    result = skill_gap.sync_institution_skills(db_session)
    assert result["updated"] == 0
    count = (
        db_session.query(InstitutionSkill)
        .filter(InstitutionSkill.institution_id == inst.id)
        .count()
    )
    assert count == 1


# ---------------------------------------------------------------------------
# Full analysis pipeline
# ---------------------------------------------------------------------------


def test_run_full_analysis_persists_gaps(db_session):
    s = _skill(db_session)
    for year, score in ((2023, 50), (2024, 70), (2025, 90)):
        _demand(db_session, s, year, score)
    inst1 = sample_institution(db_session)
    inst2 = sample_institution(db_session)
    _link(db_session, inst1, s)
    _link(db_session, inst2, s)

    result = skill_gap.run_full_analysis(db_session)
    assert result["analyzed"] >= 1

    gap = (
        db_session.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.skill_id == s.id)
        .first()
    )
    assert gap is not None
    assert gap.demand_score == 90.0
    assert gap.supply_score == 100.0
    assert gap.gap_score == pytest.approx(-10.0)
    assert gap.status == "balanced"
    assert gap.trend in ("rising", "stable")
    assert gap.forecast_demand is not None
    assert gap.methodology == "trend_extrapolation+supply_curriculum"


def test_run_full_analysis_deficit_flag(db_session):
    s = _skill(db_session)
    for year, score in ((2023, 40), (2024, 60), (2025, 80)):
        _demand(db_session, s, year, score)

    skill_gap.run_full_analysis(db_session)
    gap = (
        db_session.query(SkillGapAnalysis)
        .filter(SkillGapAnalysis.skill_id == s.id)
        .first()
    )
    assert gap is not None
    assert gap.supply_score == 0.0
    assert gap.gap_score == pytest.approx(80.0)
    assert gap.status == "deficit"


def test_emerging_skills_ranked(db_session):
    s = _skill(db_session)
    for year, score in ((2023, 40), (2024, 60), (2025, 80)):
        _demand(db_session, s, year, score)
    skill_gap.run_full_analysis(db_session)
    emerging = skill_gap.get_emerging_skills(db_session)
    assert any(e["skill"]["id"] == s.id for e in emerging)
    assert all(e["trend"] == "rising" for e in emerging)
    assert all(e["status"] == "deficit" for e in emerging)


def test_gap_report_and_institution_skills(db_session):
    s = _skill(db_session)
    for year, score in ((2024, 60), (2025, 70)):
        _demand(db_session, s, year, score)
    inst = sample_institution(db_session)
    _link(db_session, inst, s)
    skill_gap.run_full_analysis(db_session)

    report = skill_gap.get_gap_report(db_session)
    assert report["total"] >= 1
    assert any(item["skill"]["id"] == s.id for item in report["items"])

    inst_skills = skill_gap.get_institution_skills(db_session, inst.id)
    assert any(row["skill_id"] == s.id for row in inst_skills)
    assert all(row["status"] is not None for row in inst_skills)


def test_student_recommendations_return_emerging(db_session):
    s = _skill(db_session)
    for year, score in ((2023, 40), (2024, 60), (2025, 80)):
        _demand(db_session, s, year, score)
    skill_gap.run_full_analysis(db_session)
    recs = skill_gap.recommend_student_skills(db_session, limit=10)
    assert isinstance(recs, list)
    assert len(recs) > 0
    assert all(r["trend"] == "rising" for r in recs)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


def test_api_emerging_endpoint(db_session, client):
    s = _skill(db_session)
    sid = s.id
    for year, score in ((2023, 40), (2024, 60), (2025, 80)):
        _demand(db_session, s, year, score)
    skill_gap.run_full_analysis(db_session)
    resp = client.get("/api/v1/skills/emerging")
    assert resp.status_code == 200
    body = resp.json()
    assert any(item["skill"]["id"] == sid for item in body)


def test_api_gap_report_endpoint(db_session, client):
    s = _skill(db_session)
    sid = s.id
    for year, score in ((2024, 60), (2025, 70)):
        _demand(db_session, s, year, score)
    skill_gap.run_full_analysis(db_session)
    resp = client.get("/api/v1/skills/gap-report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(item["skill"]["id"] == sid for item in body["items"])


def test_api_skill_detail_endpoint(db_session, client):
    s = _skill(db_session)
    sid = s.id
    sname = s.name
    _demand(db_session, s, 2025, 65)
    resp = client.get(f"/api/v1/skills/skills/{sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sid
    assert body["name"] == sname
    assert len(body["demand_series"]) >= 1


def test_api_skill_detail_not_found(client):
    resp = client.get("/api/v1/skills/skills/999999")
    assert resp.status_code == 404


def test_api_institution_skill_gaps(db_session, client):
    inst = sample_institution(db_session)
    s = _skill(db_session)
    sid = s.id
    _link(db_session, inst, s)
    resp = client.get(f"/api/v1/skills/institutions/{inst.id}/skill-gaps")
    assert resp.status_code == 200
    body = resp.json()
    assert any(row["skill_id"] == sid for row in body)


def test_api_institution_not_found(client):
    resp = client.get("/api/v1/skills/institutions/999999/skill-gaps")
    assert resp.status_code == 404


def test_api_admin_create_skill_requires_auth(client, db_session):
    resp = client.post(
        "/api/v1/skills/admin/skills",
        json={"name": _unique("AdminSkill"), "category": "technical"},
    )
    assert resp.status_code == 401


def test_api_admin_create_skill(db_session, client):
    headers = _admin_auth(db_session)
    resp = client.post(
        "/api/v1/skills/admin/skills",
        json={"name": _unique("AdminSkill"), "category": "technical"},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"].startswith("AdminSkill")


def test_api_admin_create_skill_duplicate(db_session, client):
    s = _skill(db_session)
    headers = _admin_auth(db_session)
    resp = client.post(
        "/api/v1/skills/admin/skills",
        json={"name": s.name, "category": "technical"},
        headers=headers,
    )
    assert resp.status_code == 409


def test_api_admin_add_demand_requires_auth(client):
    resp = client.post(
        "/api/v1/skills/admin/market-demand",
        json={"skill_id": 1, "year": 2025, "demand_score": 50},
    )
    assert resp.status_code == 401


def test_api_admin_add_demand(db_session, client):
    s = _skill(db_session)
    headers = _admin_auth(db_session)
    resp = client.post(
        "/api/v1/skills/admin/market-demand",
        json={"skill_id": s.id, "year": 2026, "demand_score": 75},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["demand_score"] == 75


def test_api_admin_run_analysis(db_session, client):
    s = _skill(db_session)
    for year, score in ((2024, 60), (2025, 75)):
        _demand(db_session, s, year, score)
    headers = _admin_auth(db_session)
    resp = client.post("/api/v1/skills/admin/analyze", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["analyzed"] >= 1
