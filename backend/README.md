# ShikkhaHub Backend

FastAPI-based REST API for the Bangladesh Education Information Platform.

## Quick Start

### Using Docker (Recommended)

```bash
# From project root
docker-compose up -d

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Local Development

```bash
# 1. Setup Python environment
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup PostgreSQL (must be running locally)
# Create database: shikkhahub

# 4. Copy and edit environment config
cp .env.example .env

# 5. Run migrations
alembic upgrade head

# 6. Start server
uvicorn app.main:app --reload
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/     # API route handlers
│   ├── core/                  # Config, database setup
│   ├── models/                # SQLAlchemy models
│   ├── schemas/               # Pydantic schemas
│   └── main.py                # FastAPI app factory
├── alembic/                   # Database migrations
├── requirements.txt
├── Dockerfile
└── README.md
```

## Database Models

### Core Entities
- **Institution** - Schools, colleges, universities, etc.
- **Course** - Academic programs offered
- **Subject** - Individual subjects within courses
- **Location** - Division → District → Upazila hierarchy
- **Affiliation** - Education boards, UGC links

### Data Quality Fields
All entities include:
- `data_source` - Origin of data (scraped, manual, API)
- `verification_status` - verified / pending / flagged
- `last_updated` - Timestamp for freshness

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/institutions/` | List institutions (paginated) |
| `GET /api/v1/institutions/search?q=` | Search institutions |
| `GET /api/v1/institutions/{slug}` | Get institution details |
| `GET /api/v1/locations/divisions` | List divisions |
| `GET /api/v1/locations/hierarchy` | Full location tree |
| `GET /api/v1/search/autocomplete?q=` | Search autocomplete |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `BACKEND_CORS_ORIGINS` | `[]` | Allowed frontend origins |
| `ENVIRONMENT` | `development` | dev/staging/prod |
| `DEBUG` | `true` | Enable debug mode |

## Migrations

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one
alembic downgrade -1
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```
