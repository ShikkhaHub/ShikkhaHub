"""Test to verify test infrastructure is working."""


class TestInfrastructure:
    """Test that the test infrastructure is set up correctly."""
    
    def test_database_connection(self, db_session):
        """Test database connection."""
        result = db_session.execute("SELECT 1").scalar()
        assert result == 1
    
    def test_client_connection(self, client):
        """Test API client connection."""
        response = client.get("/")
        # Root may not exist, but we should get a response
        assert response.status_code in [200, 404]
    
    def test_fixtures_work(self, test_user):
        """Test that fixtures are working."""
        assert test_user.email == "test@example.com"
        assert test_user.username == "testuser"
    
    def test_admin_fixture_works(self, test_admin):
        """Test admin fixture."""
        assert test_admin.email == "admin@example.com"
        assert test_admin.role.value == "admin"


class TestHealthCheck:
    """Test basic API health."""
    
    def test_api_is_responsive(self, client):
        """Test that API is responsive."""
        # Test an endpoint that should exist
        response = client.get("/api/v1/institutions/")
        assert response.status_code in [200, 422]  # 200 if empty, 422 if validation error
    
    def test_docs_endpoint(self, client):
        """Test docs endpoint exists."""
        response = client.get("/docs")
        assert response.status_code == 200
