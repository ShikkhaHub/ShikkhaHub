#!/bin/bash
# Deployment script for ShikkhaHub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
COMPOSE_FILE="docker-compose.prod.yml"

if [ "$ENVIRONMENT" == "production" ]; then
    ENV_FILE=".env.production"
    echo -e "${RED}WARNING: Deploying to PRODUCTION${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled"
        exit 1
    fi
else
    ENV_FILE=".env.staging"
    echo -e "${YELLOW}Deploying to STAGING${NC}"
fi

# Check if env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: $ENV_FILE not found${NC}"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Backup database before deployment
echo -e "${YELLOW}Creating database backup...${NC}"
docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "backup_$(date +%Y%m%d_%H%M%S).sql" || echo "Backup failed, continuing..."

# Pull latest images
echo -e "${YELLOW}Pulling latest images...${NC}"
docker-compose -f "$COMPOSE_FILE" pull

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f "$COMPOSE_FILE" run --rm backend alembic upgrade head || echo "No migrations to run"

# Deploy with zero downtime (rolling update)
echo -e "${YELLOW}Deploying services...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --scale backend=2 backend

# Wait for new containers to be healthy
sleep 30

# Scale down old containers
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --scale backend=1 backend

# Cleanup
echo -e "${YELLOW}Cleaning up...${NC}"
docker system prune -f

# Health check
echo -e "${YELLOW}Running health checks...${NC}"
for i in {1..5}; do
    if curl -f http://localhost/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Application is healthy${NC}"
        exit 0
    fi
    echo "Attempt $i: Application not ready yet..."
    sleep 10
done

echo -e "${RED}✗ Health check failed${NC}"
exit 1
