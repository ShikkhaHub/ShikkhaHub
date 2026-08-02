#!/bin/bash
# Deploy ShikkhaHub to Vercel (Frontend + Backend)
# Run this from the project root directory with proper credentials
# Prerequisites:
#   - Vercel CLI installed: npm install -g vercel@latest
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
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo -e "${RED}Error: Not in project root directory${NC}"
    echo "Please run this script from the ShikkhaHub project root"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}\n"

# Deploy Frontend
echo -e "${YELLOW}Deploying Frontend...${NC}"
# The frontend project uses rootDirectory: "frontend", so deploy from the repo
# root; Vercel builds ./frontend in the cloud.
if [ ! -f ".vercel/project.json" ]; then
    echo -e "${RED}Error: Frontend not linked to Vercel${NC}"
    echo "Run: vercel link --project shikkhahub-ss"
    exit 1
fi

echo "Deploying to Vercel (cloud build)..."
vercel deploy --prod --yes --token=$VERCEL_TOKEN

echo -e "${GREEN}✓ Frontend deployed: https://shikkhahub-ss.vercel.app${NC}\n"

# Deploy Backend
echo -e "${YELLOW}Deploying Backend...${NC}"
cd backend

if [ ! -f ".vercel/project.json" ]; then
    echo -e "${RED}Error: Backend not linked to Vercel${NC}"
    echo "Run: cd backend && vercel link --project shikkhahub-backend"
    exit 1
fi

echo "Deploying to Vercel (cloud build)..."
vercel deploy --prod --yes --token=$VERCEL_TOKEN

echo -e "${GREEN}✓ Backend deployed: https://shikkhahub-backend.vercel.app${NC}\n"

cd ..

# Verify deployments
echo -e "${YELLOW}Verifying deployments...${NC}\n"

echo "Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://shikkhahub-ss.vercel.app")
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Frontend responding (HTTP ${FRONTEND_STATUS})${NC}"
else
    echo -e "${RED}✗ Frontend not responding (HTTP ${FRONTEND_STATUS})${NC}"
fi

echo "Testing backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://shikkhahub-backend.vercel.app/health")
if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Backend health check passed (HTTP ${BACKEND_STATUS})${NC}"
else
    echo -e "${RED}✗ Backend health check failed (HTTP ${BACKEND_STATUS})${NC}"
fi

echo "Testing search endpoint..."
SEARCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://shikkhahub-backend.vercel.app/api/v1/institutions/search?q=dhaka")
if [ "$SEARCH_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Search endpoint working (HTTP ${SEARCH_STATUS})${NC}"
else
    echo -e "${RED}✗ Search endpoint failed (HTTP ${SEARCH_STATUS})${NC}"
fi

echo -e "\n${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}\n"

echo "Frontend URL: https://shikkhahub-ss.vercel.app"
echo "Backend URL: https://shikkhahub-backend.vercel.app/api/v1"
echo ""
echo "Next steps:"
echo "1. Test the live application"
echo "2. Monitor logs in Vercel dashboard"
echo "3. Configure monitoring (Sentry, analytics)"
