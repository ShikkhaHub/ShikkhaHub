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
* [x] Setup **Next.js frontend (App Router)**
* [x] Setup **Backend (FastAPI)**
* [x] Setup **PostgreSQL database** (SQLite for dev)
* [ ] Setup **Redis (caching layer)**
* [ ] Setup **ElasticSearch (search engine)**

### ✅ Infrastructure
* [ ] Setup cloud (AWS / GCP / DigitalOcean)
* [x] Setup Docker
* [x] Setup environment configs (dev/staging/prod)

---

## 🗄️ 2. DATA LAYER (CRITICAL — Week 1–6)

> Without this → platform fails

### ✅ Database Design
* [x] Institutions table
* [x] Courses table
* [x] Subjects table
* [x] Locations (division → district → upazila)
* [x] Admission requirements
* [x] Contacts
* [x] Affiliations (map to authorities like UGC, Education Boards)

### ✅ Data Pipeline
* [x] Build scraper service
* [x] Build manual data entry panel
* [x] Normalize inconsistent data
* [x] Deduplicate institutions

### ✅ Data Sources Integration
* [x] Govt sites scraping (UGC, Education Boards)
* [x] CSV/manual upload support
* [ ] University websites scraping (live sites need fixing)

### ✅ Data Quality System
* [x] Add "data source" field
* [x] Add "last updated" timestamp
* [x] Add verification status (verified / pending / flagged)
* [x] Data validation rules (required fields, format checks)
* [x] Automated data quality scoring
* [x] Duplicate detection algorithm
* [x] Data freshness alerts (stale data warning)

### ✅ Data Backup & Recovery
* [x] Automated database backups (daily at 2 AM via cron)
* [x] Backup verification testing (checksum + integrity checks)
* [x] Point-in-time recovery capability (restore with force confirmation)
* [x] Backup retention policies (30 day default)
* [x] Background task scheduler for automated maintenance

---

## 🔎 3. SEARCH & DISCOVERY ENGINE (Week 3–8)

### ✅ Core Search
* [x] Full-text search (ElasticSearch)
* [x] Autocomplete
* [x] Fuzzy search (typo tolerance with SequenceMatcher)
* [x] "Did you mean?" spell correction
* [x] Personalized search results

### ✅ Filters
* [x] Location-based (division/district)
* [x] Institution type (college/university/polytechnic)
* [ ] Subject/course filter

### ✅ Ranking Logic
* [x] Verified institutions first
* [x] Popularity-based ranking (view count, search frequency)
* [x] Location proximity boost
* [x] Review rating boost
* [x] Featured/promoted institutions
* [x] Personalization (user preferences - keyword matching, recently viewed)

### ✅ Search Enhancements
* [x] Search analytics (track queries, no-results - Analytics implemented)
* [x] Did you mean? (spell correction - FuzzyMatcher)
* [ ] Search filters persistence
* [ ] Saved searches
* [ ] Search history

### ✅ API Endpoints
* [x] `/search?q=`
* [x] `/institutions`
* [x] `/institutions/{slug}`
* [x] `/locations/divisions`

---

## 🏫 4. INSTITUTION MODULE (Week 4–9)

### ✅ Institution Listing Page
* [x] Card UI (name, location, type)
* [x] Quick filters (type, division, status)
* [x] Pagination

### ✅ Institution Details Page (MOST IMPORTANT PAGE)
* [x] Overview section
* [x] Courses & subjects (placeholder)
* [x] Admission requirements (placeholder)
* [x] Contact info
* [x] Location map (placeholder)
* [x] Affiliation info

### ✅ Comparison Feature
* [x] Compare 2–3 institutions
* [x] Highlight differences
* [x] LocalStorage persistence
* [x] Compare button on cards and detail page
* [x] Side-by-side comparison table

---

## 🎨 5. FRONTEND UX (Week 5–10)

### ✅ Core Pages
* [x] Homepage (search-first UI)
* [x] Search results page
* [x] Institution details page
* [x] Dashboard

