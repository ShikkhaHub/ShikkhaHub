"""Tests for institution endpoints."""
import pytest
from app.models.institution import Institution, InstitutionType


class TestInstitutionEndpoints:
    """Test institution API endpoints."""
    
    @pytest.fixture
    def sample_institution(self, db_session):
        """Create a sample institution."""
        # First create institution type
        inst_type = InstitutionType(
            name="University",
            category="Higher Education",
            display_order=1
        )
        db_session.add(inst_type)
        db_session.commit()
        db_session.refresh(inst_type)
        
        # Create institution
        institution = Institution(
            name_en="Test University",
            name_bn="টেস্ট বিশ্ববিদ্যালয়",
            short_name="TU",
            slug="test-university",
            type_id=inst_type.id,
            established_year=1990,
            address="123 Test Street, Dhaka",
            phone="+8801234567890",
            email="info@testuniversity.edu.bd",
            website="https://testuniversity.edu.bd",
            verification_status="verified",
            is_active=True,
            is_featured=False
        )
        db_session.add(institution)
        db_session.commit()
        db_session.refresh(institution)
        return institution
    
    def test_list_institutions(self, client, sample_institution):
        """Test listing institutions."""
        response = client.get("/api/v1/institutions/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1
    
    def test_get_institution_by_slug(self, client, sample_institution):
        """Test getting institution by slug."""
        response = client.get(f"/api/v1/institutions/{sample_institution.slug}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name_en"] == "Test University"
        assert data["slug"] == "test-university"
    
    def test_get_nonexistent_institution(self, client):
        """Test getting non-existent institution."""
        response = client.get("/api/v1/institutions/nonexistent-slug")
        
        assert response.status_code == 404
    
    def test_filter_by_type(self, client, sample_institution):
        """Test filtering institutions by type."""
        response = client.get("/api/v1/institutions/?type_id=1")
        
        assert response.status_code == 200
        data = response.json()
        # Should filter correctly
        assert "items" in data
    
    def test_search_institutions(self, client, sample_institution):
        """Test searching institutions."""
        response = client.get("/api/v1/search/advanced?q=Test")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # May return results from database or elasticsearch


class TestInstitutionAdmin:
    """Test admin institution management."""
    
    @pytest.fixture
    def pending_institution(self, db_session):
        """Create a pending institution."""
        inst_type = InstitutionType(
            name="College",
            category="Higher Secondary",
            display_order=2
        )
        db_session.add(inst_type)
        db_session.commit()
        db_session.refresh(inst_type)
        
        institution = Institution(
            name_en="Pending College",
            slug="pending-college",
            type_id=inst_type.id,
            verification_status="pending",
            is_active=True
        )
        db_session.add(institution)
        db_session.commit()
        db_session.refresh(institution)
        return institution
    
    def test_list_pending_institutions(self, client, admin_headers, pending_institution):
        """Test admin listing pending institutions."""
        response = client.get(
            "/api/v1/admin/institutions/pending",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should include pending institution
    
    def test_verify_institution(self, client, admin_headers, pending_institution):
        """Test verifying an institution."""
        response = client.post(
            f"/api/v1/admin/institutions/{pending_institution.id}/verify",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "verified" in response.json()["message"]
    
    def test_flag_institution(self, client, admin_headers, pending_institution):
        """Test flagging an institution."""
        response = client.post(
            f"/api/v1/admin/institutions/{pending_institution.id}/flag?reason=suspicious",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        assert "flagged" in response.json()["message"]


class TestInstitutionReviews:
    """Test institution review system."""
    
    def test_create_review(self, client, auth_headers, sample_institution):
        """Test creating a review."""
        response = client.post(
            "/api/v1/reviews/reviews",
            headers=auth_headers,
            json={
                "institution_id": sample_institution.id,
                "overall_rating": 4.5,
                "academics_rating": 4.0,
                "facilities_rating": 5.0,
                "title": "Great University",
                "content": "This is a detailed review about the university. It has excellent facilities.",
                "pros": ["Good facilities", "Nice campus"],
                "cons": ["Expensive"],
                "study_program": "Computer Science",
                "graduation_year": 2023,
                "is_alumni": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["overall_rating"] == 4.5
        assert data["institution_id"] == sample_institution.id
    
    def test_list_institution_reviews(self, client, sample_institution):
        """Test listing reviews for an institution."""
        response = client.get(
            f"/api/v1/reviews/institutions/{sample_institution.id}/reviews"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "average_rating" in data
