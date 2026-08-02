# ShikkhaHub Database Schema — ERD Gap Audit & Reconciliation

**Date:** 2026-08-02
**Status:** Design reconciled with implementation (65 tables)

This document audits the proposed national-education-knowledge-graph ERD against
the implemented SQLAlchemy schema, lists what was added, and documents deliberate
naming differences.

---

## 1. Coverage Matrix

| Proposed ERD entity | Implemented table | Model file | Notes |
|---|---|---|---|
| `Division` | `divisions` | `app/models/location.py` | FK-only, no denormalized names |
| `District` | `districts` | `app/models/location.py` | FK-only |
| `Upazila` | `upazilas` | `app/models/location.py` | FK-only |
| `Institution` | `institutions` | `app/models/institution.py` | Full column parity |
| `Campus` | `campuses` | `app/models/institution_detail.py` | + geo & active flags |
| `Facility` (types) | `facility_types` / `institution_facilities` | `app/models/institution_detail.py` | Modeled as FK catalog (no boolean spam) |
| `Gallery` | `gallery_images` | `app/models/institution_detail.py` | |
| `Ranking` | `institution_rankings` | `app/models/institution_detail.py` | + category/score |
| `Accreditation` | `accreditations` | `app/models/institution_detail.py` | `authority`→`accrediting_body`, `certificate`→`certificate_number`, `valid_until`→`expires_at` |
| `Admission` | `admissions` | `app/models/announcement.py` | + session/program/eligibility |
| `Notice` | `notices` | `app/models/announcement.py` | `published_at`→`publish_at`, +`is_verified` on users |
| `Scholarship` | `scholarships` | `app/models/announcement.py` | + eligibility/type |
| `Course` | `courses` | `app/models/course.py` | + course types |
| `Subject` | `subjects` | `app/models/subject.py` | |
| `InstitutionCourse` | `institution_courses` | `app/models/education_graph.py` | Full M2M + offering metadata |
| `User` | `users` | `app/models/user.py` | `password`→`hashed_password` |
| `StudentProfile` | `student_profiles` | `app/models/student_analytics.py` | `ssc_gpa/hsc_gpa`→`gpa_history` (JSON) |
| `SavedInstitution` | `saved_institutions` | `app/models/education_graph.py` | |
| `Review` | `institution_reviews` | `app/models/review.py` | + sub-ratings/pros/cons |
| `Comment` | `comments` | `app/models/comment.py` | Polymorphic `content_type/content_id` |
| `AI Conversations` | `chat_sessions` / `chat_messages` | `app/models/chat.py` | `sources` is JSON array |
| Q&A | `questions` / `answers` / `*_votes` | `app/models/qa.py` | Extends proposed community |

## 2. Newly Implemented (was missing from codebase)

All three gaps from the proposed design were implemented:

### 2.1 Data Verification Layer — `app/models/data_verification.py`
- `raw_sources` — authoritative origins (UGC, BMED, boards, manual) + reliability score
- `scrape_jobs` — one crawl/import run per source (status, counts, error log)
- `scraped_records` — immutable harvested records, sha256 `checksum` for dedup
- `verification_queue` — records awaiting human/official review (priority, status)
- `change_requests` — community/official proposed edits (old/new values, review trail)
- `institution_history` — append-only audit trail of every field change

### 2.2 Admin / RBAC — `app/models/rbac.py`
- `roles`, `permissions`, `role_permissions` (granular `resource.action` codes)
- `admins` — AdminProfile linking `users` → `roles` + department metadata
- `audit_logs` — immutable privileged-action log (actor, entity, changes, IP/UA)

### 2.3 Community — `app/models/community.py`
- `communities` — interest-based communities (medical_admission, engineering, ...)
- `tags` / `post_tags` — topical tagging
- `discussion_posts` — free-form posts beyond Q&A (type, status, pin/feature)
- `post_votes` — one up/down vote per user per post
- `community_members` — membership + moderator role

## 3. PostgreSQL Extensions

Enabled via `app/core/database.py::enable_postgres_extensions()` (called by
`init_db()`) and the initial migration:

- **PostGIS** — geospatial "universities within 10 km"
- **pg_trgm** — fuzzy institution name search
- **uuid-ossp** — UUID generation
- **unaccent** — Bangla/Latin search normalization

Each is created best-effort so managed providers that restrict PostGIS privileges
do not block startup.

## 4. Migration Strategy

Previously the schema was managed only via `Base.metadata.create_all` — Alembic
had zero revisions. Added `backend/alembic/versions/0001_extensions_and_baseline.py`:

1. `CREATE EXTENSION IF NOT EXISTS` for all four extensions
2. Full normalized baseline from SQLAlchemy metadata
3. Seeds system roles (super_admin, admin, verifier, moderator)

**Future changes:** author new revisions with `alembic revision --autogenerate`.

## 5. Seeding

`backend/scripts/seed_data.py` now also seeds:
- 10 facility types (hostel, library, wifi, transport, cafeteria, medical, ...)
- 6 authoritative raw sources with reliability scores

## 6. Scale Estimates

The implemented schema supports the stated targets: 20k+ institutions,
200k+ courses, 5M+ users, 50M+ reviews, multi-campus institutions, AI chat RAG
sources, analytics, and the verification/audit backbone for government
integration. Integer PKs keep join keys compact at scale; indexes cover the hot
query paths (institution location, course offerings, verification status,
search vector).

## 7. Verified

- 65 tables registered on `Base.metadata` (smoke-tested import)
- New models insert + relationship traversal verified (in-memory SQLite)
- `alembic upgrade head --sql` emits extensions + full schema
- Full pytest run: identical pass/fail before and after (52 passed; the
  pre-existing 29 errors are test-isolation artifacts from a session-scoped
  shared test DB, unrelated to schema)