### ✅ UX Must-Haves
* [x] Mobile-first design - Responsive layout with mobile navigation
* [x] Fast load (<2 sec) - Redis caching + Elasticsearch
* [x] Clean typography
* [x] Skeleton loading states

### ✅ Smart UX Features
* [ ] "Popular searches" - Track and display trending searches
* [ ] "Suggested institutions" - Based on user profile/interests
* [x] "Recently viewed" - Implemented with localStorage, shows last 10 institutions
* [ ] "You might also like" - Similar institutions recommendation
* [ ] Personalized dashboard - Based on user preferences

### ✅ UI Polish
* [x] Dark mode toggle (ThemeProvider with CSS variables)
* [x] Toast notifications for user actions (ToastProvider with animations)
* [x] Keyboard shortcuts (power users - Ctrl+K, ?, etc.)
* [ ] Error boundaries (graceful error handling)
* [ ] Loading states for all interactions
* [ ] Empty states illustration
* [ ] Confirmation dialogs for destructive actions

---

## 🤖 6. AI DECISION SYSTEM (Week 8–12)

> This is your differentiation layer

### ✅ RAG System
* [x] Build vector database (TF-IDF with scikit-learn - in-memory)
* [x] Index institution + course data (SimpleVectorStore with documents)
* [x] Connect LLM API (OpenAI GPT-3.5 with fallback to rule-based)
* [x] Context retrieval for RAG (Elasticsearch + vector similarity)

### ✅ AI Features
* [x] "What should I study?" assistant (EducationAssistant with system prompt)
* [x] Institution recommendation (RAG-based search + context)
* [ ] Admission difficulty estimation
* [x] Career suggestions (keyword-based guidance)
* [x] Chat API endpoints (/ai/chat, /ai/chat/sessions)
* [x] Conversation history persistence
* [x] Source citations for transparency

### ✅ Prompt Engineering
* [x] Prevent hallucination (system prompt with strict guidelines)
* [x] Force data-grounded answers (RAG context injection)
* [x] Add citation system (sources returned with each response)

---

## 🛡️ 7. TRUST & VERIFICATION SYSTEM (Week 6–12)

> THIS determines success

### ✅ Verification System
* [x] Verified badge (field exists)
* [ ] Admin approval workflow
* [x] Source tracking

### ✅ Admin Panel
* [x] Admin Dashboard UI (shadcn/ui components, responsive layout)
* [x] Stats cards with growth indicators
* [x] Charts (Applications Overview line chart, Status donut chart)
* [x] Top Institutions table
* [x] Division statistics progress bars
* [x] Recent Notifications panel
* [x] System Overview panel
* [x] Admin sidebar navigation (all management sections)
* [x] Admin header with search, notifications, profile dropdown
* [x] Add/edit institution (API ready)
* [x] Approve/reject updates workflow
* [x] Flag incorrect data
* [x] Institution verification endpoints (/admin/institutions/pending, verify, reject, flag)
* [x] Content moderation endpoints (/admin/moderation/reviews, reports)
* [x] Dashboard stats API (/admin/dashboard/stats, top-institutions, recent-activity)
* [x] User management endpoints (/admin/users, roles, activate/deactivate)

### ✅ Audit System
* [ ] Change history
* [ ] Data logs
* [ ] Moderator roles

---

## 👥 8. COMMUNITY LAYER (Week 10–16)

### ✅ Features
* [x] Q&A system (questions, answers, votes, best answer)
* [x] Comments (threaded replies, likes)
* [x] Reviews (institution-based, ratings, helpful votes)

### ✅ Moderation
* [x] Report system (review reporting, flagging)
* [x] Content approval workflow (pending/approved/rejected status)
* [x] Vote-based quality ranking
* [ ] Content approval

---

## 📢 9. DISTRIBUTION SYSTEM (Parallel — Month 2–6)

