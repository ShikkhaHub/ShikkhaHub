"""Tests for the CKAN data catalog integration."""

import pytest

from app.core.ckan import CKANClient
from app.services.ckan import (
    CATEGORY_GROUPS,
    VERIFICATION_TO_CKAN,
    institution_to_dataset,
)
from app.models import (
    Institution,
    InstitutionType,
    Division,
    District,
    Upazila,
)


# ------------------------------------------------------------------ unit
class TestCKANHelpers:
    def test_make_slug(self):
        assert (
            CKANClient.make_slug("Dhaka University of Engineering & Technology")
            == "dhaka-university-of-engineering-technology"
        )
        assert CKANClient.make_slug("ঢাকা") != ""

    def test_checksum(self):
        assert len(CKANClient.checksum(b"hello")) == 64

    def test_verification_mapping(self):
        assert VERIFICATION_TO_CKAN["verified"] == "verified"
        assert VERIFICATION_TO_CKAN["official"] == "published"
        assert VERIFICATION_TO_CKAN["pending"] == "pending_review"


class TestInstitutionToDataset:
    @pytest.fixture
    def institution(self, db_session):
        div = Division(name_en="Dhaka")
        db_session.add(div)
        db_session.flush()
        dist = District(name_en="Dhaka", division_id=div.id)
        db_session.add(dist)
        db_session.flush()
        up = Upazila(name_en="Mirpur", district_id=dist.id)
        db_session.add(up)
        db_session.flush()
        itype = InstitutionType(name="University")
        db_session.add(itype)
        db_session.flush()

        inst = Institution(
            name_en="University of Dhaka",
            slug="university-of-dhaka",
            type_id=itype.id,
            division_id=div.id,
            district_id=dist.id,
            upazila_id=up.id,
            description="Oldest university in Bangladesh",
            website="https://du.ac.bd",
            eiin="123456",
            verification_status="verified",
            data_source="ugc",
            latitude=23.73,
            longitude=90.39,
            is_active=True,
        )
        db_session.add(inst)
        db_session.flush()
        return inst

    def test_basic_payload(self, institution):
        payload = institution_to_dataset(institution)
        assert payload["dataset_category"] == "institutions"
        assert payload["name"] == "institutions-university-of-dhaka"
        assert payload["verification_status"] == "verified"
        assert payload["extras"]["eiin"] == "123456"
        assert payload["extras"]["division"] == "Dhaka"
        assert payload["coverage"] == "Dhaka"

    def test_groups_mapped(self, institution):
        payload = institution_to_dataset(institution)
        group_names = {g["name"] for g in payload["groups"]}
        assert "higher-education" in group_names

    def test_tags_deduped(self, institution):
        payload = institution_to_dataset(institution)
        assert payload["tags"] == list(dict.fromkeys(payload["tags"]))

    def test_categories_have_groups(self):
        for category in ("institutions", "admission", "scholarships", "results"):
            assert category in CATEGORY_GROUPS
            assert CATEGORY_GROUPS[category]


# ------------------------------------------------------------------ api
class TestCatalogEndpoints:
    def test_status_disabled(self, client, test_db):
        resp = client.get("/api/v1/catalog/status")
        assert resp.status_code == 200
        body = resp.json()
        assert body["enabled"] is False

    def test_search_disabled_returns_empty(self, client, test_db):
        resp = client.get("/api/v1/catalog/datasets", params={"q": "dhaka"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["results"] == []

    def test_dcat_bad_format(self, client, test_db):
        resp = client.get("/api/v1/catalog/dcat/badformat")
        assert resp.status_code == 400

    def test_create_dataset_requires_auth(self, client, test_db):
        resp = client.post(
            "/api/v1/catalog/datasets",
            json={
                "title": "Test",
                "dataset_category": "institutions",
                "description": "desc",
            },
        )
        assert resp.status_code == 401
