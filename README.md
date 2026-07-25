# 🇧🇩 ShikkhaHub - Bangladesh Education Directory

> The most comprehensive education platform in Bangladesh. Find schools, colleges, universities, madrasas, and technical institutes with detailed information, reviews, and AI-powered guidance.

[![CI/CD](https://github.com/shikkhahub/shikkhahub/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/shikkhahub/shikkhahub/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB.svg)](https://reactjs.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🚀 Features

### Core Platform
- 🔍 **Advanced Search** - Full-text search with Elasticsearch, autocomplete, fuzzy matching
- 🏫 **Institution Profiles** - Detailed information on 220+ institutions (universities, colleges, schools, madrasas, technical institutes)
- 🗺️ **Location-Based Discovery** - Browse by division, district, upazila
- 📊 **Comparison Tool** - Compare up to 3 institutions side-by-side
- 👁️ **Recently Viewed** - Track and revisit previously viewed institutions

### AI & Community
- 🤖 **AI Education Assistant** - RAG-powered chatbot for education guidance
- ⭐ **Reviews & Ratings** - User reviews with multi-dimensional ratings
- ❓ **Q&A Platform** - Community questions and answers
- 💬 **Comments** - Threaded discussions on institutions and content

### Admin & Management
- 📊 **Admin Dashboard** - Real-time statistics, charts, and management tools
- ✅ **Verification System** - Institution verification workflow
- 🛡️ **Content Moderation** - Review approval, reporting, and user management
- 🔐 **Role-Based Access** - User roles (user, moderator, admin, super_admin)

### Technical Excellence
- ⚡ **Fast Performance** - Redis caching, CDN-ready, <2s load times
- 🔒 **Security** - JWT authentication, rate limiting, security headers
- 📱 **Mobile-First** - Responsive design optimized for all devices
- 🌐 **SEO Optimized** - Dynamic meta tags, schema markup, sitemap.xml
- 📈 **Analytics** - Google Analytics integration with custom events

## 🏗️ Architecture

```
ShikkhaHub/
├── frontend/               # React + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── pages/          # Route pages
│   │   ├── lib/            # Utilities, API client
│   │   └── App.tsx         # Main app component
│   └── package.json
│
├── backend/                # FastAPI + SQLAlchemy
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Config, security, caching
│   │   ├── models/         # Database models
│   │   └── main.py         # FastAPI app
│   ├── tests/              # Pytest test suite
│   ├── scraper/            # Data scraping tools
│   └── requirements.txt
│
├── docker-compose.yml      # Development environment
├── docker-compose.prod.yml # Production environment
└── .github/workflows/      # CI/CD pipelines
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.111.0
- **Database**: PostgreSQL 15 (production) / SQLite (development)
- **ORM**: SQLAlchemy 2.0+
- **Cache**: Redis 7
- **Search**: Elasticsearch 8.14
- **AI**: OpenAI GPT-3.5 with RAG
- **Authentication**: JWT with refresh tokens
- **Testing**: Pytest with 50+ tests

### Frontend
- **Framework**: React 18.2 + TypeScript
- **Styling**: Tailwind CSS 3.4
- **Routing**: React Router 6
- **Build Tool**: Vite 5.2
- **UI Components**: shadcn/ui
- **Icons**: Lucide React

### DevOps
- **Containerization**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Web Server**: Nginx with SSL
- **Monitoring**: Health checks, Sentry-ready

## 📦 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/shikkhahub/shikkhahub.git
cd shikkhahub

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Option 2: Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python init_db.py

# Import sample data
python import_csv.py scraper/data/sample_institutions.csv

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:5173
```

## 📚 Documentation

- [API Documentation](docs/API.md) - Complete API reference
- [Architecture](docs/ARCHITECTURE.md) - System design and architecture
- [Developer Guide](docs/DEVELOPER.md) - Development guidelines
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [Testing Guide](backend/tests/README.md) - Testing instructions
- [Contributing](CONTRIBUTING.md) - Contribution guidelines

## 🛠️ Development Commands

Use the Makefile for common tasks:

```bash
# Install all dependencies
make install

# Start development servers
make dev

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Database operations
make db-upgrade
make db-seed

# Docker commands
make docker-up
make docker-down

# Deployment
make deploy-staging
make deploy-prod
```

See `Makefile` for all available commands.

## 🧪 Testing

```bash
# Run all tests
make test

# Backend only
make test-backend

# With coverage
make test-backend-cov

# Frontend tests
make test-frontend

# Run specific test file
cd backend && pytest tests/test_auth.py -v
```

## 🚀 Deployment

### Staging

```bash
# Deploy to staging
./scripts/deploy.sh staging
```

### Production

```bash
# Deploy to production
./scripts/deploy.sh production

# Or use CI/CD (automatic on push to main branch)
```

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## 📊 Project Status

### ✅ Completed Features
- [x] Institution search with Elasticsearch
- [x] Admin dashboard with real-time stats
- [x] AI assistant with RAG
- [x] Reviews, Q&A, comments system
- [x] Security & authentication (JWT)
- [x] CI/CD pipeline
- [x] SEO optimization
- [x] 50+ automated tests

### 🚧 In Progress
- [ ] Live data scrapers (SSL/404 issues on govt sites)
- [ ] Mobile app (React Native)

### 📅 Next Up
- [ ] Enhanced monitoring & alerting
- [ ] Data quality validation
- [ ] Backup automation

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- Ministry of Education, Bangladesh
- UGC Bangladesh
- All education boards for publicly available data
- Open source community

## 📞 Contact

- **Website**: [shikkhahub.com](https://shikkhahub.com)
- **Email**: contact@shikkhahub.com
- **Twitter**: [@ShikkhaHub](https://twitter.com/ShikkhaHub)
- **GitHub Issues**: [Report bugs](https://github.com/shikkhahub/shikkhahub/issues)

---

Made with ❤️ for Bangladesh education

🇧🇩 শিক্ষাহাব - বাংলাদেশের শিক্ষার সবচেয়ে বড় ডিরেক্টরি
