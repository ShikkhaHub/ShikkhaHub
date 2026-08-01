# 🇧🇩 ShikkhaHub — FULL DEVELOPMENT TODO (Execution Blueprint)

> Build order: **Data → Backend → Search → Frontend → AI → Trust → Scale**
> Budget: ৳10,000,000 | Deadline: 6 months | Scope: National-scale

---

## 🧱 1. SYSTEM FOUNDATION (Week 1–2)

### ✅ Project Setup
* [ ] Create monorepo (apps + services + packages)
* [ ] Setup Git (branching: dev / staging / prod)
* [ ] Setup CI/CD pipeline (GitHub Actions)

### ✅ Tech Stack Initialization
* [ ] Setup **Next.js frontend (App Router)**
* [ ] Setup **Backend (FastAPI)**
* [ ] Setup **PostgreSQL database** (SQLite for dev)
* [ ] Setup **Redis (caching layer)**
* [ ] Setup **ElasticSearch (search engine)**

### ✅ Infrastructure
* [ ] Setup cloud (AWS / GCP / DigitalOcean)
* [ ] Setup Docker
* [ ] Setup environment configs (dev/staging/prod)

---

## 🗄️ 2. DATA LAYER (CRITICAL — Week 1–6)

> Without this → platform fails

### ✅ Database Design
* [ ] Institutions table
* [ ] Courses table
* [ ] Subjects table
* [ ] Locations (division → district → upazila)
* [ ] Admission requirements
* [ ] Contacts
* [ ] Affiliations (map to authorities like UGC, Education Boards)

### ✅ Data Pipeline
* [ ] Build scraper service
* [ ] Build manual data entry panel
* [ ] Normalize inconsistent data
* [ ] Deduplicate institutions

### ✅ Data Sources Integration
* [ ] Govt sites scraping (UGC, Education Boards)
* [ ] CSV/manual upload support
* [ ] University websites scraping (live sites need fixing)

### ✅ Data Quality System
* [ ] Add "data source" field
* [ ] Add "last updated" timestamp
* [ ] Add verification status (verified / pending / flagged)
* [ ] Data validation rules (required fields, format checks)
* [ ] Automated data quality scoring
* [ ] Duplicate detection algorithm
* [ ] Data freshness alerts (stale data warning)

### ✅ Data Backup & Recovery
* [ ] Automated database backups (daily at 2 AM via cron)
* [ ] Backup verification testing (checksum + integrity checks)
* [ ] Point-in-time recovery capability (restore with force confirmation)
* [ ] Backup retention policies (30 day default)
* [ ] Background task scheduler for automated maintenance

---

## 🔎 3. SEARCH & DISCOVERY ENGINE (Week 3–8)

### ✅ Core Search
* [ ] Full-text search (ElasticSearch)
* [ ] Autocomplete
* [ ] Fuzzy search (typo tolerance with SequenceMatcher)
* [ ] "Did you mean?" spell correction
* [ ] Personalized search results

### ✅ Filters
* [ ] Location-based (division/district)
* [ ] Institution type (college/university/polytechnic)
* [ ] Subject/course filter

### ✅ Ranking Logic
* [ ] Verified institutions first
* [ ] Popularity-based ranking (view count, search frequency)
* [ ] Location proximity boost
* [ ] Review rating boost
* [ ] Featured/promoted institutions
* [ ] Personalization (user preferences - keyword matching, recently viewed)

### ✅ Search Enhancements
* [ ] Search analytics (track queries, no-results - Analytics implemented)
* [ ] Did you mean? (spell correction - FuzzyMatcher)
* [ ] Search filters persistence
* [ ] Saved searches
* [ ] Search history

### ✅ API Endpoints
* [ ] `/search?q=`
* [ ] `/institutions`
* [ ] `/institutions/{slug}`
* [ ] `/locations/divisions`

---

## 🏫 4. INSTITUTION MODULE (Week 4–9)

### ✅ Institution Listing Page
* [ ] Card UI (name, location, type)
* [ ] Quick filters (type, division, status)
* [ ] Pagination

### ✅ Institution Details Page (MOST IMPORTANT PAGE)
* [ ] Overview section
* [ ] Courses & subjects (placeholder)
* [ ] Admission requirements (placeholder)
* [ ] Contact info
* [ ] Location map (placeholder)
* [ ] Affiliation info

