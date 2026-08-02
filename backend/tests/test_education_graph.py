"""Tests for the national education knowledge graph schema.

Covers:
- Enhanced Institution fields (ownership, education_level, eiin,
  verification_level, division/district FKs)
- Campuses CRUD
- Facility types + institution facilities
- Gallery
- Rankings & accreditations
- Admissions, notices, scholarships
- Course offerings (institution_courses join)
- Saved institutions (authenticated users)
- Graph metadata endpoint

Note: the shared test conftest uses an in-memory SQLite StaticPool; fixture
ORM objects can be expired by interleaved client requests, so all plain
values (ids, names, auth headers) are captured before the first client call.
"""

from app.core.security import create_access_token
from app.models import (
    Course,
    CourseType,
    District,
    Division,
    FacilityType,
    Institution,
    InstitutionType,
    Upazila,
    User,
    UserRole,
)

_counter = {"user": 0, "inst": 0, "course": 0}


def _next(key: str) -> int:
    _counter[key] += 1
    return _counter[key]


def _user_headers(user: User) -> dict:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _make_user(db_session, role=UserRole.ADMIN):
    """Create a unique user; return (auth_headers, user_id) as plain values."""
    key = _next("user")
    user = User(
        email=f"graph-admin{key}@example.com",
        username=f"graphadmin{key}",
        hashed_password="hash",
        first_name="Admin",
        last_name="User",
        role=role,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    headers = _user_headers(user)
    user_id = user.id
    return headers, user_id


def _make_institution(db_session):
    """Create a unique institution; return its id."""
    key = _next("inst")
    inst_type = InstitutionType(name=f"university{key}", category="higher_education")
    db_session.add(inst_type)
    db_session.flush()
    inst = Institution(
        name_en=f"Graph University {key}",
        name_bn=f"গ্রাফ বিশ্ববিদ্যালয় {key}",
        slug=f"graph-university-{key}",
        type_id=inst_type.id,
        established_year=1995,
        ownership="private",
        education_level="degree",
        eiin=f"EIIN{100000 + key}",
        board="dhaka",
        university_affiliation="University of Dhaka",
        ugc_approved=True,
        verification_level=2,
        status="active",
    )
    db_session.add(inst)
    db_session.commit()
    return inst.id


def _make_course(db_session):
    """Create a unique course; return (course_id, course_name)."""
    key = _next("course")
    ctype = CourseType(name=f"BSc{key}", category="undergraduate")
    db_session.add(ctype)
    db_session.flush()
    course = Course(
        name_en=f"Computer Science {key}",
        slug=f"computer-science-{key}",
        course_type_id=ctype.id,
        duration_years=4,
        total_credits=140,
        semester_system="semester",
    )
    db_session.add(course)
    db_session.commit()
    return course.id, course.name_en


def test_institution_enhanced_fields(db_session):
    inst = db_session.query(Institution).get(_make_institution(db_session))
    assert inst.ownership == "private"
    assert inst.education_level == "degree"
    assert inst.eiin is not None
    assert inst.board == "dhaka"
    assert inst.ugc_approved is True
    assert inst.verification_level == 2
    assert inst.status == "active"
    assert inst.facebook is None
    assert inst.logo is None
    assert inst.division_id is None
    assert inst.district_id is None


def test_institution_location_relationships(db_session):
    division = Division(name_en="Dhaka", name_bn="ঢাকা", code="DHA")
    db_session.add(division)
    db_session.flush()
    district = District(name_en="Dhaka", code="DHA-D", division_id=division.id)
    db_session.add(district)
    db_session.flush()
    upazila = Upazila(name_en="Dhanmondi", code="DHA-DM", district_id=district.id)
    db_session.add(upazila)
    db_session.flush()

    inst_id = _make_institution(db_session)
    inst = db_session.query(Institution).get(inst_id)
    inst.division_id = division.id
    inst.district_id = district.id
    inst.upazila_id = upazila.id
    db_session.commit()

    db_session.refresh(inst)
    assert inst.division.name_en == "Dhaka"
    assert inst.district.name_en == "Dhaka"
    assert inst.upazila.name_en == "Dhanmondi"


def test_campus_crud(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    # create
    resp = client.post(
        "/api/v1/campuses",
        json={
            "institution_id": inst_id,
            "name_en": "Main Campus",
            "campus_type": "main",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    campus_id = resp.json()["id"]

    # list by institution (public)
    resp = client.get(f"/api/v1/institutions/{inst_id}/campuses")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # get single
    resp = client.get(f"/api/v1/campuses/{campus_id}")
    assert resp.status_code == 200
    assert resp.json()["name_en"] == "Main Campus"

    # update
    resp = client.put(
        f"/api/v1/campuses/{campus_id}",
        json={"name_en": "Permanent Campus", "is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name_en"] == "Permanent Campus"

    # delete
    resp = client.delete(f"/api/v1/campuses/{campus_id}", headers=admin_headers)
    assert resp.status_code == 204
    resp = client.get(f"/api/v1/institutions/{inst_id}/campuses")
    assert len(resp.json()) == 0


def test_campus_write_requires_admin(client, db_session):
    regular_headers, _ = _make_user(db_session, role=UserRole.USER)
    inst_id = _make_institution(db_session)
    resp = client.post(
        "/api/v1/campuses",
        json={"institution_id": inst_id, "name_en": "X"},
        headers=regular_headers,
    )
    assert resp.status_code == 403


def test_facilities(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    ftype = FacilityType(name=f"library{_next('inst')}", icon="book")
    db_session.add(ftype)
    db_session.commit()
    ftype_id = ftype.id
    ftype_name = ftype.name

    # add facility to institution (authed write first commits the shared txn)
    resp = client.post(
        f"/api/v1/institutions/{inst_id}/facilities",
        json={"facility_type_id": ftype_id, "is_available": True, "capacity": 500},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    fac_id = resp.json()["id"]

    # duplicate -> conflict
    resp = client.post(
        f"/api/v1/institutions/{inst_id}/facilities",
        json={"facility_type_id": ftype_id},
        headers=admin_headers,
    )
    assert resp.status_code == 409

    # list facility types (public)
    resp = client.get("/api/v1/facilities/types")
    assert resp.status_code == 200
    assert any(f["name"] == ftype_name for f in resp.json())

    # list institution facilities
    resp = client.get(f"/api/v1/institutions/{inst_id}/facilities")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # remove
    resp = client.delete(
        f"/api/v1/institutions/{inst_id}/facilities/{fac_id}", headers=admin_headers
    )
    assert resp.status_code == 204


def test_gallery(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    resp = client.post(
        f"/api/v1/institutions/{inst_id}/gallery",
        json={
            "url": "https://example.com/photo.jpg",
            "title": "Library",
            "category": "building",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    image_id = resp.json()["id"]

    resp = client.get(f"/api/v1/institutions/{inst_id}/gallery")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Library"

    resp = client.delete(f"/api/v1/gallery/{image_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_rankings_and_accreditations(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    resp = client.post(
        f"/api/v1/institutions/{inst_id}/rankings",
        json={
            "ranking_type": "national",
            "category": "engineering",
            "year": 2026,
            "rank": 3,
            "score": 87.5,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    rank_id = resp.json()["id"]

    resp = client.get(f"/api/v1/institutions/{inst_id}/rankings")
    assert resp.status_code == 200
    assert resp.json()[0]["rank"] == 3

    resp = client.post(
        f"/api/v1/institutions/{inst_id}/accreditations",
        json={
            "accrediting_body": "BAETE",
            "certificate_number": "BAETE-001",
            "status": "active",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    acc_id = resp.json()["id"]

    resp = client.get(f"/api/v1/institutions/{inst_id}/accreditations")
    assert resp.status_code == 200
    assert resp.json()[0]["accrediting_body"] == "BAETE"

    resp = client.delete(f"/api/v1/rankings/{rank_id}", headers=admin_headers)
    assert resp.status_code == 204
    resp = client.delete(f"/api/v1/accreditations/{acc_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_admissions_crud(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    resp = client.post(
        "/api/v1/admissions",
        json={
            "institution_id": inst_id,
            "title": "BSc Admission 2026",
            "session": "2025-26",
            "minimum_gpa": 3.5,
            "total_seats": 120,
            "application_fee": 1000,
            "status": "open",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    admission_id = resp.json()["id"]
    assert resp.json()["minimum_gpa"] == 3.5

    # list public
    resp = client.get(f"/api/v1/institutions/{inst_id}/admissions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # filter by status
    resp = client.get(f"/api/v1/institutions/{inst_id}/admissions?status=closed")
    assert resp.json() == []

    # update
    resp = client.put(
        f"/api/v1/admissions/{admission_id}",
        json={"status": "closed", "minimum_gpa": 3.75},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["minimum_gpa"] == 3.75

    # get single
    resp = client.get(f"/api/v1/admissions/{admission_id}")
    assert resp.status_code == 200

    resp = client.delete(f"/api/v1/admissions/{admission_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_notices_crud(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    resp = client.post(
        "/api/v1/notices",
        json={
            "institution_id": inst_id,
            "title": "Exam Routine",
            "category": "examination",
            "is_important": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    notice_id = resp.json()["id"]

    resp = client.get(f"/api/v1/institutions/{inst_id}/notices")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Exam Routine"

    resp = client.put(
        f"/api/v1/notices/{notice_id}",
        json={"category": "result"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["category"] == "result"

    resp = client.delete(f"/api/v1/notices/{notice_id}", headers=admin_headers)
    assert resp.status_code == 204


def test_scholarships_crud(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)

    resp = client.post(
        "/api/v1/scholarships",
        json={
            "institution_id": inst_id,
            "name": "Merit Scholarship",
            "amount": 25000,
            "scholarship_type": "merit",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    scholarship_id = resp.json()["id"]

    resp = client.get(f"/api/v1/institutions/{inst_id}/scholarships")
    assert resp.status_code == 200
    assert resp.json()[0]["amount"] == 25000

    resp = client.put(
        f"/api/v1/scholarships/{scholarship_id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    resp = client.delete(
        f"/api/v1/scholarships/{scholarship_id}", headers=admin_headers
    )
    assert resp.status_code == 204


def test_course_offerings(client, db_session):
    admin_headers, _ = _make_user(db_session)
    inst_id = _make_institution(db_session)
    course_id, course_name = _make_course(db_session)

    resp = client.post(
        f"/api/v1/institutions/{inst_id}/courses",
        json={
            "course_id": course_id,
            "total_seats": 80,
            "shift": "day",
            "fee": 45000,
            "language": "english",
            "status": "open",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["course_name"] == course_name
    offering_id = resp.json()["id"]

    # duplicate -> conflict
    resp = client.post(
        f"/api/v1/institutions/{inst_id}/courses",
        json={"course_id": course_id, "status": "open"},
        headers=admin_headers,
    )
    assert resp.status_code == 409

    # list with course name
    resp = client.get(f"/api/v1/institutions/{inst_id}/courses")
    assert resp.status_code == 200
    assert resp.json()[0]["course_name"] == course_name

    # update
    resp = client.put(
        f"/api/v1/institution-courses/{offering_id}",
        json={"fee": 50000, "status": "closed"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["fee"] == 50000

    resp = client.delete(
        f"/api/v1/institution-courses/{offering_id}", headers=admin_headers
    )
    assert resp.status_code == 204


def test_saved_institutions(client, db_session):
    user_headers, _ = _make_user(db_session, role=UserRole.USER)
    inst_id = _make_institution(db_session)
    inst_slug = f"graph-university-{_counter['inst']}"

    # not authenticated
    resp = client.post(f"/api/v1/me/saved/{inst_id}", json={"note": "want to apply"})
    assert resp.status_code == 401

    # save
    resp = client.post(
        f"/api/v1/me/saved/{inst_id}",
        json={"note": "want to apply"},
        headers=user_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["institution_name"] == f"Graph University {_counter['inst']}"

    # duplicate -> conflict
    resp = client.post(f"/api/v1/me/saved/{inst_id}", json={}, headers=user_headers)
    assert resp.status_code == 409

    # list
    resp = client.get("/api/v1/me/saved", headers=user_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["institution_slug"] == inst_slug

    # get single
    resp = client.get(f"/api/v1/me/saved/{inst_id}", headers=user_headers)
    assert resp.status_code == 200

    # unsave
    resp = client.delete(f"/api/v1/me/saved/{inst_id}", headers=user_headers)
    assert resp.status_code == 204
    resp = client.get("/api/v1/me/saved", headers=user_headers)
    assert resp.json() == []


def test_graph_metadata(client):
    resp = client.get("/api/v1/meta/institution-types")
    assert resp.status_code == 200
    data = resp.json()
    assert "private" in data["ownerships"]
    assert "degree" in data["education_levels"]
    assert "active" in data["statuses"]
    assert data["verification_levels"] == [0, 1, 2, 3]


def test_models_registered():
    from app.core.database import Base

    tables = set(Base.metadata.tables.keys())
    for table in (
        "campuses",
        "facility_types",
        "institution_facilities",
        "gallery_images",
        "institution_rankings",
        "accreditations",
        "admissions",
        "notices",
        "scholarships",
        "institution_courses",
        "saved_institutions",
    ):
        assert table in tables, f"missing table {table}"
