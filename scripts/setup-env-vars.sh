#!/bin/bash
# Setup environment variables for Vercel deployment
# Usage: ./scripts/setup-env-vars.sh

set -e

echo "🔧 ShikkhaHub Environment Variables Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to prompt for input
prompt_var() {
    local var_name=$1
    local description=$2
    local default=$3
    
    echo -n "Enter $description"
    if [ ! -z "$default" ]; then
        echo -n " (default: $default)"
    fi
    echo -n ": "
    read value
    
    if [ -z "$value" ] && [ ! -z "$default" ]; then
        value=$default
    fi
    
    echo "$var_name=$value"
}

# Create .env files
echo -e "${BLUE}Creating environment files...${NC}"
echo ""

# Backend environment
echo -e "${YELLOW}Backend Environment Variables${NC}"
cat > backend/.env.production << EOF
# Database
DATABASE_URL=postgresql://user:password@host:5432/shikkhahub

# API Configuration
DEBUG=false
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
API_PORT=8000
API_TIMEOUT=30

# OpenAI API
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Search Configuration
ELASTICSEARCH_URL=https://your-elasticsearch-host:9200
USE_ELASTICSEARCH=false

# Redis (optional)
REDIS_URL=redis://localhost:6379

# JWT Configuration
JWT_SECRET=your-secret-key-change-this-in-production
JWT_EXPIRATION=604800

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
ENVIRONMENT=production

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@shikkhahub.edu.bd

# Admin Credentials
ADMIN_EMAIL=admin@shikkhahub.edu.bd
ADMIN_PASSWORD=change-this-in-production
EOF

# Frontend environment
echo -e "${YELLOW}Frontend Environment Variables${NC}"
cat > frontend/.env.production << EOF
# API Configuration
VITE_API_URL=https://api.yourdomain.com/api/v1

# Analytics
VITE_GOOGLE_ANALYTICS_ID=G-your-id

# Sentry
VITE_SENTRY_DSN=https://your-sentry-dsn

# Feature Flags
VITE_ENABLE_REVIEWS=true
VITE_ENABLE_QA=true
VITE_ENABLE_AI_ASSISTANT=true
VITE_ENABLE_COMMUNITY=true

# Environment
VITE_ENVIRONMENT=production
VITE_APP_VERSION=1.0.0
EOF

echo -e "${GREEN}✓ Environment files created${NC}"
echo ""

# Summary
echo -e "${BLUE}Summary${NC}"
echo "Created:"
echo "  • backend/.env.production"
echo "  • frontend/.env.production"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT:${NC}"
echo "1. Update the .env.production files with actual values"
echo "2. DATABASE_URL: Set your PostgreSQL connection string"
echo "3. OPENAI_API_KEY: Add your OpenAI API key"
echo "4. API URLs: Update to your actual domain"
echo "5. Secrets: Change all passwords and keys"
echo ""
echo "6. Add these to Vercel project settings:"
echo "   • Go to Vercel Dashboard → Project → Settings → Environment Variables"
echo "   • Copy values from .env.production files"
echo "   • Select 'Production' environment"
echo ""
echo -e "${GREEN}✓ Setup complete!${NC}"
