# National Education Knowledge Graph

ShikkhaHub's data model is designed as a **national education knowledge graph**
with a normalized relational core. Instead of denormalized monolithic tables,
entities are modeled as nodes (institutions, campuses, courses, subjects,
facilities, accreditations, scholarships, ...) connected through typed
relationships (course offerings, facility availability, board/UGC affiliations,
user saves, ...).

## Design principles

- **One canonical identity per entity.** `institutions`, `courses`, `subjects`,
  `divisions`, `districts`, `upazilas` each have a stable primary key and unique
  slug/code.
- **Many-to-many relationships carry metadata.** `institution_courses` is the
  join between the national course catalog and institutions, carrying
  offering-specific data (seats, shift, fee, language, status). `affiliations`,
  `institution_boards` and `institution_ugc` model authority relationships.
- **Administrative geography is a tree.** `divisions -> districts -> upazilas`;
  institutions denormalize `division_id`/`district_id` for fast national-level
  filtering while keeping `upazila_id` as the source of truth.
- **Everything points to institutions.** Campuses, facilities, gallery images,
  rankings, accreditations, admissions, notices, scholarships all reference
  `institutions.id`, forming the graph's edges.
- **Verification is first-class.** `verification_status`, `verification_level`,
  `status` and `eiin`/`board`/`ugc_approved` national identifiers support a
  trust pipeline and data-quality reporting.

## Core node tables

| Table | Purpose | Notable columns |
|---|---|---|
| `institutions` | Canonical institution node | `slug`, `name_en`, `name_bn`, `type_id`, `ownership`, `education_level`, `division_id`, `district_id`, `upazila_id`, `eiin`, `board`, `university_affiliation`, `ugc_approved`, `verification_status`, `verification_level`, `status`, `facebook`, `logo`, `banner` |
| `institution_types` | Institution taxonomy | `name`, `category`, `display_order` |
| `campuses` | Physical campuses of an institution | `institution_id`, `campus_type`, location FKs, `area_sqft` |
| `courses` | National course catalog (standalone) | `name_en`, `name_bn`, `code`, `slug`, `course_type_id`, `duration_years`, `total_credits`, `semester_system` |
| `course_types` | Course taxonomy (HSC, BSc, ...) | `name`, `category`, `duration_months`, `level` |
| `subjects` | Standalone subject catalog | `name_en`, `name_bn`, `code`, `category`, `credits`, `prerequisite_id` |
| `facility_types` | Facility catalog (library, lab, hostel, ...) | `name`, `icon` |
| `divisions` / `districts` / `upazilas` | National administrative geography | `name_en`, `name_bn`, `code` |

## Relationship (edge) tables

| Table | Connects | Metadata carried |
|---|---|---|
| `institution_courses` | institutions ⟷ courses | `total_seats`, `reserved_seats`, `shift`, `fee`, `fee_currency`, `language`, `intake_year`, `duration_years`, `status` |
| `institution_facilities` | institutions ⟷ facility_types | `is_available`, `capacity`, `notes` |
| `institution_boards` | institutions ⟷ education_boards | — |
| `institution_ugc` | institutions ⟷ university_grant_commissions | — |
| `affiliations` | institution ⟷ institution (parent/member) | `affiliation_type` |
| `saved_institutions` | users ⟷ institutions | `note` |

## Institution detail & announcement tables

| Table | Purpose |
|---|---|
| `gallery_images` | Photos (`url`, `thumbnail_url`, `caption`, `category`, `sort_order`) |
| `institution_rankings` | Ranks within a `ranking_type`/`category`/`year` |
| `accreditations` | Certifications from `accrediting_body` with validity window |
| `admissions` | Admission cycles (`session`, `application_start/end`, `exam_date`, `minimum_gpa`, `total_seats`, `application_fee`, `status`) |
| `notices` | Notices (`category`, `publish_at`, `expire_at`, `is_important`) |
| `scholarships` | Financial aid (`scholarship_type`, `amount`, `currency`, `application_deadline`) |

## Taxonomy values

`app/models/institution.py` exports the canonical vocabularies:

