"""Tests for location endpoints."""
import pytest
from app.models.location import Division, District, Upazila


class TestLocationEndpoints:
    """Test location API endpoints."""
    
    @pytest.fixture
    def sample_locations(self, db_session):
        """Create sample location data."""
        # Create division
        division = Division(
            name_en="Dhaka",
            name_bn="ঢাকা",
            code="DHK"
        )
        db_session.add(division)
        db_session.commit()
        db_session.refresh(division)
        
        # Create district
        district = District(
            name_en="Dhaka",
            name_bn="ঢাকা",
            code="DHK-D",
            division_id=division.id
        )
        db_session.add(district)
        db_session.commit()
        db_session.refresh(district)
        
        # Create upazila
        upazila = Upazila(
            name_en="Dhanmondi",
            name_bn="ধানমন্ডি",
            code="DHK-D-DHM",
            district_id=district.id
        )
        db_session.add(upazila)
        db_session.commit()
        db_session.refresh(upazila)
        
        return {
            "division": division,
            "district": district,
            "upazila": upazila
        }
    
    def test_list_divisions(self, client, sample_locations):
        """Test listing all divisions."""
        response = client.get("/api/v1/locations/divisions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check structure
        if len(data) > 0:
            assert "id" in data[0]
            assert "name_en" in data[0]
            assert "name_bn" in data[0]
            assert "district_count" in data[0]
    
    def test_list_districts_by_division(self, client, sample_locations):
        """Test listing districts within a division."""
        division_id = sample_locations["division"].id
        
        response = client.get(f"/api/v1/locations/divisions/{division_id}/districts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_districts_invalid_division(self, client):
        """Test listing districts for non-existent division."""
        response = client.get("/api/v1/locations/divisions/99999/districts")
        
        assert response.status_code == 404
    
    def test_list_upazilas_by_district(self, client, sample_locations):
        """Test listing upazilas within a district."""
        district_id = sample_locations["district"].id
        
        response = client.get(f"/api/v1/locations/districts/{district_id}/upazilas")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_location_hierarchy(self, client, sample_locations):
        """Test getting complete location hierarchy."""
        response = client.get("/api/v1/locations/hierarchy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "divisions" in data
        assert "total_districts" in data
        assert "total_upazilas" in data
        assert isinstance(data["divisions"], list)
