# ShikkhaHub Architecture

## System Overview

ShikkhaHub is a full-stack education platform built with modern technologies and best practices.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
├─────────────────────────────────────────────────────────────┤
│  React + TypeScript + Tailwind CSS                          │
│  ├── Public Pages (Home, Search, Institution Detail)        │
│  ├── User Dashboard (Recently Viewed, Saved)                │
│  ├── Admin Dashboard (Stats, Moderation)                  │
│  └── AI Chat Interface                                      │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ HTTPS / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Load Balancer                          │
│                      (Nginx + SSL)                          │
└─────────────────────────────────────────────────────────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐
│  FastAPI Backend │ │  FastAPI Backend │ │  Frontend    │
│     (API v1)     │ │     (API v1)     │ │   (Static)   │
│   ┌──────────┐   │ │   ┌──────────┐   │ │              │
│   │ Auth     │   │ │   │ Auth     │   │ │              │
│   │ Search   │   │ │   │ Search   │   │ │              │
│   │ Admin    │   │ │   │ Admin    │   │ │              │
│   │ AI       │   │ │   │ AI       │   │ │              │
│   └──────────┘   │ │   └──────────┘   │ │              │
└──────────────────┘ └──────────────────┘ └──────────────┘
            │                │
            └────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
         ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌─────────────┐
│ PostgreSQL  │ │  Redis  │ │Elasticsearch│
│ (Main DB)   │ │ (Cache) │ │  (Search)   │
└─────────────┘ └─────────┘ └─────────────┘
```

## Component Details

### Frontend Layer

**Technology Stack:**
- **Framework**: React 18.2 + TypeScript
- **Routing**: React Router 6
- **Styling**: Tailwind CSS 3.4
- **Build Tool**: Vite 5.2
- **UI Components**: shadcn/ui + Radix UI
- **State Management**: React Query (TanStack Query) + localStorage
- **Icons**: Lucide React

**Key Components:**
1. **SEO Component** - Dynamic meta tags, Open Graph, Schema markup
2. **Search Components** - HeroSection, SearchResults, Filters
3. **Institution Components** - Cards, Detail view, Comparison
4. **Admin Components** - Dashboard, Tables, Charts
5. **AI Components** - Chat interface

### Backend Layer

**Technology Stack:**
- **Framework**: FastAPI 0.111.0
- **ORM**: SQLAlchemy 2.0+
- **Authentication**: JWT with refresh tokens
- **Validation**: Pydantic v2
- **Testing**: Pytest with 50+ tests

**Architecture Pattern: Layered Architecture**

```
┌────────────────────────────────────────┐
│           API Layer (Endpoints)          │
│  - Route definitions                     │
│  - Request/Response handling             │
│  - Authentication/Authorization          │
├────────────────────────────────────────┤
│         Service Layer                  │
│  - Business logic                      │
│  - Data processing                     │
│  - External API integration            │
├────────────────────────────────────────┤
│         Data Access Layer              │
│  - Database queries                    │
│  - Caching operations                  │
│  - Search indexing                     │
├────────────────────────────────────────┤
│         Model Layer                    │
│  - SQLAlchemy models                   │
│  - Database schema                     │
└────────────────────────────────────────┘
```

### Data Layer

**PostgreSQL (Primary Database):**
- Institutions (220+ records)
- Locations (Divisions, Districts, Upazilas)
- Users & Authentication
- Reviews, Q&A, Comments
- Chat sessions

**Redis (Cache Layer):**
- API response caching
- Session management
- Rate limiting
- Search result caching (5 min TTL)
- Institution data caching

**Elasticsearch (Search Engine):**
- Full-text search
- Fuzzy matching
- Autocomplete suggestions
- Faceted filtering

### External Services

**OpenAI:**
- GPT-3.5 for AI assistant
- RAG (Retrieval Augmented Generation)
- Context-aware responses

**Monitoring (Future):**
- Sentry for error tracking
- Google Analytics for user behavior
- Uptime monitoring

## Data Flow

### 1. Institution Search Flow

```
User → Search Input
  ↓
Frontend validates query
  ↓
API Request: GET /api/v1/search/advanced?q={query}
  ↓
Backend: Rate limiting check
  ↓
Cache check (Redis)
  ↓
Elasticsearch search (with fallback to DB)
  ↓
Cache results (5 min TTL)
  ↓
Return JSON response
  ↓
Frontend renders results
```

### 2. AI Chat Flow

```
User → Message Input
  ↓
Frontend: POST /api/v1/ai/chat
  ↓
Backend: Get conversation history
  ↓
Vector search (TF-IDF) for context
  ↓
Elasticsearch search for institutions
  ↓
Build context from retrieved documents
  ↓
Call OpenAI API with context
  ↓
Store response in database
  ↓
Return AI response with sources
  ↓
Frontend displays message + citations
```

### 3. Admin Moderation Flow

```
Admin → Reviews Dashboard
  ↓
GET /api/v1/admin/moderation/reviews/pending
  ↓
Admin reviews content
  ↓
POST /api/v1/admin/reviews/{id}/approve
  ↓
Update review status
  ↓
Recalculate institution ratings
  ↓