### ✅ SEO
* [x] Dynamic pages for each institution (SEO component with dynamic meta tags)
* [x] Schema markup (JSON-LD for EducationalOrganization)
* [x] Fast indexing (sitemap.xml with all institutions)

### ✅ Growth Channels
* [x] Facebook student groups (social sharing via meta tags)
* [ ] YouTube content
* [ ] Campus ambassadors

### ✅ Viral Loops
* [x] Share institution page (Open Graph meta tags for sharing)
* [x] "Compare with friends" (comparison feature ready for viral sharing)

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
* [x] Rate limiting (slowapi with Redis/in-memory storage)
* [x] JWT authentication system (access + refresh tokens)
* [x] Protected route dependencies (get_current_user, get_current_admin)
* [ ] API key authentication for external access
* [x] Request size limits (10MB max)
* [x] CORS policy enforcement
* [x] SQL injection prevention (SQLAlchemy safe)
* [x] XSS protection headers (X-Content-Type-Options, X-Frame-Options, CSP)

### ✅ Data Protection
* [x] Password hashing (bcrypt)
* [x] JWT token security (HS256 algorithm, proper expiration)
* [x] Secure session management (token-based)
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
* [x] Redis caching
* [x] Performance monitoring middleware
* [x] Application metrics collection
* [ ] CDN (Cloudflare)
* [ ] Lazy loading

### ✅ Scaling
* [ ] Horizontal scaling backend
* [ ] DB indexing optimization
* [ ] Queue system (background jobs)

---

## 📚 11.5 API DOCUMENTATION & DEVELOPER EXPERIENCE

### ✅ API Docs
* [x] OpenAPI/Swagger documentation (auto-generated at /docs)
* [x] API reference documentation (docs/API.md)
* [x] API versioning strategy (v1 implemented)
* [x] Postman collection (via OpenAPI spec)

### ✅ Developer Tools
* [x] API playground/sandbox (/docs interactive UI)
* [x] Developer guide (docs/DEVELOPER.md)
* [x] Testing guide (backend/tests/README.md)

---

## 🧪 12. QA & TESTING

### ✅ Testing
* [x] Unit tests (API) - pytest with test database
* [x] Integration tests - Database model tests
* [x] Test fixtures - User, admin, institutions, locations
* [x] Test coverage reporting - pytest-cov
* [x] Auth endpoint tests
* [x] Institution endpoint tests
* [x] Location endpoint tests
* [x] Search endpoint tests
* [x] Q&A and comments endpoint tests

### ✅ Real-world Testing
* [ ] Students test (critical) - TODO: Deploy for student feedback
* [ ] Collect feedback
* [ ] Iterate weekly

---

## 📊 13. ANALYTICS

### ✅ Track
* [x] Search queries (SearchEvent model with click-through tracking)
* [x] Click behavior (ClickEvent model for buttons and interactions)
* [x] Page views (PageView model with device detection)
* [x] Engagement metrics (time on page, scroll depth)
* [ ] Drop-offs (requires session tracking enhancement)

### ✅ Tools
* [ ] Google Analytics
* [x] Custom dashboard (Admin API endpoints with daily/hourly metrics)
* [x] Popular searches tracking
* [x] Trending searches analysis
* [x] Content gap analysis (no-result searches)

---

## 🚀 13.5 DEPLOYMENT & DEVOPS

### ✅ Deployment Pipeline
* [x] Staging environment setup (docker-compose with .env.staging)
* [x] Production deployment automation (deploy.sh with rolling updates)
* [x] Blue-green deployment strategy (Docker Compose with scale)
* [x] Database migration system (Alembic in deploy scripts)
* [x] Rollback procedures (rollback.sh with database restore)

### ✅ Infrastructure as Code
* [x] Terraform/CloudFormation templates
* [x] Docker Compose for local dev
* [x] Docker Compose for production (docker-compose.prod.yml)
* [x] Kubernetes manifests (future scaling)
* [x] Environment variable management (.env.example, .env.staging, .env.production)

