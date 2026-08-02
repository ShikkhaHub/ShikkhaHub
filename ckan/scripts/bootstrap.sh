#!/bin/bash
# ShikkhaHub CKAN bootstrap script.
#
# Runs inside the CKAN container after first boot to:
#   1. Ensure sysadmin user exists
#   2. Initialize DataStore permissions
#   3. Seed organizations, groups and tags
#
#   docker compose -f ckan/docker-compose.yml exec ckan bash /srv/app/scripts/bootstrap.sh

set -euo pipefail

echo "==> Creating sysadmin ${CKAN_SYSADMIN_NAME}..."
ckan -c /srv/app/ckan.ini sysadmin ensure "${CKAN_SYSADMIN_NAME}" || true

echo "==> Initializing DataStore..."
ckan -c /srv/app/ckan.ini datastore set-permissions | \
    PGPASSWORD="${CKAN_DB_PASSWORD:-ckan_default}" \
    psql -h ckan-db -U "${CKAN_DB_USER:-ckan_default}" -d "${CKAN_DB_DATABASE:-ckan_default}" \
    --set ON_ERROR_STOP=1 || echo "  (DataStore permissions may already be applied)"

echo "==> Seeding catalog (organizations / groups)..."
python /srv/app/scripts/seed_catalog.py \
    /srv/app/config/seed_catalog.json \
    --api http://localhost:5000 \
    --token "$(ckan -c /srv/app/ckan.ini user token generate ${CKAN_SYSADMIN_NAME:-ckan_admin} 2>/dev/null | tail -1 | awk '{print $2}')" \
    || true

echo "==> Bootstrap complete."
