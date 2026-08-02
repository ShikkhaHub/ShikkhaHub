# ShikkhaHub Student Data Analytics — Implementation

This document maps the **Student Data Analytics Plan** to the code shipped in
this repository. It covers what was built, the data model, the API surface,
privacy controls, and what remains for Phase 2/3.

---

## 1. What Was Built (Phase 1 MVP)

| Plan Section | Status | Location |
| --- | --- | --- |
| Student Data Model (Student 360 profile) | ✅ | `backend/app/models/student_analytics.py` |
| Event Tracking System (every action → event) | ✅ | `backend/app/services/student_analytics.py::EventTracker` |
| AI Student Profile | ✅ | `StudentProfileService.build_ai_profile` (rule-based) |
| Recommendation Engine | ✅ | `backend/app/services/recommendations.py` |
| Student Segmentation | ✅ | `StudentSegmenter` |
| Learning Analytics | ✅ | `LearningAnalytics` |
| Behavioral Analytics | ✅ | `BehavioralAnalytics` |
| Institutional Analytics Dashboard | ✅ | `backend/app/services/institutional_analytics.py` |
| National Education Insights | ✅ | `NationalInsights` |
| Privacy & Consent Governance | ✅ | `ConsentService` + `ConsentRecord` |
| KPIs | ✅ | Aggregated across the services above |
| Predictive Analytics (ML) | 🚧 Phase 3 | Interfaces designed; replace heuristics |
| Kafka / event queue, DW / ETL | 🚧 Phase 3 | Current MVP writes directly to Postgres |

---

## 2. Data Model

New tables in `backend/app/models/student_analytics.py`:

### `student_profiles` — the Student 360 record
One row per `user`. Maps 1:1 to the plan's Student Data Model:

- **Basic**: full_name, age, gender, date_of_birth, profile_picture_url
- **Academic**: current_level (SSC/HSC/Diploma/University/Masters), education_board,
  current_institution, department, session, expected_graduation, gpa_history (JSON),
  academic_interests (JSON)
- **Geographic**: division, district, upazila, area, current_location
- **Career**: dream_career, interested_sectors, preferred_university, preferred_subject,
  expected_salary, abroad_interest, scholarship_interest, annual_income, disability
- **Learning**: favorite_subjects, weak_subjects, completed_courses,
  study_hours_per_week, learning_style, language_preference, exam_preparation,
  weekly_study_target_minutes
- **AI profile cache**: student_type, strong_subjects, interested_universities,
  risk_score, recommendation_score, ai_profile (JSON), ai_profile_generated_at
- **Consent**: analytics_consent, analytics_consent_at

### `analytics_events` — generic event stream
Every important platform action produces a row. Event types follow the plan:
`search_query`, `institution_view`, `admission_page_view`, `admission_interest`,
`save_institution`, `course_view`, `video_watch`, `pdf_read`, `ai_chat`,
`career_assistant_usage`, `bookmark`, `download`, `share`, `comment`, `review`,
`scholarship_view`, `apply_click`, `course_complete`.

Each event carries optional `institution_id`, `course_id`, `subject`,
`page_path`, `source`, `event_data` (JSON), `duration_seconds`, `session_id`,
and `is_anonymous`.

### `study_sessions` — learning analytics
One row per study/quiz session: subject, session_date, duration_minutes,
lessons_completed, quiz_accuracy, average_score, content_type. Powers daily/
weekly/monthly time, streak, and subject performance.

### `consent_records` — privacy audit trail
Every grant/revoke of consent is logged with type, version, timestamp, and IP.

---

## 3. API Surface

All under `/api/v1`. See `backend/app/api/v1/endpoints/student_analytics.py`.

### Tracking (no auth required; authenticated events are consent-gated)
- `POST /analytics/track/event` — record any platform event
- `POST /analytics/track/study` — record a study session (auth)

### Student profile & 360 (auth)
- `POST /students/profile` — create/update profile
- `GET /students/me/profile` — get profile (auto-creates)
- `GET /students/me` — Student 360: profile + AI profile + segments + learning
- `GET /students/me/ai-profile?refresh=true` — AI student profile
- `GET /students/me/learning?days=30` — learning analytics
- `GET /students/me/segments` — dynamic segments

