# Deployment Guide

## Overview

ShikkhaHub supports multiple deployment options:
- Vercel (serverless, recommended for hosting on Vercel)
- Docker Compose (recommended for self-hosting)
- Kubernetes (future)
- Manual deployment

## Prerequisites

- Linux server (Ubuntu 22.04 LTS recommended)
- Docker & Docker Compose
- Domain name with SSL certificate
- 4GB+ RAM, 2+ CPU cores

## Vercel Deployment

ShikkhaHub is a monorepo with two Vercel projects (one for `frontend/`, one for `backend/`).

### Architecture

- **Frontend** (`frontend/`) — Vite + React static site. Vercel detects the Vite
  framework preset. Client-side routes are rewritten to `index.html` via
  `frontend/vercel.json`.
- **Backend** (`backend/`) — FastAPI served as a single Vercel Function. Vercel
  auto-detects the FastAPI app at `backend/app/main.py` (zero-config). The whole
  app runs on **Python 3.12** (pinned in `backend/vercel.json`) and matches the
  full request path itself, so routes like `/api/v1/institutions` work as-is.

### 1. Create the projects (one-time)

```bash
# Frontend project (root directory: frontend)
vercel link --yes --project shikkhahub-frontend
cd frontend && vercel link && cd ..

# Backend project (root directory: backend)
cd backend && vercel link && cd ..
```

Set `Root Directory` to `frontend` / `backend` respectively in each project's
Settings if the link did not pick it up automatically.

### 2. Configure environment variables

Backend project (Production):
```env
DATABASE_URL=postgresql://user:password@host:5432/shikkhahub   # Managed Postgres (e.g. Vercel Postgres / Neon / Supabase)
BACKEND_CORS_ORIGINS=["https://<frontend>.vercel.app"]
SECRET_KEY=<random-32-char-string>
ENVIRONMENT=production
DEBUG=false
```

Frontend project (Production):
```env
VITE_API_URL=https://<backend>.vercel.app/api/v1
```

> **Database note:** Vercel's filesystem is ephemeral and read-only, so SQLite
> (`DATABASE_URL=sqlite:///...`) will **not** persist. A managed PostgreSQL
> database is required. Tables are created automatically on cold start via
> `init_db()`.

### 3. Deploy

```bash
# Frontend
cd frontend && vercel --prod

# Backend
cd backend && vercel --prod
```

### CI/CD

Pushes to `main` auto-deploy both projects via
`.github/workflows/vercel-deploy.yml`. Configure these GitHub secrets:

| Secret | Value |
| --- | --- |
| `VERCEL_TOKEN` | Vercel access token |
| `VERCEL_ORG_ID` | Team ID (found in `.vercel/project.json` → `orgId`) |
| `VERCEL_PROJECT_ID_FRONTEND` | Frontend project ID |
| `VERCEL_PROJECT_ID_BACKEND` | Backend project ID |

### Serverless constraints handled by the code

- The background scheduler and automated backups are **disabled** on Vercel
  (checked via the `VERCEL` env var in `backend/app/main.py`).
- Redis and Elasticsearch are optional: if unreachable they degrade gracefully
  (in-memory rate limiting, DB-backed search fallback).
- Rate limiting uses forwarded headers (`x-forwarded-for` / `x-real-ip`) to work
  behind Vercel's proxy (`backend/app/core/rate_limit.py`).
- Prefer cold starts: the app keeps dependencies lean and defers heavy work.

## Quick Deploy

```bash
# 1. Setup server
./scripts/setup-server.sh

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Deploy
./scripts/deploy.sh staging    # or production
```

## Manual Deployment

### 1. Server Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. SSL Certificate

```bash
# Using Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ~/shikkhahub/nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ~/shikkhahub/nginx/ssl/key.pem
```

### 3. Environment Configuration

Create `.env` file:

```env
POSTGRES_USER=shikkhahub
POSTGRES_PASSWORD=secure_random_password
POSTGRES_DB=shikkhahub
DATABASE_URL=postgresql://user:pass@postgres:5432/shikkhahub

REDIS_URL=redis://redis:6379/0
ELASTICSEARCH_URL=http://elasticsearch:9200
ELASTICSEARCH_PASSWORD=elastic_password

SECRET_KEY=random_32_char_string
OPENAI_API_KEY=sk-...

ENVIRONMENT=production
DEBUG=false
```

### 4. Deploy

```bash
cd ~/shikkhahub

# Pull images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Import data (optional)
docker-compose exec backend python import_csv.py /data/institutions.csv
```

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost/api/v1/health

# Check services
docker-compose ps
```

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
```

## Backup & Restore

### Database Backup

```bash
# Manual backup
docker-compose exec postgres pg_dump -U postgres shikkhahub > backup_$(date +%Y%m%d).sql

# Automated (add to crontab)
0 2 * * * cd ~/shikkhahub && docker-compose exec -T postgres pg_dump -U postgres shikkhahub > backups/backup_$(date +\%Y\%m\%d).sql
```

### Restore

```bash
./scripts/rollback.sh production backup_file.sql
```

## CI/CD

Deployments are automated via GitHub Actions:
- Push to `develop` → Deploy to staging
- Push to `main` → Deploy to production

Configure secrets in GitHub:
- `SSH_PRIVATE_KEY`
- `STAGING_SSH_HOST`
- `PROD_SSH_HOST`
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :80
   sudo systemctl stop nginx  # if running locally
   ```

2. **Database connection failed**
   ```bash
   docker-compose logs postgres
   # Check credentials in .env
   ```

3. **Elasticsearch won't start**
   ```bash
   # Increase memory
   docker-compose exec elasticsearch sysctl -w vm.max_map_count=262144
   ```

## Security Checklist

- [ ] SSL certificate installed
- [ ] Strong database password
- [ ] JWT secret key changed
- [ ] API keys secured
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] Automatic security updates enabled
- [ ] Backups configured
- [ ] Monitoring alerts set up

## Support

For deployment issues:
1. Check logs: `docker-compose logs`
2. Review [Troubleshooting](#troubleshooting)
3. Open GitHub issue with logs
