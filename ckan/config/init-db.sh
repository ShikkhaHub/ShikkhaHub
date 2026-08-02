#!/bin/bash
# CKAN database bootstrap — creates the datastore DB and read-only role.
# Runs automatically on first PostgreSQL container start (docker-entrypoint-initdb.d).

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE datastore_default OWNER $POSTGRES_USER;
    CREATE ROLE datastore_ro NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN PASSWORD '${CKAN_DATASTORE_RO_PASSWORD:-ckan_datastore_ro}';
    CREATE ROLE datastore_write NOSUPERUSER NOCREATEDB NOCREATEROLE LOGIN PASSWORD '${CKAN_DATASTORE_WRITE_PASSWORD:-ckan_datastore_write}';
    GRANT CREATE, CONNECT ON DATABASE datastore_default TO datastore_ro;
    GRANT CREATE, CONNECT ON DATABASE datastore_default TO datastore_write;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO datastore_ro;
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO datastore_write;
EOSQL
