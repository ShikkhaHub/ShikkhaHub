# Testing Guide

## Running Tests

### Run all tests
```bash
cd backend
pytest
```

### Run specific test file
```bash
pytest tests/test_auth.py
```

### Run specific test class
```bash
pytest tests/test_auth.py::TestAuthEndpoints
```

### Run specific test method
```bash
pytest tests/test_auth.py::TestAuthEndpoints::test_register_success
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run only unit tests
```bash
pytest -m unit
```

### Run only integration tests
```bash
pytest -m integration
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_auth.py          # Authentication tests
├── test_institutions.py  # Institution API tests
├── test_locations.py     # Location API tests
├── test_search.py        # Search API tests
├── test_qa.py            # Q&A and comments tests
└── test_coverage.py      # Infrastructure tests
```

## Test Database

Tests use an in-memory SQLite database that is created fresh for each test session.
Each test runs in a transaction that is rolled back after the test, ensuring test isolation.

## Fixtures

### Common Fixtures
- `client` - FastAPI test client
- `db_session` - Database session
- `test_user` - Regular test user
- `test_admin` - Admin test user
- `auth_headers` - Authorization headers for regular user
- `admin_headers` - Authorization headers for admin

## Writing Tests

### Example Test
```python
def test_example(client, test_user, auth_headers):
    # Test code here
    response = client.get("/api/v1/some-endpoint", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "expected_key" in data
```

### Using Markers
```python
import pytest

@pytest.mark.unit
def test_unit_something():
    pass

@pytest.mark.integration
def test_integration_something():
    pass

@pytest.mark.slow
def test_slow_something():
    pass
```