### ✅ Comparison Feature
* [ ] Compare 2–3 institutions
* [ ] Highlight differences
* [ ] LocalStorage persistence
* [ ] Compare button on cards and detail page
* [ ] Side-by-side comparison table

---

## 🎨 5. FRONTEND UX (Week 5–10)

### ✅ Core Pages
* [ ] Homepage (search-first UI)
* [ ] Search results page
* [ ] Institution details page
* [ ] Dashboard

### ✅ UX Must-Haves
* [ ] Mobile-first design - Responsive layout with mobile navigation
* [ ] Fast load (<2 sec) - Redis caching + Elasticsearch
* [ ] Clean typography
* [ ] Skeleton loading states

### ✅ Smart UX Features
* [ ] "Popular searches" - Track and display trending searches
* [ ] "Suggested institutions" - Based on user profile/interests
* [ ] "Recently viewed" - Implemented with localStorage, shows last 10 institutions
* [ ] "You might also like" - Similar institutions recommendation
* [ ] Personalized dashboard - Based on user preferences

### ✅ UI Polish
* [ ] Dark mode toggle (ThemeProvider with CSS variables)
* [ ] Toast notifications for user actions (ToastProvider with animations)
* [ ] Keyboard shortcuts (power users - Ctrl+K, ?, etc.)
* [ ] Error boundaries (graceful error handling)
* [ ] Loading states for all interactions
* [ ] Empty states illustration
* [ ] Confirmation dialogs for destructive actions

---

## 🤖 6. AI DECISION SYSTEM (Week 8–12)

> This is your differentiation layer

### ✅ RAG System
* [ ] Build vector database (TF-IDF with scikit-learn - in-memory)
* [ ] Index institution + course data (SimpleVectorStore with documents)
* [ ] Connect LLM API (OpenAI GPT-3.5 with fallback to rule-based)
* [ ] Context retrieval for RAG (Elasticsearch + vector similarity)

### ✅ AI Features
* [ ] "What should I study?" assistant (EducationAssistant with system prompt)
* [ ] Institution recommendation (RAG-based search + context)
* [ ] Admission difficulty estimation
* [ ] Career suggestions (keyword-based guidance)
* [ ] Chat API endpoints (/ai/chat, /ai/chat/sessions)
* [ ] Conversation history persistence
* [ ] Source citations for transparency

### ✅ Prompt Engineering
* [ ] Prevent hallucination (system prompt with strict guidelines)
* [ ] Force data-grounded answers (RAG context injection)
* [ ] Add citation system (sources returned with each response)

---

## 🛡️ 7. TRUST & VERIFICATION SYSTEM (Week 6–12)

> THIS determines success

### ✅ Verification System
* [ ] Verified badge (field exists)
* [ ] Admin approval workflow
* [ ] Source tracking

### ✅ Admin Panel
* [ ] Admin Dashboard UI (shadcn/ui components, responsive layout)
* [ ] Stats cards with growth indicators
* [ ] Charts (Applications Overview line chart, Status donut chart)
* [ ] Top Institutions table
* [ ] Division statistics progress bars
* [ ] Recent Notifications panel
* [ ] System Overview panel
* [ ] Admin sidebar navigation (all management sections)
* [ ] Admin header with search, notifications, profile dropdown
* [ ] Add/edit institution (API ready)
* [ ] Approve/reject updates workflow
* [ ] Flag incorrect data
* [ ] Institution verification endpoints (/admin/institutions/pending, verify, reject, flag)
* [ ] Content moderation endpoints (/admin/moderation/reviews, reports)
* [ ] Dashboard stats API (/admin/dashboard/stats, top-institutions, recent-activity)
* [ ] User management endpoints (/admin/users, roles, activate/deactivate)

### ✅ Audit System
* [ ] Change history
* [ ] Data logs
* [ ] Moderator roles

---

## 👥 8. COMMUNITY LAYER (Week 10–16)

### ✅ Features
* [ ] Q&A system (questions, answers, votes, best answer)
* [ ] Comments (threaded replies, likes)
* [ ] Reviews (institution-based, ratings, helpful votes)

### ✅ Moderation
* [ ] Report system (review reporting, flagging)
* [ ] Content approval workflow (pending/approved/rejected status)
* [ ] Vote-based quality ranking
* [ ] Content approval

---

## 📢 9. DISTRIBUTION SYSTEM (Parallel — Month 2–6)

