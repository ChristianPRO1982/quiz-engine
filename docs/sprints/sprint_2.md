# Sprint 2 — Auth & Minimal Quiz Builder (MVP)

## 1) Sprint Objective

Deliver the first usable authenticated UX for quiz-engine:

- A discrete, fixed **top-right auth widget** on every page:
  - **Connect**
  - **Account**
  - **Logout**
- **DEV mode** login flow:
  - Clicking **Connect** allows selecting `user1` or `user2`
- Minimal **quiz builder** allowing an authenticated user to:
  - create a quiz
  - list their quizzes
  - open quiz details (read-only)

This sprint establishes the entrypoint flows for future gameplay (sessions) but does not implement gameplay.

---

## 2) Scope — INCLUDED

### A) Authentication UX (Jinja)
- Global header widget included in the base layout:
  - fixed position, top-right, discreet
  - shows **Connect** when anonymous
  - shows **Account** and **Logout** when authenticated
- Pages:
  - `/login`
  - `/account`

### B) DEV auth mode
- DEV mode must allow selecting one of:
  - `user1`
  - `user2`
- The selected dev user becomes the authenticated user context.
- DEV mode should be enabled via configuration (consistent with Sprint 1 rules).

### C) Auth persistence
- Authentication state must persist across requests using a server-side session cookie.
- Logout must remove the session state.

### D) Quiz CRUD (minimal)
- Authenticated user can create a quiz.
- Authenticated user can list their quizzes.
- Authenticated user can view quiz details.
- Quiz storage:
  - use PostgreSQL
  - store quiz definition in `qe_quiz` as opaque JSON
  - store `schema_version` for quiz payload compatibility

### E) REST endpoints
- `POST /api/quizzes` (create)
- `GET /api/quizzes` (list)
- `GET /api/quizzes/{quiz_id}` (detail)

### F) Basic templates (mobile-first)
- `/admin/quizzes` list page
- `/admin/quizzes/new` create page
- `/admin/quizzes/{quiz_id}` detail page

### G) Tests (minimum viable)
- auth dev login/logout flow
- quiz create/list/detail with auth gating

---

## 3) Scope — EXCLUDED

- Session gameplay (host start, questions, WebSocket runtime)
- Scoring, timers, leaderboards
- Plugins execution and stage outcomes logic
- Consentements UI/logic (handled in Sprint 1+/later if not already implemented)
- Email sending
- Full hub/OIDC integration (only placeholder wiring allowed)

---

## 4) Runtime & Data Contracts

### A) Auth user context (internal contract)
Authenticated user context must provide at least:
- `subject` (stable identifier; for hub it will be OIDC `sub`)
- `display_name`
- optional `email`
- `auth_mode` (e.g., `dev` / `hub`)

### B) Quiz schema (MVP payload)
All quiz payloads stored in DB must include:
- `schema_version` (string, required)
- `title` (string, required)
- optional `description` (string)
- `questions` (list)

Question type supported in Sprint 2:
- `qcm_single` (single choice)

Example payload:
```json
{
  "schema_version": "v1",
  "title": "Sample Quiz",
  "description": "My first quiz",
  "questions": [
    {
      "type": "qcm_single",
      "text": "Question text",
      "choices": ["A", "B", "C"]
    }
  ]
}
```

---

## 5) Configuration Requirements

### Required env vars

* `DATABASE_URL` (Postgres)
* `AUTH_MODE`:

  * `dev` enables dev user selection
  * any other value keeps hub mode placeholder
* `SESSION_SECRET_KEY` (must be set outside dev)

### DEV mode behavior

* Clicking Connect leads to `/login` where the user selects `user1` or `user2`.
* The selected user must map to a deterministic `subject`:

  * `dev-user1`
  * `dev-user2`

---

## 6) Files to Create / Modify

### Backend

* Create:

  * `quiz_engine/routers/auth.py`
  * `quiz_engine/routers/quizzes.py`
  * `quiz_engine/services/auth_service.py` (dev user resolution)
  * `quiz_engine/services/quiz_service.py`
  * `quiz_engine/repositories/quiz_repository.py`
  * `quiz_engine/schemas/quiz_schemas.py` (Pydantic request/response models)
* Modify:

  * `quiz_engine/app.py` (register middleware + routers)
  * existing settings module (wire `AUTH_MODE`, `SESSION_SECRET_KEY`, `DATABASE_URL`)
  * DB models for `qe_quiz` if not already present

### Templates

* Create:

  * `quiz_engine/templates/partials/auth_widget.html`
  * `quiz_engine/templates/auth/login.html`
  * `quiz_engine/templates/auth/account.html`
  * `quiz_engine/templates/admin/quizzes_list.html`
  * `quiz_engine/templates/admin/quizzes_new.html`
  * `quiz_engine/templates/admin/quizzes_detail.html`
* Modify:

  * `quiz_engine/templates/base.html` (include auth widget)

### Migrations

* If `qe_quiz` is not present yet:

  * add Alembic migration (qe-only rules apply)

---

## 7) Security & Guardrails

* All `/admin/*` pages must require authentication.
* All `/api/quizzes*` endpoints must require authentication.
* In shared DB context:

  * only `qe_*` tables may be created/modified
  * no foreign keys to non-`qe_*` tables

---

## 8) Definition of Done (DoD)

### Auth

* [ ] Auth widget appears on all pages, fixed top-right, discreet
* [ ] Anonymous sees **Connect**
* [ ] Authenticated sees **Account** + **Logout**
* [ ] DEV mode Connect → can select `user1` or `user2`
* [ ] Logout clears session and returns to anonymous state

### Quiz builder

* [ ] Authenticated user can create a quiz via `/admin/quizzes/new`
* [ ] Quiz is persisted in Postgres (`qe_quiz`)
* [ ] Authenticated user can list quizzes via `/admin/quizzes`
* [ ] Authenticated user can open quiz detail via `/admin/quizzes/{id}`
* [ ] REST endpoints `POST/GET` work with validation and correct HTTP codes

### Tests & CI

* [ ] Tests cover: dev login/logout + quiz create/list/detail
* [ ] CI passes lint + tests
* [ ] No migration touches non-`qe_*` tables

---

## 9) Validation Scenario (Manual)

1. Start the service with `AUTH_MODE=dev`
2. Open home page
3. Top-right shows **Connect**
4. Click **Connect** → pick `user1` → confirm logged in
5. Click **Account** → see subject `dev-user1`
6. Go to `/admin/quizzes/new` → create quiz (1 question, 3 choices)
7. Go to `/admin/quizzes` → quiz appears
8. Open quiz detail → payload rendered
9. Click **Logout** → widget returns to **Connect**

---

## 10) Exit Rule

Sprint 2 ends when:

* Auth widget + dev login selection works end-to-end
* Quiz creation + listing + detail works end-to-end
* Data persists correctly in Postgres
* Tests + CI are green
