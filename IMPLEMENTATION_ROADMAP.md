# ShikkhaHub Implementation Roadmap (2026)

**Status:** Vercel Deployment Setup Complete ✅ | Next: Production Deployment

**Current Date:** August 1, 2026 | **Deadline:** February 1, 2027 (6 months)

---

## Executive Summary

ShikkhaHub has completed foundational work:
- ✅ Full backend API (FastAPI, PostgreSQL, Redis, Elasticsearch)
- ✅ Complete frontend (React/Vite with TypeScript)
- ✅ Search engine with AI assistant
- ✅ Admin dashboard & moderation tools
- ✅ Vercel serverless deployment configs
- ✅ CI/CD pipeline ready

**Immediate Action Required:** Deploy to production on Vercel by setting GitHub secrets.

**Critical Success Factor:** Database accuracy across 10,000+ institutions in Bangladesh.

---

## Phase 1: Complete Vercel Deployment (Week 1)

### Current Status
- ✅ Vercel configs created (`frontend/vercel.json`, `backend/vercel.json`)
- ✅ CI/CD workflow written (`.github/workflows/vercel-deploy.yml`)
- ✅ Commit pushed to `v0/mdselim606570-9293-d1524972` branch
- ⚠️ **Blocked:** GitHub secrets not yet configured

### Deployment Checklist

**Step 1: Create Vercel Projects**
```bash
# Visit https://vercel.com/new
# Create two projects:
# 1. "shikkhahub-frontend" (Root: frontend/)
# 2. "shikkhahub-backend" (Root: backend/)

# Retrieve project IDs from .vercel/project.json after linking
vercel link --yes
```

**Step 2: Set GitHub Secrets**
Configure these in https://github.com/ShikkhaHub/ShikkhaHub/settings/secrets/actions:

| Secret | Source | Notes |
|--------|--------|-------|
| `VERCEL_TOKEN` | [Vercel Tokens](https://vercel.com/account/tokens) | Create with "Full Access" scope |
| `VERCEL_ORG_ID` | `.vercel/project.json` → `orgId` | Team ID for both projects |
| `VERCEL_PROJECT_ID_FRONTEND` | Frontend project settings | From Vercel dashboard |
| `VERCEL_PROJECT_ID_BACKEND` | Backend project settings | From Vercel dashboard |

**Step 3: Configure Environment Variables**

**Backend (Vercel Production):**
- `DATABASE_URL` → PostgreSQL connection (use Vercel Postgres, Neon, or Supabase)
- `REDIS_URL` → Redis instance (optional, degrades gracefully)
- `ELASTICSEARCH_URL` → Elasticsearch (optional, uses DB fallback)
- `OPENAI_API_KEY` → OpenAI API key for AI assistant
- `SECRET_KEY` → Random 32-char string
- `BACKEND_CORS_ORIGINS` → `["https://shikkhahub-frontend.vercel.app"]`
- `ENVIRONMENT` → `production`
- `DEBUG` → `false`

**Frontend (Vercel Production):**
- `VITE_API_URL` → `https://shikkhahub-backend.vercel.app/api/v1`

**Step 4: First Deployment**
Push commit to `main` branch → GitHub Actions automatically deploys both projects.

```bash
# From local machine with GitHub auth:
git push origin v0/mdselim606570-9293-d1524972:main
```

### Testing Post-Deployment
```bash
# Backend health check
curl https://shikkhahub-backend.vercel.app/api/v1/health

# Frontend - visit https://shikkhahub-frontend.vercel.app
# - Homepage loads
# - Search works
# - Institution details page accessible
# - Admin dashboard requires auth
```

---

## Phase 2: Build Mobile App (Week 2–4)

### Approach: React Native Monorepo

**Architecture:**
- Share API client & types between web and mobile
- React Native Expo for fast development
- Same FastAPI backend

**Step 1: Setup React Native Project**
```bash
# In project root
npx create-expo-app mobile
cd mobile
npx expo install expo-router
```

**Step 2: Share Code**
```
packages/
├── api-client/          # Shared with frontend
├── types/               # Shared types (Institution, Location, etc.)
└── ui-components/       # Reusable components
```

**Step 3: Core Screens**
- `SearchScreen` — Search + filters
- `InstitutionListScreen` — Results
- `InstitutionDetailScreen` — Full details + AI assistant
- `ComparisonScreen` — Side-by-side comparison
- `AuthScreen` — Login/signup

**Step 4: Deploy**
- iOS: TestFlight (requires Apple developer account)
- Android: Google Play Store
- Staging: EAS Build (Expo managed build service)

---

## Phase 3: Growth Channels (Week 4–8)

### 3.1 Social Media Distribution

**Facebook**
- Student group posts (manual initially, then automated via Meta API)
- "Compare institutions" viral hook
- Retargeting ads for top searches

**YouTube**
- "Top 10 universities in Bangladesh"
- "How to choose a college"
- SEO-optimized channel (10+ videos month 1)

### 3.2 Campus Ambassador Program

**Recruitment:**
- 50 ambassadors across top universities
- Referral commission system (track via `referrer_id`)
- Leaderboard in admin dashboard

**Incentives:**
- Monthly prizes
- Feature on app ("Ambassador of the Month")
- Co-marketing opportunities

### 3.3 Viral Loops

**Share Feature:**
- "Compare 2 institutions" → Share link → Shows comparison (no signup required)
- "Recommend to a friend" → Referral code → Unlock premium (future)

**Implementation:**
```
/share/:institutionIds  # Compare link
/ref/:referrerId        # Referral link
```

---

## Phase 4: Enhance UX Features (Week 8–12)

### 4.1 Saved Searches & History
- ✅ Recently viewed (localStorage)
- [ ] Saved searches (needs auth + database)
- [ ] Search history (frontend + backend tracking)

**Implementation:**
```typescript
// SavedSearch table
CREATE TABLE saved_searches (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  query TEXT,
  filters JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

// API endpoints
GET /api/v1/users/{user_id}/saved-searches
POST /api/v1/users/{user_id}/saved-searches
DELETE /api/v1/users/{user_id}/saved-searches/{id}
```

### 4.2 Notification System
- "New institutions in your area"
- "Admission deadlines approaching"
- "New reviews from your saved institutions"

### 4.3 Personalized Dashboard
- User interests (selected subjects + divisions)
- Recommended institutions
- Saved searches
- Search stats ("10 searches this month")

---

## Phase 5: Scale & Monitor Production (Week 12–16)

### 5.1 Performance Optimization

**Frontend:**
- ✅ Code splitting (Vite handles automatically)
- [ ] Image optimization (WebP, lazy loading)
- [ ] Service Worker for offline support

**Backend:**
- ✅ Redis caching layer
- [ ] Database query optimization (add indexes)
- [ ] Elasticsearch caching (cache popular searches)

### 5.2 Monitoring Stack

**Error Tracking:** Sentry
```python
import sentry_sdk
sentry_sdk.init("https://key@sentry.io/project")
```

**Performance:** New Relic / Datadog
- Transaction tracing (search queries, institution fetches)
- Database slow query logs
- API latency metrics

**Uptime:** Healthchecks.io
```bash
# Ping from backend health endpoint
curl https://healthchecks.io/ping/{uuid}
```

**Analytics:** Google Analytics 4 + Custom Dashboard
- Trending searches
- User journey (search → institution → action)
- Geography heatmap (which divisions searched most)

### 5.3 Database Optimization

**Indexes to Add:**
```sql
CREATE INDEX idx_institutions_type ON institutions(type);
CREATE INDEX idx_institutions_division ON institutions(division_id);
CREATE INDEX idx_institutions_status ON institutions(is_verified);
CREATE INDEX idx_search_events_query ON search_events(query);
```

**Regular Maintenance:**
```sql
-- Run weekly
VACUUM ANALYZE;

-- Archive old logs (keep 90 days)
DELETE FROM search_events WHERE created_at < NOW() - INTERVAL '90 days';
```

---

## Phase 6: Iteration & Polish (Week 16–26)

### 6.1 User Feedback Loop
- Deploy beta access (500 students)
- Weekly surveys ("What would make this 10x better?")
- Track drop-off points in analytics
- A/B test search UI variations

### 6.2 Feature Validation

**Top Priorities (in order of impact):**
1. **Admission Calculator** — "Based on SSC score, what can I get into?"
2. **Cost Comparison** — Tuition + living expenses by institution
3. **Career Outcomes** — "Where do XYZ university graduates work?"
4. **Scholarship Finder** — "Apply for 10 scholarships in 2 minutes"

### 6.3 Community Growth
- ✅ Q&A system exists
- [ ] Moderation team (5 people)
- [ ] Content guidelines & enforcement
- [ ] Reputation system (badges for helpful answers)

---

## Technical Debt & Risk Management

### Critical Risks
1. **Database Accuracy** — If institutions are wrong, platform fails
   - Mitigation: Weekly spot-check 5% of data, automated freshness alerts

2. **API Rate Limiting** — Peak traffic could overwhelm server
   - Mitigation: Vercel auto-scales, but monitor cold starts

3. **Elasticsearch Downtime** — Search service degradation
   - Mitigation: Fallback to PostgreSQL full-text search ✅ implemented

4. **Vendor Lock-in** — Heavy Vercel + OpenAI dependency
   - Mitigation: Keep FastAPI portable, use standard OpenAI API

### Technical Debt to Address
- [ ] Unit test coverage < 50% (aim for 80%)
- [ ] API documentation needs updating (schemas drift)
- [ ] Admin dashboard performance (loading 10,000 institutions)
- [ ] Mobile app offline mode

---

## Budget & Resource Allocation

**Estimated Monthly Cost (Production):**
- Vercel hosting: $20–50 (Frontend + Backend)
- PostgreSQL (Neon/Supabase): $50–100
- Elasticsearch: $20 (or $0 with fallback)
- Redis (Upstash): $10
- OpenAI API: $50–200 (depends on usage)
- Sentry monitoring: $29
- **Total: $170–430/month**

**Team Structure (Recommended):**
- 1 Backend Engineer (maintenance + API)
- 1 Frontend Engineer (UX + web)
- 1 Mobile Engineer (React Native)
- 1 DevOps (deployment + monitoring)
- 1 Product Manager
- 1 QA Engineer

---

## Success Metrics (Key Results)

### By End of Month 1:
- [ ] Vercel deployment live & stable
- [ ] 99.5% API uptime
- [ ] <500ms avg search latency
- [ ] Mobile app (iOS TestFlight, Android internal testing)

### By End of Month 3:
- [ ] 10,000+ institutions in database
- [ ] 5,000 daily active users
- [ ] 50 campus ambassadors
- [ ] YouTube channel (10+ videos, 1,000 subscribers)

### By End of Month 6:
- [ ] 50,000 daily active users
- [ ] Mobile app launched on App Store + Play Store
- [ ] 200+ campus ambassadors
- [ ] Featured in 5 major news outlets
- [ ] SEO ranking #1 for "universities in Bangladesh"

---

## Git Workflow

**Branch Strategy:**
```
main (production)
├── staging (staging environment)
│   ├── feature/mobile-app
│   ├── feature/growth-channels
│   ├── feature/saved-searches
│   └── bugfix/search-optimization
```

**Before Merging to Main:**
1. Code review (2+ approvals)
2. All tests pass (CI/CD)
3. Staging deployed & tested
4. Product sign-off
5. Merge and auto-deploy to production

---

## Appendix: Quick Links

- **Vercel Dashboard:** https://vercel.com/dashboard
- **GitHub Repo:** https://github.com/ShikkhaHub/ShikkhaHub
- **API Docs:** https://shikkhahub-backend.vercel.app/docs
- **Database:** (configure in Vercel secrets)
- **Sentry Alerts:** https://sentry.io
- **Analytics:** https://analytics.google.com

---

**Last Updated:** August 1, 2026
**Next Review:** August 8, 2026 (Post-deployment)