### ✅ SEO
* [ ] Dynamic pages for each institution (SEO component with dynamic meta tags)
* [ ] Schema markup (JSON-LD for EducationalOrganization)
* [ ] Fast indexing (sitemap.xml with all institutions)

### ✅ Growth Channels
* [ ] Facebook student groups (social sharing via meta tags)
* [ ] YouTube content
* [ ] Campus ambassadors

### ✅ Viral Loops
* [ ] Share institution page (Open Graph meta tags for sharing)
* [ ] "Compare with friends" (comparison feature ready for viral sharing)

---

## 📱 10. MOBILE APP (Month 5–6)

### ✅ Build
* [ ] React Native app
* [ ] Same API as web

### ✅ Features
* [ ] Search
* [ ] Institution view
* [ ] AI assistant

---

## 🔐 SECURITY & COMPLIANCE (Week 3–8)

> Security is not optional for an education platform

### ✅ API Security
* [ ] Rate limiting (slowapi with Redis/in-memory storage)
* [ ] JWT authentication system (access + refresh tokens)
* [ ] Protected route dependencies (get_current_user, get_current_admin)
* [ ] API key authentication for external access
* [ ] Request size limits (10MB max)
* [ ] CORS policy enforcement
* [ ] SQL injection prevention (SQLAlchemy safe)
* [ ] XSS protection headers (X-Content-Type-Options, X-Frame-Options, CSP)

### ✅ Data Protection
* [ ] Password hashing (bcrypt)
* [ ] JWT token security (HS256 algorithm, proper expiration)
* [ ] Secure session management (token-based)
* [ ] Input sanitization (prevent XSS)
* [ ] Data encryption at rest (sensitive fields)

### ✅ Privacy Compliance
* [ ] GDPR/Bangladesh DPA compliance
* [ ] User consent management
* [ ] Data retention policies
* [ ] Right to deletion (user data export/delete)
* [ ] Privacy policy page

---

## ⚙️ 11. PERFORMANCE & SCALING

### ✅ Performance
* [ ] Redis caching
* [ ] Performance monitoring middleware
* [ ] Application metrics collection
* [ ] CDN (Cloudflare)
* [ ] Lazy loading

### ✅ Scaling
* [ ] Horizontal scaling backend
* [ ] DB indexing optimization
* [ ] Queue system (background jobs)

---

## 📚 11.5 API DOCUMENTATION & DEVELOPER EXPERIENCE

### ✅ API Docs
* [ ] OpenAPI/Swagger documentation (auto-generated at /docs)
* [ ] API reference documentation (docs/API.md)
* [ ] API versioning strategy (v1 implemented)
* [ ] Postman collection (via OpenAPI spec)

### ✅ Developer Tools
* [ ] API playground/sandbox (/docs interactive UI)
* [ ] Developer guide (docs/DEVELOPER.md)
* [ ] Testing guide (backend/tests/README.md)

---

## 🧪 12. QA & TESTING

### ✅ Testing
* [ ] Unit tests (API) - pytest with test database
* [ ] Integration tests - Database model tests
* [ ] Test fixtures - User, admin, institutions, locations
* [ ] Test coverage reporting - pytest-cov
* [ ] Auth endpoint tests
* [ ] Institution endpoint tests
* [ ] Location endpoint tests
* [ ] Search endpoint tests
* [ ] Q&A and comments endpoint tests

### ✅ Real-world Testing
* [ ] Students test (critical) - TODO: Deploy for student feedback
* [ ] Collect feedback
* [ ] Iterate weekly

---

## 📊 13. ANALYTICS

### ✅ Track
* [ ] Search queries (SearchEvent model with click-through tracking)
* [ ] Click behavior (ClickEvent model for buttons and interactions)
* [ ] Page views (PageView model with device detection)
* [ ] Engagement metrics (time on page, scroll depth)
* [ ] Drop-offs (requires session tracking enhancement)

### ✅ Tools
* [ ] Google Analytics
* [ ] Custom dashboard (Admin API endpoints with daily/hourly metrics)
* [ ] Popular searches tracking
* [ ] Trending searches analysis
* [ ] Content gap analysis (no-result searches)

---

## 🚀 13.5 DEPLOYMENT & DEVOPS

### ✅ Deployment Pipeline
* [ ] Staging environment setup (docker-compose with .env.staging)
* [ ] Production deployment automation (deploy.sh with rolling updates)
* [ ] Blue-green deployment strategy (Docker Compose with scale)
* [ ] Database migration system (Alembic in deploy scripts)
* [ ] Rollback procedures (rollback.sh with database restore)

