# ShikkhaHub Makefile
# Common development commands

.PHONY: help install dev test lint format clean docker-build deploy

# Default target
help:
	@echo "ShikkhaHub Development Commands"
	@echo "================================"
	@echo "make install         - Install all dependencies"
	@echo "make dev             - Start development servers"
	@echo "make test            - Run all tests"
	@echo "make lint            - Run linters"
	@echo "make format          - Format code"
	@echo "make clean           - Clean build artifacts"
	@echo "make docker-build    - Build Docker images"
	@echo "make docker-up       - Start Docker containers"
	@echo "make deploy-staging  - Deploy to staging"
	@echo "make deploy-prod     - Deploy to production"

# Installation
install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	npm install

# Development
dev:
	@echo "Starting development environment..."
	@make dev-backend & make dev-frontend

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	npm run dev

# Testing
test:
	@echo "Running backend tests..."
	cd backend && pytest -v
	@echo "Running frontend tests..."
	npm run test

test-backend:
	cd backend && pytest -v --tb=short

test-backend-cov:
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

test-frontend:
	npm run test

# Linting
lint:
	@echo "Linting backend..."
	cd backend && flake8 app tests --max-line-length=100 --extend-ignore=E203,W503
	@echo "Linting frontend..."
	npm run lint

lint-backend:
	cd backend && flake8 app tests --max-line-length=100

lint-frontend:
	npm run lint

type-check:
	@echo "Type checking backend..."
	cd backend && mypy app --ignore-missing-imports
	@echo "Type checking frontend..."
	npm run type-check

# Formatting
format:
	@echo "Formatting backend..."
	cd backend && black app tests --line-length=100
	cd backend && isort app tests --profile black
	@echo "Formatting frontend..."
	npm run format

format-backend:
	cd backend && black app tests --line-length=100
	cd backend && isort app tests --profile black

format-frontend:
	npm run format

# Cleaning
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	rm -rf frontend/node_modules/.cache 2>/dev/null || true

# Database
db-init:
	cd backend && python init_db.py

db-migrate:
	cd backend && alembic revision --autogenerate -m "$(message)"

db-upgrade:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

db-seed:
	cd backend && python import_csv.py scraper/data/sample_institutions.csv

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# Deployment
deploy-staging:
	./scripts/deploy.sh staging

deploy-prod:
	./scripts/deploy.sh production

# CI/CD Simulation
ci-check:
	@make lint
	@make type-check
	@make test-backend

# Utilities
env-setup:
	cp .env.example .env
	@echo "Please edit .env file with your configuration"

requirements-export:
	cd backend && pip freeze > requirements.txt

# Git hooks
git-hooks-install:
	@echo "Installing pre-commit hooks..."
	cd backend && pre-commit install || pip install pre-commit && pre-commit install

# Health checks
health-check:
	curl -s http://localhost:8000/api/v1/health | jq .

health-check-prod:
	curl -s https://api.shikkhahub.com/api/v1/health | jq .
