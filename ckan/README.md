# ShikkhaHub CKAN Data Catalog

CKAN acts as the **trusted data catalog and metadata layer** for the national
education platform. Raw scraped data flows through the ETL/validation pipeline
into PostgreSQL, then is published to CKAN as governed, versioned datasets.
ShikkhaHub services (web, mobile, AI, analytics) consume verified datasets from
CKAN's APIs rather than raw scrapers.

## Architecture

```text
Government sources / universities / boards / user contributions
        │  (scrapers + ETL + validation)
        ▼
ShikkhaHub PostgreSQL ──────► CKAN ──────► ShikkhaHub DB / Web / Mobile / AI / Analytics
        │                     │   datasets, metadata, APIs, version history
        └──► ckan/scripts/sync_to_ckan.py
```

## Components

| Component | Technology | Container |
|---|---|---|
| CKAN | 2.10.5 (latest stable) | `ckan` |
| Database | PostgreSQL 14 | `ckan-db` |
| Search | Solr 9 (`ckan/ckan-solr`) | `ckan-solr` |
| Cache | Redis 7 | `ckan-redis` |
| DataPusher | ckan-datapusher | `ckan-datapusher` |
| Storage | Local volume (S3/MinIO in prod) | `storage/` |
| Reverse proxy | Nginx (prod) | — |

### Extensions (all enabled)

- **DataStore** — query structured resource data
- **DataPusher** — auto-import CSV/XLSX into DataStore
- **DCAT** — metadata interoperability (RDF/XML/JSON-LD export)
- **Harvest** — import from external catalogs (RDF/JSON harvesters)
- **Scheming** — custom national metadata schema (8 categories)
- **Spatial** — GIS support (ISO19139 validator)
- **XLoader** — reliable large-file loading

## Quick Start

```bash
cp ckan/.env.example ckan/.env

# Build and start the CKAN stack
docker compose -f ckan/docker-compose.yml up -d --build

# Wait for health, then bootstrap (sysadmin + DataStore + catalog seed)
docker compose -f ckan/docker-compose.yml exec ckan bash /srv/app/scripts/bootstrap.sh

# UI: http://localhost:5000  (login as ckan_admin / changeme123)
```

## Dataset Categories (Scheming)

`ckan/config/scheming/dataset.yaml` defines the metadata standard with the
8 categories from the plan:

1. Institutions
2. Admission
3. Academic Programs
4. Results
5. Rankings
6. Scholarships
7. Job & Career
8. Geographic Data

Every dataset carries the metadata standard (dataset ID, title, description,
organization, owner, contact, license, source URL, source type, last updated,
verification status, tags, language, coverage, update frequency, quality score).

## Organizations & Groups

Seed catalog: `ckan/config/seed_catalog.json` — 11 organizations (Ministry of
Education, UGC, BANBEIS, BTEB, boards, universities) and 11 groups (Higher
Education, School, College, Technical, Medical, Engineering, Scholarships,
Research, Jobs, Admission, Results).

## Backend Integration

FastAPI endpoints under `/api/v1/catalog`:

| Endpoint | Description |
|---|---|
| `GET /catalog/status` | Catalog health & config |
| `GET /catalog/datasets?q=&category=&verification_status=` | Dataset search |
| `GET /catalog/datasets/{name_or_id}` | Dataset detail + resources |
| `GET /catalog/organizations` | Organizations |
| `GET /catalog/groups` | Groups |
| `GET /catalog/dcat/{format}` | DCAT export (rdf/xml/jsonld) |
| `POST /catalog/datasets` | Publish dataset (admin) |
| `PATCH /catalog/datasets/{name}` | Update dataset (admin) |
| `POST /catalog/sync/institutions` | Publish verified institutions (admin) |

Enable via env vars: `CKAN_ENABLED=true`, `CKAN_URL`, `CKAN_API_TOKEN`.

## Data Quality Workflow

Verification status enum on every dataset (scheming + service layer):
`collected → pending_review → verified → published → archived`

Verification checks: duplicate detection, URL validation, metadata
completeness, geographic validation, manual approval, periodic re-verification.

## ETL Sync

```bash
# One-shot: publish verified institutions to CKAN
python ckan/scripts/sync_to_ckan.py \
    --db "postgresql://postgres:postgres@localhost:5432/shikkhahub" \
    --ckan http://localhost:5000 \
    --token <CKAN_API_TOKEN> \
    --limit 1000
```

Idempotent: existing datasets are updated in place.

## AI Integration

CKAN is the trusted metadata layer for the AI assistant:
- institution recommendation / scholarship matching consume verified datasets
- RAG document indexing reads dataset resources + metadata
- semantic search over the catalog via `/catalog/datasets` + DCAT export

## Implementation Phases

1. **Weeks 1–2** — deploy CKAN stack (this directory), configure Solr/Postgres,
   enable auth, create organizations/groups (bootstrap.sh)
2. **Weeks 3–5** — metadata schema (scheming YAML), import institution datasets
3. **Weeks 6–8** — ETL integration, DataStore, expose APIs, connect backend
4. **Weeks 9–10** — DCAT export, analytics dashboards, monitoring, search tuning