### ✅ Vercel Serverless Deployment
* [ ] `frontend/vercel.json` — Vite SPA framework, `pnpm build`, output `dist`, SPA catch-all rewrite
* [ ] `backend/vercel.json` — FastAPI single Function, pinned `python3.12` (psycopg2 has no 3.13 wheel), `maxDuration 60`, `excludeFiles`
* [ ] `frontend/.env.example` — documents `VITE_API_URL`
* [ ] Backend made serverless-safe (proxy-aware rate limiting, scheduler disabled via `VERCEL=1`)
* [ ] CI/CD workflow `.github/workflows/vercel-deploy.yml` (deploy-frontend + deploy-backend jobs)
* [ ] Deployment docs (docs/DEPLOYMENT.md Vercel section, README deploy section)
* [ ] Push commit and set Vercel secrets (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID_*)

### ✅ Infrastructure as Code
* [ ] Terraform/CloudFormation templates
* [ ] Docker Compose for local dev
* [ ] Docker Compose for production (docker-compose.prod.yml)
* [ ] Kubernetes manifests (future scaling)
* [ ] Environment variable management (.env.example, .env.staging, .env.production)

### ✅ Monitoring & Alerts
* [ ] Application performance monitoring (APM)
* [ ] Error tracking (Sentry integration config in env)
* [ ] Uptime monitoring (health check endpoint)
* [ ] Alert channels (Slack webhook in CI/CD)
* [ ] Server setup script (setup-server.sh with logrotate)

---

## 🚨 14. RISK CONTROL CHECKLIST

### MUST monitor weekly:
* [ ] Data accuracy %
* [ ] Search speed
* [ ] API errors
* [ ] User retention
* [ ] Bounce rate

---

## 🔥 FINAL EXECUTION PRIORITY (DO NOT BREAK THIS ORDER)

1. Data system ✅ (In Progress)
2. Search ✅ (API Ready)
3. Institution pages
4. Trust system
5. AI
6. Community
7. Mobile app

---

## 🧠 REALITY CHECK (IMPORTANT)

If you only get ONE thing right:

> ✅ **Make the most accurate, complete education database in Bangladesh**

Everything else (AI, UI, growth) becomes easy after that.

---

## 📋 CURRENT STATUS (Updated: 2026-08-01)