Clear related caches
  ↓
Send notification to user
```

## Security Architecture

### Authentication Flow

```
User Login
  ↓
Password verification (bcrypt)
  ↓
Generate JWT access token (30 min)
  ↓
Generate refresh token (7 days)
  ↓
Return tokens to client
  ↓
Client stores in memory/localStorage
  ↓
Subsequent requests include Bearer token
  ↓
Server validates token on each request
```

### Security Measures

1. **Rate Limiting**
   - Auth endpoints: 5 requests/minute
   - API endpoints: 100 requests/minute
   - Search endpoints: 200 requests/minute

2. **Input Validation**
   - Pydantic schema validation
   - SQL injection prevention (SQLAlchemy ORM)
   - XSS protection (security headers)

3. **Data Protection**
   - Password hashing (bcrypt)
   - JWT token expiration
   - HTTPS only (production)
   - Secure cookies

4. **CORS Policy**
   - Whitelist allowed origins
   - Credentials enabled
   - Preflight caching

## Caching Strategy

### Multi-Level Caching

```
L1: Browser Cache (Static assets)
  ├── CSS/JS files: 1 year
  └── Images: 1 year

L2: CDN Cache (Cloudflare)
  ├── Static pages: 1 hour
  └── API responses: 5 minutes

L3: Redis Cache (Application)
  ├── Institution details: 5 minutes
  ├── Search results: 5 minutes
  ├── Autocomplete: 1 hour
  └── User sessions: 24 hours

L4: Database Cache (PostgreSQL)
  ├── Query results: Configured by PostgreSQL
  └── Connection pooling
```

## Scalability Considerations

### Horizontal Scaling

1. **Stateless Backend**
   - No local session storage
   - JWT authentication
   - Shared Redis cache

2. **Database Scaling**
   - Read replicas for queries
   - Connection pooling
   - Query optimization

3. **Search Scaling**
   - Elasticsearch clustering
   - Sharding by location/type

4. **CDN Integration**
   - Static assets on CDN
   - API response caching
   - DDoS protection

### Future Optimizations

- GraphQL for flexible queries
- Microservices for AI/Search
- Kubernetes orchestration
- Message queue for background jobs

## Deployment Architecture

### CI/CD Pipeline

```
Developer Push
  ↓
GitHub Actions Trigger
  ├─ Backend Tests (pytest)
  ├─ Frontend Tests (jest)
  ├─ Linting (flake8, eslint)
  └─ Type Checking (mypy, tsc)
  ↓
Build Docker Images
  ↓
Push to Docker Hub
  ↓
Deploy to Staging (develop branch)
  or
Deploy to Production (main branch)
  ↓
Run Migrations
  ↓
Health Checks
  ↓
Slack Notification
```

### Environment Strategy

- **Development**: Local with SQLite/PostgreSQL
- **Staging**: Docker Compose on VPS
- **Production**: Docker Compose with SSL, monitoring

## Monitoring & Observability

### Health Checks

- `/api/v1/health` - API health
- `/api/v1/health/db` - Database connectivity
- `/api/v1/health/cache` - Redis connectivity
- `/api/v1/health/search` - Elasticsearch connectivity

### Metrics to Track

1. **Performance**
   - API response time
   - Database query time
   - Search latency
   - Page load time

2. **Business**
   - Search queries
   - Institution views
   - AI chat sessions
   - Review submissions

3. **Infrastructure**
   - CPU/Memory usage
   - Database connections
   - Cache hit rate
   - Error rate

## API Design Principles

1. **RESTful Design**
   - Resource-based URLs
   - HTTP methods (GET, POST, PUT, DELETE)
   - Standard status codes

2. **Versioning**
   - URL-based versioning (/api/v1/)
   - Backward compatibility

3. **Pagination**
   - Offset-based pagination
   - Consistent response format

4. **Error Handling**
   - Structured error responses
   - Clear error messages
   - Appropriate status codes

## Frontend Architecture

### Component Hierarchy

```
App
├── Public Routes
│   ├── Dashboard (Home)
│   ├── InstitutionListing
│   ├── InstitutionDetail
│   └── ComparePage
├── Admin Routes
│   └── AdminDashboard
└── Shared Components
    ├── Layout
    ├── SEO
    ├── Loading States
    └── Error Boundaries
```

### State Management

1. **Server State**: React Query (TanStack Query)
   - Caching
   - Background refetching
   - Optimistic updates

2. **Client State**: React Context + useState
   - UI state
   - Form state
   - Local preferences

3. **Persistent State**: localStorage
   - Recently viewed
   - Comparison list
   - Theme preferences

## Development Workflow

### Local Development

```
make install      # Install dependencies
make dev          # Start both backend and frontend
make test         # Run tests
make lint         # Check code style
make format       # Format code
```

### Testing Strategy

1. **Unit Tests**: Individual functions/components
2. **Integration Tests**: API endpoints
3. **E2E Tests**: User workflows (future)

## Conclusion

ShikkhaHub uses a modern, scalable architecture with:
- Separation of concerns
- Multiple caching layers
- Comprehensive security
- Automated CI/CD
- Extensive documentation

This architecture supports the current feature set while enabling future growth.
