"""Tests for the Augmented Reality (AR) campus tour feature."""

import pytest

from app.models import (
    Campus,
    CampusPOI,
    CampusTour,
    Division,
    District,
    Institution,
    InstitutionType,
    TourStop,
    Upazila,
)
from app.models.ar import ARAsset
from app.services.ar_tours import (
    ARTourService,
    bearing_deg,
    haversine_m,
    walk_minutes,
)


@pytest.fixture
def ar_campus(db_session):
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

    itype = InstitutionType(name=f"univ_{tag}", category="higher_education")
    db_session.add(itype)
    db_session.flush()

    inst = Institution(
        name_en=f"AR University {tag}",
        slug=f"ar-univ-{tag}",
        type_id=itype.id,
        division_id=div.id,
        district_id=dist.id,
        upazila_id=up.id,
        is_active=True,
        view_count=10,
    )
    db_session.add(inst)
    db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        name_en=f"Main Campus {tag}",
        latitude=23.8103,
        longitude=90.4125,
        is_active=True,
    )
    db_session.add(campus)
    db_session.flush()

    # POIs laid out ~100m apart
    gate = CampusPOI(
        campus_id=campus.id,
        institution_id=inst.id,
        name_en="Main Gate",
        category="gate",
        latitude=23.8103,
        longitude=90.4125,
        is_active=True,
    )
    lib = CampusPOI(
        campus_id=campus.id,
        institution_id=inst.id,
        name_en="Central Library",
        category="library",
        latitude=23.8103 + 0.001,
        longitude=90.4125,
        is_active=True,
    )
    db_session.add_all([gate, lib])
    db_session.flush()

    # Attach a lightweight asset to the library
    db_session.add(
        ARAsset(
            poi_id=lib.id,
            asset_type="image",
            url="https://cdn.example/marker.jpg",
            size_kb=30,
            format="jpeg",
            is_primary=True,
        )
    )

    tour = CampusTour(
        campus_id=campus.id,
        institution_id=inst.id,
        title="Highlights Tour",
        difficulty="easy",
    )
    db_session.add(tour)
    db_session.flush()

    db_session.add_all(
        [
            TourStop(tour_id=tour.id, poi_id=gate.id, position=1, dwell_seconds=30),
            TourStop(tour_id=tour.id, poi_id=lib.id, position=2, dwell_seconds=45),
        ]
    )
    db_session.commit()

    return {
        "campus": campus,
        "inst": inst,
        "gate": gate,
        "lib": lib,
        "tour": tour,
    }


class TestGeoMath:
    def test_haversine_zero(self):
        assert haversine_m(23.8, 90.4, 23.8, 90.4) == 0.0

    def test_haversine_known_distance(self):
        # ~111km per degree of latitude
        d = haversine_m(23.8, 90.4, 24.8, 90.4)
        assert 110000 < d < 112000

    def test_bearing_north(self):
        b = bearing_deg(23.8, 90.4, 24.0, 90.4)
        assert b is not None and abs(b - 0.0) < 5

    def test_bearing_east(self):
        b = bearing_deg(23.8, 90.4, 23.8, 90.6)
        assert b is not None and abs(b - 90.0) < 5

    def test_walk_minutes(self):
        assert walk_minutes(420) == 5.0  # 420m at 1.4 m/s = 5 min


class TestARTourService:
    def test_find_nearby(self, db_session, ar_campus):
        result = ARTourService.find_nearby(
            db_session,
            lat=ar_campus["gate"].latitude,
            lng=ar_campus["gate"].longitude,
            radius_m=500,
        )
        assert result["total"] >= 1
        # nearest POI should be the gate itself
        assert result["items"][0]["poi"]["id"] == ar_campus["gate"].id
        assert result["items"][0]["distance_m"] == 0.0
        assert "estimated_walk_minutes" in result["items"][0]

    def test_find_nearby_out_of_range(self, db_session, ar_campus):
        result = ARTourService.find_nearby(
            db_session, lat=25.0, lng=90.0, radius_m=100
        )
        assert result["total"] == 0

    def test_find_nearby_category_filter(self, db_session, ar_campus):
        result = ARTourService.find_nearby(
            db_session,
            lat=ar_campus["gate"].latitude,
            lng=ar_campus["gate"].longitude,
            radius_m=1000,
            category="library",
        )
        assert result["total"] == 1
        assert result["items"][0]["poi"]["category"] == "library"

    def test_list_campus_pois(self, db_session, ar_campus):
        pois = ARTourService.list_campus_pois(db_session, ar_campus["campus"].id)
        assert len(pois) == 2

    def test_poi_assets_serialized(self, db_session, ar_campus):
        pois = ARTourService.list_campus_pois(db_session, ar_campus["campus"].id)
        lib = next(p for p in pois if p["category"] == "library")
        assert len(lib["assets"]) == 1
        assert lib["assets"][0]["asset_type"] == "image"

    def test_guided_tour_wayfinding(self, db_session, ar_campus):
        guide = ARTourService.guided_tour(db_session, ar_campus["tour"].id)
        assert guide is not None
        assert len(guide["steps"]) == 2
        # step 2 should have a distance leg from step 1
        assert guide["steps"][1]["distance_from_prev_m"] is not None
        assert guide["steps"][1]["bearing_from_prev_deg"] is not None
        assert guide["total_distance_m"] > 0

    def test_get_tour_not_found(self, db_session):
        assert ARTourService.get_tour(db_session, 999999) is None


class TestARAPI:
    def test_nearby_endpoint(self, client, db_session, ar_campus):
        resp = client.get(
            "/api/v1/ar/nearby",
            params={
                "lat": ar_campus["gate"].latitude,
                "lng": ar_campus["gate"].longitude,
                "radius_m": 500,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert "distance_m" in body["items"][0]

    def test_nearby_requires_coords(self, client):
        resp = client.get("/api/v1/ar/nearby")
        assert resp.status_code == 422

    def test_campus_pois_endpoint(self, client, db_session, ar_campus):
        resp = client.get(
            f"/api/v1/ar/campuses/{ar_campus['campus'].id}/pois"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_tour_guide_endpoint(self, client, db_session, ar_campus):
        resp = client.get(f"/api/v1/ar/tours/{ar_campus['tour'].id}/guide")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["steps"]) == 2
        assert body["steps"][1]["distance_from_prev_m"] is not None

    def test_poi_detail(self, client, db_session, ar_campus):
        resp = client.get(f"/api/v1/ar/pois/{ar_campus['lib'].id}")
        assert resp.status_code == 200
        assert resp.json()["category"] == "library"
        assert len(resp.json()["assets"]) == 1

    def test_admin_create_poi_requires_auth(self, client, db_session, ar_campus):
        resp = client.post(
            f"/api/v1/ar/campuses/{ar_campus['campus'].id}/pois",
            json={"name_en": "Lab", "category": "lab"},
        )
        assert resp.status_code == 401