- `INSTITUTION_OWNERSHIPS`: `government`, `private`, `trust`, `autonomous`
- `INSTITUTION_EDUCATION_LEVELS`: `primary`, `secondary`, `higher_secondary`,
  `diploma`, `degree`, `postgraduate`
- `INSTITUTION_STATUSES`: `active`, `inactive`, `suspended`, `merged`
- `VERIFICATION_LEVELS`: `0` unverified, `1` basic, `2` enhanced, `3` fully verified

A public metadata endpoint exposes these:

```
GET /api/v1/meta/institution-types
```

## API surface

All endpoints live under `app/api/v1/endpoints/education.py` (router mounted at
`/api/v1` with no extra prefix). Reads are public; writes require admin; saved
institutions require an authenticated user.

### Campuses
- `GET /api/v1/institutions/{id}/campuses`
- `GET /api/v1/campuses/{id}`
- `POST /api/v1/campuses`, `PUT /api/v1/campuses/{id}`, `DELETE /api/v1/campuses/{id}`

### Facilities
- `GET /api/v1/facilities/types`
- `GET /api/v1/institutions/{id}/facilities`
- `POST /api/v1/institutions/{id}/facilities`
- `DELETE /api/v1/institutions/{id}/facilities/{facility_id}`

### Gallery
- `GET /api/v1/institutions/{id}/gallery`
- `POST /api/v1/institutions/{id}/gallery`
- `DELETE /api/v1/gallery/{image_id}`

### Rankings & accreditations
- `GET /api/v1/institutions/{id}/rankings`
- `POST /api/v1/institutions/{id}/rankings`
- `DELETE /api/v1/rankings/{ranking_id}`
- `GET /api/v1/institutions/{id}/accreditations`
- `POST /api/v1/institutions/{id}/accreditations`
- `DELETE /api/v1/accreditations/{accreditation_id}`

### Announcements
- `GET /api/v1/institutions/{id}/admissions` (optional `?status=`)
- `GET /api/v1/admissions/{id}`, `POST /api/v1/admissions`, `PUT/DELETE /api/v1/admissions/{id}`
- `GET /api/v1/institutions/{id}/notices`, `POST /api/v1/notices`, `PUT/DELETE /api/v1/notices/{id}`
- `GET /api/v1/institutions/{id}/scholarships`, `POST /api/v1/scholarships`, `PUT/DELETE /api/v1/scholarships/{id}`

### Course offerings
- `GET /api/v1/institutions/{id}/courses`
- `POST /api/v1/institutions/{id}/courses`
- `PUT /api/v1/institution-courses/{offering_id}`
- `DELETE /api/v1/institution-courses/{offering_id}`

### Saved institutions (auth required)
- `GET /api/v1/me/saved`
- `GET /api/v1/me/saved/{institution_id}`
- `POST /api/v1/me/saved/{institution_id}` (body: `{"note": "..."}`)
- `DELETE /api/v1/me/saved/{institution_id}`

### Metadata
- `GET /api/v1/meta/institution-types`

## Implementation notes

- New models live in `app/models/institution_detail.py`, `app/models/announcement.py`
  and `app/models/education_graph.py`; all are registered in `app/models/__init__.py`
  so `Base.metadata.create_all` covers them.
- `Course.institution_id` and `Subject.course_id` are now **nullable** to allow a
  standalone national catalog; per-institution offerings are expressed through
  `institution_courses`.
- Tests: `tests/test_education_graph.py` (14 tests covering every table and
  endpoint plus admin/role gating).

## Recommended PostgreSQL additions (production)

The schema was designed to take advantage of PostgreSQL extensions when deployed:

- `PostGIS` (`postgis` extension) for geospatial queries on `institutions.latitude/longitude`
  and `campuses` — enable when serving proximity search at national scale.
- `pg_trgm` for fuzzy/prefix matching on `institutions.name_en/name_bn` and `courses`.
- Built-in `uuid` + `pgcrypto` for distributed, collision-free IDs.
- `unaccent` for accent-insensitive Bangla/Latin search normalization.
- `tsvector` full-text columns (`institutions.search_vector` already reserved).

Estimated scale targets: 20k+ institutions, 200k+ courses, 5M+ users,
50M+ reviews. All join tables carry indexes and unique constraints tuned for
these volumes.