### Recommendations (auth)
- `GET /students/me/recommendations/institutions` — best / safety / competitive / dream
- `GET /students/me/recommendations/courses`
- `GET /students/me/recommendations/scholarships`
- `GET /students/me/recommendations` — all three

### Consent & privacy (auth)
- `POST /students/consent` — grant/revoke analytics consent
- `GET /students/consent/history` — audit history

### Institutional dashboard & national insights (admin)
- `GET /institutions/{institution_id}/analytics?days=30`
- `GET /admin/analytics/national-insights?days=30`
- `GET /admin/analytics/behavioral?days=30`

---

## 4. How the Pieces Work

### Event tracking & privacy
`EventTracker.track_event` checks the student's `analytics_consent`. If consent
has not been granted, the event is stored with `user_id = NULL` and
`is_anonymous = True` — no identity is retained without explicit consent.
Analytics tracking endpoints swallow exceptions so analytics never break UX.

### AI Student Profile (rule-based)
`StudentProfileService.build_ai_profile` infers, from profile + event history:

- **Student type** — Admission Focused / Career Focused / Active Learner / level-based
- **Learning style** — from profile (defaults to Visual Learner)
- **Strong/weak subjects** — favorites + most-engaged subjects from events
- **Interested universities** — preferred + most-viewed institutions
- **Career goal** — from `dream_career`
- **Risk score** — Low/Medium/High heuristic from engagement + profile completeness
- **Recommendation score** — 0–100 readiness heuristic

The result is cached on `student_profiles.ai_profile` and regenerated on demand
(`?refresh=true`). The function is a single seam that can be swapped for an ML
model in Phase 3 without changing the API contract.

### Recommendations
- **Institutions**: scores each active institution by subject keyword match,
  location match, and popularity; tiers (safety/competitive/dream) come from the
  institution's minimum-GPA requirement vs. the student's SSC/HSC GPA.
- **Courses**: matches courses to academic interests + event-observed subjects.
- **Scholarships**: matches `InstitutionRequirement(requirement_type='scholarship')`
  records by merit GPA, financial need (`annual_income`), and disability.

### Segmentation
`StudentSegmenter.segment` evaluates every definition in `SEGMENT_DEFINITIONS`
(10 groups from the plan) against profile + behavior, returning all matching
groups.

### Institutional dashboard & national insights
All outputs are **anonymous aggregates** — geography comes from student profiles
without exposing identities; event counts are never tied to individual students
in reports.

---

## 5. KPIs

Aggregated across services (all admin endpoints return these):

| KPI | Where |
| --- | --- |
| Registered students | `StudentProfile` count (`national-insights.total_student_profiles`) |
| DAU / MAU | `AnalyticsEvent` distinct users in period |
| Weekly learning hours | `LearningAnalytics` / `BehavioralAnalytics` |
| Search success rate | existing `SearchEvent.click_through_rate` |
| AI recommendation acceptance | `ai_chat` + `career_assistant_usage` counts |
| Institution page → application CTR | `InstitutionAnalytics.interest.admission_ctr` |
| 7/30/90-day retention | extend `BehavioralAnalytics` per period |
| Avg session duration / bounce / return | `BehavioralAnalytics` |

---

## 6. Frontend

- `frontend/src/pages/StudentDashboard.tsx` — student 360 dashboard at `/student`
  (AI profile, learning stats, segments, recommendations, profile editor, consent toggle).
- `frontend/src/api/analytics.ts` — typed API client (`studentAnalyticsApi`).
- Sidebar link "My Analytics" added in `LeftSidebar.tsx`.

---

## 7. Tests

`backend/tests/test_student_analytics.py` — 19 tests covering profile CRUD,
consent lifecycle, anonymous event fallback, AI profile, segmentation, learning
analytics, recommendations, institutional dashboard, national insights, and
behavioral analytics.

```bash
cd backend && pytest tests/test_student_analytics.py -q
```

---

## 8. Phase 2 / Phase 3 Roadmap (not yet built)

- **Phase 2**: predictive churn/inactivity model, career interest evolution,
  institution demand forecasting.
- **Phase 3**: Kafka-based event ingestion, ETL → analytics warehouse, real-time
  dashboards, ML models replacing the rule-based scoring, and authorized data
  APIs for institutional partners.
- Institution roles so non-admin institution staff can view their own dashboard
  (currently admin-only).
- Privacy policy pages in Bangla & English wired to the consent flow.
