"""Tests for search endpoints."""
import pytest
from app.models.institution import Institution, InstitutionType
from app.models.location import Division, District, Upazila


class TestSearchEndpoints:
    """Test search API endpoints."""
    
    @pytest.fixture
    def search_data(self, db_session):
        """Create sample data for search tests."""
        # Create institution type
        inst_type = InstitutionType(
            name="University",
            category="Higher Education",
            display_order=1
        )
        db_session.add(inst_type)
        db_session.commit()
        db_session.refresh(inst_type)
        
        # Create locations
        division = Division(name_en="Dhaka", name_bn="ঢাকা", code="DHK")
        db_session.add(division)
        db_session.commit()
        db_session.refresh(division)
        
        district = District(name_en="Dhaka", name_bn="ঢাকা", code="DHK-D", division_id=division.id)
        db_session.add(district)
        db_session.commit()
        db_session.refresh(district)
        
        upazila = Upazila(name_en="Dhanmondi", name_bn="ধানমন্ডি", code="DHK-D-DHM", district_id=district.id)
        db_session.add(upazila)
        db_session.commit()
        db_session.refresh(upazila)
        
        # Create institutions
        inst1 = Institution(
            name_en="Dhaka University",
            slug="dhaka-university",
            type_id=inst_type.id,
            upazila_id=upazila.id,
            address="Dhaka",
            verification_status="verified",
            is_active=True
        )
        inst2 = Institution(
            name_en="BUET",
            slug="buet",
            type_id=inst_type.id,
            upazila_id=upazila.id,
            address="Dhaka",
            verification_status="verified",
            is_active=True
        )
        inst3 = Institution(
            name_en="Private University",
            slug="private-university",
            type_id=inst_type.id,
            upazila_id=upazila.id,
            address="Chittagong",
            verification_status="pending",
            is_active=True
        )
        
        db_session.add_all([inst1, inst2, inst3])
        db_session.commit()
        
        return {
            "type": inst_type,
            "division": division,
            "district": district,
            "upazila": upazila,
            "institutions": [inst1, inst2, inst3]
        }
    
    def test_advanced_search_no_query(self, client, search_data):
        """Test advanced search without query."""
        response = client.get("/api/v1/search/advanced")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_advanced_search_with_query(self, client, search_data):
        """Test advanced search with query."""
        response = client.get("/api/v1/search/advanced?q=Dhaka")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # May return results from database or elasticsearch
    
    def test_advanced_search_with_filters(self, client, search_data):
        """Test advanced search with filters."""
        type_id = search_data["type"].id
        
        response = client.get(f"/api/v1/search/advanced?q=University&type_id={type_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_autocomplete(self, client, search_data):
        """Test autocomplete endpoint."""
        response = client.get("/api/v1/search/autocomplete?q=Uni")
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "suggestions" in data
    
    def test_autocomplete_min_length(self, client):
        """Test autocomplete with query too short."""
        response = client.get("/api/v1/search/autocomplete?q=U")
        
        # Should fail validation (min_length=2)
        assert response.status_code == 422
    
    def test_popular_searches(self, client, search_data):
        """Test popular searches endpoint."""
        # First create some search activity
        client.get("/api/v1/search/advanced?q=Dhaka")
        client.get("/api/v1/search/advanced?q=University")
        client.get("/api/v1/search/advanced?q=College")
        
        response = client.get("/api/v1/search/popular-queries")
        
        assert response.status_code == 200
        data = response.json()
        assert "popular_searches" in data


class TestSearchFilters:
    """Test search filtering functionality."""
    
    def test_filter_by_verification_status(self, client, search_data):
        """Test filtering by verification status."""
        response = client.get("/api/v1/search/advanced?verification_status=verified")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        
        # All results should be verified
        for item in data["items"]:
            assert item.get("verification_status") == "verified"
    
    def test_filter_by_featured(self, client, search_data):
        """Test filtering by featured status."""
        response = client.get("/api/v1/search/advanced?is_featured=true")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_combined_filters(self, client, search_data):
        """Test multiple filters combined."""
        type_id = search_data["type"].id
        
        response = client.get(
            f"/api/v1/search/advanced?q=Uni&type_id={type_id}&verification_status=verified"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "query" in data