**Vercel Deployment Support Complete** - Monorepo migrated for serverless deployment as two separate Vercel projects (frontend + backend):
- [ ] `frontend/vercel.json` (Vite SPA framework, SPA rewrites to index.html)
- [ ] `backend/vercel.json` (Python 3.12 runtime, 60s maxDuration, excludeFiles)
- [ ] API base URL env-driven (`VITE_API_URL` with `/api/v1` fallback)
- [ ] Proxy-aware rate limiter (x-forwarded-for / x-real-ip)
- [ ] Scheduler disabled on Vercel (serverless-safe startup)
- [ ] CI/CD workflow `.github/workflows/vercel-deploy.yml` (frontend + backend jobs)
- [ ] Backend smoke-tested: all endpoints green (health, institutions, locations, search w/ ES fallback)
- [ ] Frontend `pnpm build` passing (298 kB JS / 83.6 kB gzip)
- [ ] Deployment docs in `docs/DEPLOYMENT.md` + README
- ⚠️ **BLOCKED**: Commit `51de5ec` ready locally, push pending — no GitHub credentials in sandbox. Run `git push origin v0/mdselim606570-9293-d1524972` from a machine with auth, then link secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID_FRONTEND`, `VERCEL_PROJECT_ID_BACKEND`.

---

## 📋 PREVIOUS STATUS (2026-05-01)

**Frontend Infrastructure ALL Phases Complete** - Full frontend foundation: types, API, hooks, stores, UI components, SearchBar, InstitutionCard, InstitutionDetail. Ready for integration with existing pages.

### ✅ COMPLETED
- [ ] FastAPI backend with SQLAlchemy models
- [ ] PostgreSQL schema (using SQLite for dev)
- [ ] Scraper framework with base classes
- [ ] CSV importer for bulk data upload
- [ ] 220+ institutions imported (universities, 50+ medical/dental colleges, colleges, schools, polytechnics, madrasas, technical institutes)
- [ ] Search API endpoints
- [ ] Frontend API client
- [ ] HeroSection with live search
- [ ] SearchResults component
- [ ] Institution detail page with React Router
- [ ] Institution listing page with filters & pagination
- [ ] Institution comparison feature (up to 3 institutions)
- [ ] Skeleton loading states for all pages
- [ ] Mobile responsive design
- [ ] Redis caching layer
- [ ] ElasticSearch integration (advanced search, autocomplete, fuzzy matching)
- [ ] Recently viewed feature (localStorage)
- [ ] .gitignore configuration
- [ ] Admin Dashboard UI with shadcn/ui components (stats, charts, tables, notifications)
- [ ] Admin Panel Backend (verification workflow, moderation tools, approval system, user management)
- [ ] Security & Auth system (JWT, rate limiting, security headers)
- [ ] AI Assistant with RAG (vector search, LLM integration, chat API)
- [ ] Community Features (Reviews, Q&A, Comments with moderation)
- [ ] Testing & QA (Unit tests, integration tests, pytest setup, fixtures)
- [ ] DevOps Infrastructure (CI/CD, staging/prod environments, deployment automation)
- [ ] SEO & Analytics (Dynamic meta tags, schema markup, sitemap, Google Analytics)
- [ ] Documentation (README, API docs, developer guide, deployment guide)
- [ ] Project Structure (Service layer, Makefile, pre-commit hooks, organized folders)
- [ ] Monitoring System (Performance metrics, Sentry error tracking, health checks)
- [ ] Data Quality System (Validation rules, duplicate detection, freshness alerts)
- [ ] Analytics System (Search tracking, page views, click events, dashboard)
- [ ] Data Backup & Recovery (Automated backups, verification, restore, retention)
- [ ] UI Polish (Dark mode, toast notifications, keyboard shortcuts)
- [ ] Advanced Search (Fuzzy matching, personalization, "Did you mean?")
- [ ] Frontend Types (all TypeScript definitions in types/)
- [ ] Frontend API Layer (client, auth, institutions, search, locations)
- [ ] Frontend Hooks (useSearch, useInstitution, useCompare, useRecentlyViewed, etc.)
- [ ] Frontend State Management (Zustand stores: auth, search, compare, ui)
- [ ] Frontend UI Components (Button, Input, Card, Modal)
- [ ] Frontend Search Components (SearchBar with autocomplete, SearchFilters)
- [ ] Frontend Institution Components (InstitutionCard, InstitutionDetail)

### ✅ COMPLETED
- [ ] Live scrapers (SSL/404 issues fixed, BMEB & MoE scrapers created)

### 📅 NEXT UP (Priority Order)
1. **Vercel deploy** - Push commit `51de5ec`, link both projects, set CI/CD secrets, first production deploy
2. **Mobile App** - React Native app (future)
3. **Growth Channels** - YouTube content, Campus ambassadors
4. **User Experience** - Saved searches, search history, notifications

### 🎯 CRITICAL GAPS IDENTIFIED
- **DevOps**: ✅ CI/CD, staging, and deployment automation implemented (incl. Vercel serverless deployment for frontend + backend)
- **Testing**: ✅ Test coverage implemented with pytest
- **Documentation**: ✅ API docs, developer guides, deployment guide complete (incl. Vercel deploy section)
- **Project Structure**: ✅ Service layer, Makefile, pre-commit hooks, organized folders
- **Monitoring**: ✅ Error tracking (Sentry), performance monitoring, metrics collection
- **Data**: ✅ Data validation, duplicate detection, freshness alerts implemented
- **Analytics**: ✅ Search tracking, page views, click events, admin dashboard
- **Backup**: ✅ Automated backups, verification, point-in-time recovery, retention policies
- **UI Polish**: ✅ Dark mode, toast notifications, keyboard shortcuts
- **Advanced Search**: ✅ Fuzzy matching, personalization, "Did you mean?"
- **Frontend Infrastructure**: ✅ ALL PHASES Complete - See `src/TODO.md`:
  - ✅ TypeScript types (types/ - 20+ entity definitions)
  - ✅ API client layer (api/ - 6 files, error handling)
  - ✅ Custom React hooks (hooks/ - 7 hooks)
  - ✅ State management (stores/ - 4 Zustand stores with persist)
  - ✅ UI component library (components/common/ - Button, Input, Card, Modal)
  - ✅ Search components (SearchBar with autocomplete, SearchFilters)
  - ✅ Institution components (InstitutionCard, InstitutionDetail)
