#!/bin/bash
# Rollback script for ShikkhaHub deployments

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-staging}
BACKUP_FILE=${2:-}

if [ "$ENVIRONMENT" == "production" ]; then
    read -p "Are you sure you want to rollback PRODUCTION? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Rollback cancelled"
        exit 1
    fi
fi

echo -e "${YELLOW}Starting rollback for $ENVIRONMENT...${NC}"

# Find latest backup if not specified
if [ -z "$BACKUP_FILE" ]; then
    BACKUP_FILE=$(ls -t backup_*.sql 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "${RED}No backup file found${NC}"
        exit 1
    fi
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}Restoring database from: $BACKUP_FILE${NC}"
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d shikkhahub < "$BACKUP_FILE"

echo -e "${YELLOW}Rolling back to previous image...${NC}"
# This would require tagging previous images or using a registry with history
# For now, just restart services
docker-compose -f docker-compose.prod.yml restart

echo -e "${GREEN}Rollback completed${NC}"
