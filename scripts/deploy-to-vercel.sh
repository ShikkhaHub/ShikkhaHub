#!/bin/bash
# Deploy ShikkhaHub to Vercel (Frontend + Backend)
# Run this from the project root directory with proper credentials
# Prerequisites:
#   - Vercel CLI installed: npm install -g vercel@latest
#   - GitHub CLI configured: gh auth login
#   - Vercel projects already created (frontend + backend)
#   - Environment variables configured on each project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}ShikkhaHub Vercel Deployment${NC}"
echo -e "${YELLOW}================================${NC}\n"

# Check if VERCEL_TOKEN is set
if [ -z "$VERCEL_TOKEN" ]; then
    echo -e "${RED}Error: VERCEL_TOKEN not set${NC}"
    echo "Set VERCEL_TOKEN environment variable:"
    echo "export VERCEL_TOKEN=your_token_here"
    exit 1
fi

# Check if we're in the project root
if [ ! -f "package.json" ] || [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo -e "${RED}Error: Not in project root directory${NC}"
    echo "Please run this script from the ShikkhaHub project root"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"

# Deploy Frontend
echo -e "${YELLOW}Deploying Frontend...${NC}"
cd frontend

if [ ! -f ".vercel/project.json" ]; then
    echo -e "${RED}Error: Frontend not linked to Vercel${NC}"
    echo "Run: cd frontend && vercel link"
    exit 1
fi

echo "Building frontend..."
pnpm build

echo "Deploying to Vercel..."
vercel deploy --prod --token=$VERCEL_TOKEN

FRONTEND_URL=$(vercel ls --prod --token=$VERCEL_TOKEN 2>/dev/null | head -1 | awk '{print $1}')
echo -e "${GREEN}✓ Frontend deployed: https://${FRONTEND_URL}${NC}\n"

cd ..

# Deploy Backend
echo -e "${YELLOW}Deploying Backend...${NC}"
cd backend

if [ ! -f ".vercel/project.json" ]; then
    echo -e "${RED}Error: Backend not linked to Vercel${NC}"
    echo "Run: cd backend && vercel link"
    exit 1
fi

echo "Building backend..."
# No explicit build needed for FastAPI, Vercel does it automatically

echo "Deploying to Vercel..."
vercel deploy --prod --token=$VERCEL_TOKEN

BACKEND_URL=$(vercel ls --prod --token=$VERCEL_TOKEN 2>/dev/null | head -1 | awk '{print $1}')
echo -e "${GREEN}✓ Backend deployed: https://${BACKEND_URL}${NC}\n"

cd ..

# Verify deployments
echo -e "${YELLOW}Verifying deployments...${NC}\n"

echo "Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${FRONTEND_URL}")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend responding (HTTP ${FRONTEND_STATUS})${NC}"
else
    echo -e "${RED}✗ Frontend not responding (HTTP ${FRONTEND_STATUS})${NC}"
fi

echo "Testing backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${BACKEND_URL}/api/v1/health")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check passed (HTTP ${BACKEND_STATUS})${NC}"
else
    echo -e "${RED}✗ Backend health check failed (HTTP ${BACKEND_STATUS})${NC}"
fi

echo "Testing search endpoint..."
SEARCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://${BACKEND_URL}/api/v1/institutions/search?q=dhaka")
if [ "$SEARCH_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Search endpoint working (HTTP ${SEARCH_STATUS})${NC}"
else
    echo -e "${RED}✗ Search endpoint failed (HTTP ${SEARCH_STATUS})${NC}"
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo "Frontend URL: https://${FRONTEND_URL}"
echo "Backend URL: https://${BACKEND_URL}/api/v1"
echo ""
echo "Next steps:"
echo "1. Update VITE_API_URL on frontend project in Vercel"
echo "2. Test the live application"
echo "3. Monitor logs in Vercel dashboard"
echo "4. Configure monitoring (Sentry, analytics)"
