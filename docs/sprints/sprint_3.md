# Sprint 3 — Admin Navigation + Quiz Creation Flow (Mobile-First)

## 1) Sprint Objective

Provide a clean, mobile-first **admin navigation** and a complete, guided flow to create a new quiz.

This sprint focuses on UX structure (navigation + layout) and a reliable quiz authoring entrypoint,
building directly on Sprint 2 auth + minimal quiz persistence.

Primary outcome:
- An authenticated user can discover the quiz section easily and create a quiz via a consistent admin UI.

---

## 2) Scope — INCLUDED

### A) Global Navigation (authenticated)
- Add an **admin navigation bar** available to authenticated users:
  - visible on all pages (via `base.html`)
  - mobile-first (compact)
  - includes links:
    - **Quizzes** (list)
    - **New quiz** (create)
    - (optional placeholder) **Sessions** (disabled/coming soon)
- Navigation must coexist with the **top-right auth widget** (Connect/Account/Logout).

### B) Admin Landing Page
- Add `/admin` route:
  - shows simple dashboard tiles/links:
    - "My quizzes"
    - "Create a new quiz"

### C) Quiz Creation UX (guided)
- `/admin/quizzes/new` becomes a guided authoring page:
  - Step 1: quiz metadata (title, description)
  - Step 2: add questions (MVP: `qcm_single`)
  - Step 3: review and save
- The flow must be resilient to refresh/back:
  - use server-side draft (session) OR a simple draft table (see option below)

Draft persistence options (choose one):
- **Option 1 (recommended): session draft**
  - store draft in session cookie server-side
  - simplest, no DB migration
- **Option 2: DB draft**
  - add `qe_quiz_draft` table
  - allows multi-device continuity

Codex must implement **Option 1 by default**, unless `qe_quiz_draft` already exists.

### D) Quiz List Improvements
- `/admin/quizzes` list page improvements:
  - "Create new quiz" CTA button
  - consistent empty state if no quizzes exist
  - each quiz row links to detail

### E) Quiz Detail Page Improvements
- `/admin/quizzes/{quiz_id}`:
  - display quiz metadata + questions formatted nicely
  - "Duplicate" button (optional: copies payload into draft and redirects to new)

### F) REST API alignment
- Keep Sprint 2 endpoints.
- Add optional draft endpoints if useful (only if Option 2 is chosen).

### G) Tests
- UI routing tests (template responses)
- Draft flow tests (session-based draft)
- Create quiz end-to-end (auth required)

---

## 3) Scope — EXCLUDED

- Gameplay sessions runtime
- WebSocket gameplay events
- Scoring, timers, leaderboards
- Plugin execution engine
- Full hub/OIDC integration (still placeholder acceptable)
- Emails
- Consentements UX (unless already present and required to access admin)

---

## 4) UX Requirements (Non-Functional)

- Mobile-first layout:
  - large tap targets
  - minimal text
  - clear hierarchy
- Admin navigation must be:
  - consistent across pages
  - accessible
  - not visually dominant
- Auth widget remains:
  - fixed top-right
  - discreet

---

## 5) Routes (Jinja pages)

- `GET /admin`
- `GET /admin/quizzes`
- `GET /admin/quizzes/new`
- `POST /admin/quizzes/new` (or step endpoints)
- `GET /admin/quizzes/{quiz_id}`

Draft steps (if multi-step routes are preferred):
- `GET /admin/quizzes/new/step-1`
- `POST /admin/quizzes/new/step-1`
- `GET /admin/quizzes/new/step-2`
- `POST /admin/quizzes/new/step-2`
- `GET /admin/quizzes/new/review`
- `POST /admin/quizzes/new/save`

Codex should choose either:
- single URL with internal step parameter, or
- multiple step URLs (recommended for clarity).

---

## 6) Data Contracts

### Quiz payload (unchanged)
- Must continue storing quiz definition as opaque JSON:
  - `schema_version`
  - `title`
  - `description`
  - `questions[]`

Supported question type (Sprint 3):
- `qcm_single` only

### Draft payload (session)
Draft stored in session must include:
- `schema_version`
- `title`
- `description`
- `questions[]`
- `updated_at` (string or timestamp)

---

## 7) Files to Create / Modify

### Templates
- Modify:
  - `quiz_engine/templates/base.html`
    - include admin navigation when authenticated
- Create:
  - `quiz_engine/templates/partials/admin_nav.html`
  - `quiz_engine/templates/admin/index.html`
  - `quiz_engine/templates/admin/quizzes_new_step1.html`
  - `quiz_engine/templates/admin/quizzes_new_step2.html`
  - `quiz_engine/templates/admin/quizzes_new_review.html`
  - (or a single-page alternative if Codex chooses)

### Backend
- Create:
  - `quiz_engine/routers/admin.py` (Jinja admin routes)
  - `quiz_engine/services/quiz_draft_service.py`
- Modify:
  - existing `quiz_engine/app.py` to include `admin_router`
  - existing quiz service if needed (create from draft payload)

### Tests
- Create/Modify:
  - `tests/test_admin_navigation.py`
  - `tests/test_quiz_draft_flow.py`

---

## 8) Definition of Done (DoD)

### Navigation
- [ ] Authenticated users see admin nav on all pages
- [ ] Admin nav includes:
  - Quizzes list
  - New quiz
- [ ] `/admin` landing page exists and links correctly
- [ ] Works on mobile viewport without overlap with auth widget

### Quiz creation flow
- [ ] `/admin/quizzes/new` is discoverable from nav + list CTA
- [ ] Multi-step flow works:
  - metadata
  - questions
  - review
  - save
- [ ] Draft is preserved across steps (session-based)
- [ ] Saving creates a persisted quiz in Postgres
- [ ] After save, redirect to quiz detail

### Tests & CI
- [ ] Tests cover admin routing + draft flow + auth gating
- [ ] CI green (lint + tests)

---

## 9) Manual Validation Scenario

1) Start with `AUTH_MODE=dev`
2) Login as `user1`
3) See admin nav (Quizzes / New quiz)
4) Click Quizzes → list page, click Create new quiz
5) Step 1: enter title/description
6) Step 2: add 2 questions with choices
7) Review: see formatted quiz preview
8) Save → redirected to detail page
9) Go back to Quizzes list → new quiz appears

---

## 10) Exit Rule

Sprint 3 ends when:
- admin navigation is in place and stable
- creating a new quiz is a guided, reliable flow
- the quiz is persisted and visible in list/detail
- tests and CI pass

## Navigation Rules

### NAV-001 — Auth-gated quiz creation
- Quiz creation pages are accessible only to authenticated users.
- Anonymous access must redirect to `/login`.

### NAV-002 — Public home page
- Home page (`/`) is always accessible.
- UI adapts based on authentication state.

### NAV-003 — Auth-aware navigation visibility
- Admin navigation links (Quizzes, New quiz) are visible only to authenticated users.
- Anonymous users never see admin links.
