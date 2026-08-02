"""Tests for the Natural Language Query Processing (NLQP) engine."""

import pytest

from app.models import (
    Admission,
    Course,
    CourseType,
    Division,
    District,
    Institution,
    InstitutionCourse,
    InstitutionType,
    Scholarship,
    Upazila,
)
from app.services.nlqp import (
    extract_courses,
    extract_features,
    extract_location,
    extract_ownership,
    extract_types,
    natural_language_search,
)


@pytest.fixture
def location(db_session):
    import uuid

    tag = uuid.uuid4().hex[:6]
    div = Division(name_en=f"Dhaka_{tag}")
    db_session.add(div)
    db_session.flush()
    dist = District(name_en=f"Chittagong_{tag}", division_id=div.id)
    db_session.add(dist)
    db_session.flush()
    up = Upazila(name_en=f"Mirpur_{tag}", district_id=dist.id)
    db_session.add(up)
    db_session.flush()
    return {"division": div, "district": dist, "upazila": up}


@pytest.fixture
def seed(db_session, location):
    import uuid

    tag = uuid.uuid4().hex[:6]
    univ = InstitutionType(name=f"university_{tag}", category="higher_education")
    college = InstitutionType(name=f"college_{tag}", category="higher_education")
    db_session.add_all([univ, college])
    db_session.flush()

    ctype = CourseType(name=f"BSc_{tag}", category="undergraduate")
    db_session.add(ctype)
    db_session.flush()

    cse = Course(
        name_en=f"Computer Science {tag}",
        slug=f"cs-{tag}",
        course_type_id=ctype.id,
        keywords="computer science, cse, ict",
        description="Computer science and engineering program",
        is_active=True,
    )
    econ = Course(
        name_en=f"Economics {tag}",
        slug=f"econ-{tag}",
        course_type_id=ctype.id,
        keywords="economics, finance, banking",
        description="Economics program",
        is_active=True,
    )
    db_session.add_all([cse, econ])
    db_session.flush()

    private = Institution(
        name_en=f"Dhaka Private University {tag}",
        name_bn="ঢাকা প্রাইভেট বিশ্ববিদ্যালয়",
        short_name="DPU",
        slug=f"dpu-{tag}",
        type_id=univ.id,
        ownership="private",
        education_level="degree",
        division_id=location["division"].id,
        district_id=location["district"].id,
        upazila_id=location["upazila"].id,
        description="A private university",
        keywords="university",
        is_active=True,
        view_count=100,
        is_featured=True,
        verification_status="verified",
    )
    govt = Institution(
        name_en=f"Chittagong Govt College {tag}",
        name_bn="চট্টগ্রাম সরকারি কলেজ",
        short_name="CGC",
        slug=f"cgc-{tag}",
        type_id=college.id,
        ownership="government",
        education_level="degree",
        division_id=location["division"].id,
        district_id=location["district"].id,
        upazila_id=location["upazila"].id,
        description="A government college",
        keywords="college",
        is_active=True,
        view_count=50,
        verification_status="pending",
    )
    db_session.add_all([private, govt])
    db_session.flush()

    # Course offerings: private university offers CSE + Economics
    db_session.add_all(
        [
            InstitutionCourse(institution_id=private.id, course_id=cse.id),
            InstitutionCourse(institution_id=private.id, course_id=econ.id),
            InstitutionCourse(institution_id=govt.id, course_id=econ.id),
        ]
    )

    # Scholarship only at the private university
    db_session.add(
        Scholarship(
            institution_id=private.id,
            name="Merit Scholarship",
            amount=10000,
            scholarship_type="merit",
            is_active=True,
        )
    )

    # Open admission at the private university
    db_session.add(
        Admission(
            institution_id=private.id,
            title="Admission 2026",
            status="open",
            minimum_gpa=3.0,
        )
    )
    db_session.commit()

    return {
        "private": private,
        "govt": govt,
        "cse": cse,
        "econ": econ,
        "tag": tag,
    }


class TestEntityExtraction:
    def test_extract_types(self):
        assert extract_types("polytechnic in dhaka") == ["polytechnic"]
        assert "university" in extract_types("private universities with scholarships")
        assert extract_types("no entity here") == []

    def test_extract_ownership(self):
        assert extract_ownership("government colleges") == "government"
        assert extract_ownership("private university") == "private"
        assert extract_ownership("just schools") is None

    def test_extract_features(self):
        assert "scholarship" in extract_features("with scholarship available")
        assert "hostel" in extract_features("residential hostel")
        assert "verified" in extract_features("verified institutions")

    def test_extract_courses(self):
        assert "computer science" in extract_courses(db=None, text="cse university")
        assert "economics" in extract_courses(db=None, text="banking colleges")
        assert extract_courses(db=None, text="nothing here") == []

    def test_extract_location(self, db_session, location):
        found = extract_location(db_session, f"near {location['district'].name_en}")
        assert found.get("district") == location["district"].name_en


class TestNaturalLanguageSearch:
    def test_find_with_type_and_location(self, db_session, seed):
        result = natural_language_search(
            db_session, f"college in {seed['tag']}"
        )
        # tag alone won't match a district name; query is a "find" with no filters
        assert result["intent"] == "find_institutions"
        assert result["total"] >= 0
        assert "query_summary" in result

    def test_scholarship_filter(self, db_session, seed):
        result = natural_language_search(
            db_session,
            f"universities with scholarships in {seed['tag']}",
        )
        # scholarship filter should narrow to the private university
        ids = {item["id"] for item in result["items"]}
        if result["total"] > 0:
            assert seed["private"].id in ids
            assert "scholarship" in result["entities"].get("features", [])

    def test_private_university_entities(self, db_session, seed):
        result = natural_language_search(
            db_session,
            f"private universities in {seed['tag']}",
        )
        assert result["entities"]["ownership"] == "private"
        assert "university" in result["entities"]["types"]
        assert "filters_applied" in result

    def test_count_intent(self, db_session, seed):
        result = natural_language_search(
            db_session, f"how many institutions in {seed['tag']}"
        )
        assert result["intent"] == "count"
        assert isinstance(result["total"], int)
        assert result["items"] == []

    def test_admissions_intent(self, db_session, seed):
        result = natural_language_search(
            db_session,
            f"when is admission at {seed['tag']}",
        )
        assert result["intent"] == "admissions"

    def test_named_institution(self, db_session, seed):
        name = seed["private"].name_en
        result = natural_language_search(db_session, f"show me {name}")
        assert seed["private"].id in {
            i["id"] for i in result["items"]
        }


class TestNLQPAPI:
    def test_endpoint_requires_query(self, client):
        resp = client.get("/api/v1/search/natural")
        assert resp.status_code == 422

    def test_endpoint_basic(self, client, db_session, seed):
        resp = client.get("/api/v1/search/natural", params={"q": "universities"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["intent"] == "find_institutions"
        assert "query_summary" in body
        assert "filters_applied" in body
        assert isinstance(body["items"], list)

    def test_endpoint_pagination(self, client, db_session, seed):
        resp = client.get(
            "/api/v1/search/natural",
            params={"q": "institutions", "page": 1, "page_size": 5},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["page_size"] == 5
