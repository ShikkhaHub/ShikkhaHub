# Developer Guide

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional)
- Git

### Quick Start

```bash
# Clone repo
git clone https://github.com/shikkhahub/shikkhahub.git
cd shikkhahub

# Option 1: Docker (easiest)
docker-compose up -d

# Option 2: Manual
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API routes
│   ├── core/                # Config, security, caching
│   ├── models/              # Database models
│   └── main.py              # FastAPI app
├── tests/                   # Pytest tests
└── requirements.txt

frontend/
├── src/
│   ├── components/          # React components
│   ├── pages/               # Route pages
│   └── lib/                 # Utilities
└── package.json
```

## Backend Development

### Adding New Endpoints

1. Create file in `app/api/v1/endpoints/`
2. Add router to `app/api/v1/__init__.py`
3. Add tests in `tests/`

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
pytest                    # Run all tests
pytest -v                # Verbose output
pytest --cov=app         # With coverage
```

## Frontend Development

### Adding New Pages

1. Create page in `src/pages/`
2. Add route in `src/App.tsx`
3. Add SEO component for the page

### Components

- Use shadcn/ui components when possible
- Follow existing naming conventions
- Add TypeScript types

## Code Style

- **Python**: PEP 8, Black formatter
- **TypeScript**: ESLint + Prettier
- **Git**: Conventional commits

## Environment Variables

See `.env.example` for all required variables.

## Debugging

### Backend
- API docs: `http://localhost:8000/docs`
- ReDocs: `http://localhost:8000/redoc`

### Frontend
- React DevTools extension
- Vite HMR for fast refresh

## Contributing

1. Fork the repo
2. Create feature branch
3. Make changes with tests
4. Submit PR with description

## Useful Commands

```bash
# Format code
black backend/
npm run format

# Run linting
flake8 backend/
npm run lint

# Type check
mypy backend/
npm run type-check
```
