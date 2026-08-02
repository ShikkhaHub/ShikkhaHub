# 🚀 Vercel Deployment Checklist

**Status:** Ready for Production | **Target Date:** ASAP

---

## ⚠️ IMMEDIATE ACTIONS REQUIRED (Do These First)

### 1. Create Vercel Projects

**Frontend Project:**
```bash
# Visit https://vercel.com/new
# Connect GitHub: ShikkhaHub/ShikkhaHub repository
# Create project "shikkhahub-ss"
# Root directory: frontend/
# Accept defaults, click Deploy

# After deployment completes, verify .vercel/project.json exists
```

**Backend Project:**
```bash
# Repeat for backend
# Create project "shikkhahub-backend"
# Root directory: backend/
# Runtime: Python 3.12 (auto-detected)
```

**Get Project IDs:**
- From Vercel Dashboard → Project Settings → General
- Look for "Project ID" field
- Copy both IDs to notepad

### 2. Add GitHub Secrets (CRITICAL)

Visit: https://github.com/ShikkhaHub/ShikkhaHub/settings/secrets/actions

**Create these secrets:**

| Name | Value | How to Get |
|------|-------|-----------|
| `VERCEL_TOKEN` | Your Vercel access token | https://vercel.com/account/tokens → Create Token → Full Access |
| `VERCEL_ORG_ID` | Your Vercel Team ID | https://vercel.com/account/settings → Team Settings → Team ID |
| `VERCEL_PROJECT_ID_FRONTEND` | Frontend project ID | Vercel Dashboard → shikkhahub-ss → Settings → General → Project ID |
| `VERCEL_PROJECT_ID_BACKEND` | Backend project ID | Vercel Dashboard → shikkhahub-backend → Settings → General → Project ID |

**Verification:**
```bash
# These secrets appear as *** in GitHub Actions logs
# If missing, CI/CD will fail with auth errors
```

### 3. Configure Backend Environment Variables

**In Vercel Dashboard → shikkhahub-backend → Settings → Environment Variables:**

```env
DATABASE_URL=postgresql://user:password@host/dbname
# Options:
# - Vercel Postgres: https://vercel.com/docs/storage/vercel-postgres
# - Neon: https://neon.tech
# - Supabase: https://supabase.com

SECRET_KEY=<random 32 character string>
# Generate: python -c "import secrets; print(secrets.token_urlsafe(32))"

BACKEND_CORS_ORIGINS=["https://shikkhahub-ss.vercel.app"]

ENVIRONMENT=production

DEBUG=false

OPENAI_API_KEY=sk-...
# Get from https://platform.openai.com/account/api-keys

# Optional (graceful degradation if not set):
REDIS_URL=redis://...
ELASTICSEARCH_URL=http://elasticsearch:9200
```

### 4. Configure Frontend Environment Variables

**In Vercel Dashboard → shikkhahub-ss → Settings → Environment Variables:**

```env
VITE_API_URL=https://shikkhahub-backend.vercel.app/api/v1
```

### 5. Trigger First Deployment

```bash
# From your local machine with GitHub access
cd /vercel/share/v0-project
git push origin v0/mdselim606570-9293-d1524972:main

# Monitor deployment at:
# https://github.com/ShikkhaHub/ShikkhaHub/actions
```

---

## ✅ Verification After Deployment

### Backend Health Check
```bash
curl -s https://shikkhahub-backend.vercel.app/api/v1/health | jq

# Expected response:
# {
#   "status": "ok",
#   "timestamp": "2026-08-01T12:00:00",
#   "environment": "production"
# }
```

### API Endpoints Test
```bash
# Search institutions
curl -s "https://shikkhahub-backend.vercel.app/api/v1/institutions/search?q=dhaka" | jq '.data[0]'

# List locations
curl -s "https://shikkhahub-backend.vercel.app/api/v1/locations/divisions" | jq

# Check API docs
# Visit: https://shikkhahub-backend.vercel.app/docs
```

### Frontend Verification
1. Visit: https://shikkhahub-ss.vercel.app
2. Test search functionality
3. Click on an institution
4. Verify API calls in browser DevTools Network tab

---

## 🐛 Troubleshooting

### Problem: "VERCEL_TOKEN not found" in CI/CD logs

**Solution:** Add `VERCEL_TOKEN` secret (see step 2 above)

```bash
# Verify secret exists
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/ShikkhaHub/ShikkhaHub/actions/secrets
```

### Problem: Backend deployment fails with "Runtime not found"

**Solution:** Verify `backend/vercel.json` exists and contains:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "functions": {
    "api/index.py": {
      "maxDuration": 60,
      "excludeFiles": "{tests/**,scripts/**,**/__pycache__/**,**/*.pyc}"
    }
  },
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index" }
  ]
}
```

Note: the Python runtime is auto-detected (no `runtime` key — an explicit `runtime`
value causes "Function Runtimes must have a valid version"). The FastAPI app is
exposed through the `api/index.py` entrypoint, which imports `app` from `app.main`.

### Problem: Frontend returns "Cannot GET /institutions/123"

**Solution:** Verify `frontend/vercel.json` has SPA rewrite:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Problem: CORS errors in browser console

**Solution:** Check `BACKEND_CORS_ORIGINS` includes frontend URL:

```bash
# Backend should allow:
["https://shikkhahub-ss.vercel.app"]

# NOT: ["*"]  # Security risk
```

### Problem: Database connection refused

**Solution:** Verify `DATABASE_URL` in Vercel environment:

```bash
# Format: postgresql://user:password@host:port/database
# NOT: postgresql://localhost/shikkhahub  # Won't work on Vercel!

# Test connection locally:
psql "postgresql://user:password@host:port/database" -c "SELECT 1"
```

---

## 📋 Post-Deployment Checklist

- [ ] Backend API responding (/health endpoint)
- [ ] Frontend accessible and loads
- [ ] Search functionality works
- [ ] Institution details page loads
- [ ] Admin dashboard accessible (with auth)
- [ ] No console errors in browser
- [ ] No 5xx errors in Vercel logs
- [ ] Google Analytics events firing
- [ ] Monitoring alerts configured

---

## 🔐 Security Verification

After deployment, verify:

- [ ] All secrets are **hidden** in Vercel (show as `***` in logs)
- [ ] HTTPS enforced (URLs are `https://`, not `http://`)
- [ ] CORS only allows frontend domain
- [ ] DEBUG=false in production
- [ ] JWT SECRET_KEY is random, not "secret"
- [ ] No API keys logged (check Vercel Function logs)

---

## 📞 Support

If deployment fails:

1. **Check Vercel Function Logs:**
   ```
   Vercel Dashboard → Project → Deployments → [Latest] → Function Logs
   ```

2. **Check CI/CD Logs:**
   ```
   GitHub → Actions → [Latest Workflow] → [Step that failed]
   ```

3. **Run Smoke Tests Locally:**
   ```bash
   cd backend && python -m pytest tests/test_health.py -v
   cd frontend && npm test
   ```

4. **Common Error Codes:**
   - **Exit code 1** → Build failed (check build logs)
   - **Exit code 128** → Git auth issue
   - **Timeout** → Function took >60 seconds (max on Vercel)

---

## 🎯 Next Steps After Successful Deployment

1. ✅ Production deployment live
2. [ ] Mobile app development (React Native)
3. [ ] Growth channels (YouTube, Campus ambassadors)
4. [ ] Monitoring & alerting setup
5. [ ] Performance optimization
6. [ ] User feedback collection

**Estimated Time:** 30 min to 1 hour for complete deployment

---

**Last Updated:** August 1, 2026