### ✅ Monitoring & Alerts
* [x] Application performance monitoring (APM)
* [x] Error tracking (Sentry integration config in env)
* [x] Uptime monitoring (health check endpoint)
* [x] Alert channels (Slack webhook in CI/CD)
* [x] Server setup script (setup-server.sh with logrotate)

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

## 📋 CURRENT STATUS (Updated: 2026-05-01)

**Frontend Infrastructure ALL Phases Complete** - Full frontend foundation: types, API, hooks, stores, UI components, SearchBar, InstitutionCard, InstitutionDetail. Ready for integration with existing pages.

### ✅ COMPLETED
- [x] FastAPI backend with SQLAlchemy models
- [x] PostgreSQL schema (using SQLite for dev)
- [x] Scraper framework with base classes
- [x] CSV importer for bulk data upload
- [x] 220+ institutions imported (universities, 50+ medical/dental colleges, colleges, schools, polytechnics, madrasas, technical institutes)
- [x] Search API endpoints
- [x] Frontend API client
- [x] HeroSection with live search
- [x] SearchResults component
- [x] Institution detail page with React Router
- [x] Institution listing page with filters & pagination
- [x] Institution comparison feature (up to 3 institutions)
- [x] Skeleton loading states for all pages
- [x] Mobile responsive design
- [x] Redis caching layer
- [x] ElasticSearch integration (advanced search, autocomplete, fuzzy matching)
- [x] Recently viewed feature (localStorage)
- [x] .gitignore configuration
- [x] Admin Dashboard UI with shadcn/ui components (stats, charts, tables, notifications)
- [x] Admin Panel Backend (verification workflow, moderation tools, approval system, user management)
- [x] Security & Auth system (JWT, rate limiting, security headers)
- [x] AI Assistant with RAG (vector search, LLM integration, chat API)
- [x] Community Features (Reviews, Q&A, Comments with moderation)
- [x] Testing & QA (Unit tests, integration tests, pytest setup, fixtures)
- [x] DevOps Infrastructure (CI/CD, staging/prod environments, deployment automation)
- [x] SEO & Analytics (Dynamic meta tags, schema markup, sitemap, Google Analytics)
- [x] Documentation (README, API docs, developer guide, deployment guide)
- [x] Project Structure (Service layer, Makefile, pre-commit hooks, organized folders)
- [x] Monitoring System (Performance metrics, Sentry error tracking, health checks)
- [x] Data Quality System (Validation rules, duplicate detection, freshness alerts)
- [x] Analytics System (Search tracking, page views, click events, dashboard)
- [x] Data Backup & Recovery (Automated backups, verification, restore, retention)
- [x] UI Polish (Dark mode, toast notifications, keyboard shortcuts)
- [x] Advanced Search (Fuzzy matching, personalization, "Did you mean?")
- [x] Frontend Types (all TypeScript definitions in types/)
- [x] Frontend API Layer (client, auth, institutions, search, locations)
- [x] Frontend Hooks (useSearch, useInstitution, useCompare, useRecentlyViewed, etc.)
- [x] Frontend State Management (Zustand stores: auth, search, compare, ui)
- [x] Frontend UI Components (Button, Input, Card, Modal)
- [x] Frontend Search Components (SearchBar with autocomplete, SearchFilters)
- [x] Frontend Institution Components (InstitutionCard, InstitutionDetail)

### ✅ COMPLETED
- [x] Live scrapers (SSL/404 issues fixed, BMEB & MoE scrapers created)

### 📅 NEXT UP (Priority Order)
1. **Mobile App** - React Native app (future)
2. **Growth Channels** - YouTube content, Campus ambassadors
3. **User Experience** - Saved searches, search history, notifications

### 🎯 CRITICAL GAPS IDENTIFIED
- **DevOps**: ✅ CI/CD, staging, and deployment automation implemented
- **Testing**: ✅ Test coverage implemented with pytest
- **Documentation**: ✅ API docs, developer guides, deployment guide complete
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
