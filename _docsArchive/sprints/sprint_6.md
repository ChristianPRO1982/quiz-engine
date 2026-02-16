# Sprint 6 — Quiz Preview & Playtest (Editor-only)

## 1) Sprint Objective

Allow quiz authors to **preview and playtest their quiz locally** from the editor,
without starting a real session and without involving WebSockets or players.

The preview mode must:
- render the quiz exactly as it will appear during gameplay
- allow sequential navigation through questions
- help authors validate content, order, and readability before publishing or playing

This sprint is strictly **editor-side** and introduces no live session logic.

---

## 2) Scope — INCLUDED

### A) Preview entrypoint
- Add a **Preview** button in the quiz editor UI.
- Clicking Preview opens a preview mode:
  - either in-place (editor replaced by preview)
  - or in a dedicated route (recommended): `/admin/quizzes/{quiz_id}/preview`

### B) Preview mode behavior
- Preview mode renders quiz stages sequentially:
  - slide stages
  - other question types rendered in non-interactive mode if present
- Navigation controls:
  - **Next**
  - **Previous**
  - optional **Exit preview** (return to editor)

### C) Rendering rules
- Preview uses the same rendering logic as runtime gameplay:
  - same plugin rendering components
  - same layout constraints (mobile-first)
- Preview does **not**:
  - accept player input
  - compute scores
  - emit PlayerEvents
  - produce StageOutcome

### D) Data source
- Preview must use the **current quiz draft**:
  - if editor has unsaved changes, preview reflects the draft
  - no persistence is triggered by preview
- Preview must never modify quiz data.

### E) Plugin compatibility (minimal)
- SLIDE plugin must be previewable.
- Other plugins, if present:
  - may render a static placeholder view
  - must not block preview flow.

---

## 3) Scope — EXCLUDED

- WebSocket connections
- Session creation / join
- Host vs Player roles
- Scoring, timers, rankings
- Answer submission
- Persistence or autosave

Preview mode is **read-only** and **local**.

---

## 4) UX Requirements

### A) Layout
- Preview must simulate the player view as closely as possible.
- Editor UI (question list, save button, etc.) must be hidden during preview.
- Navigation buttons must be clearly accessible on mobile.

### B) Navigation behavior
- Preview starts at the first stage.
- Navigation rules:
  - Next on last stage does nothing or exits preview.
  - Previous on first stage does nothing.
- Exit preview always returns to the editor in the same state as before.

### C) Unsaved changes
- If the quiz editor is dirty:
  - entering preview is allowed
  - preview reflects unsaved changes
- Exiting preview returns to editor with dirty state unchanged.

---

## 5) Routes

### Jinja pages
- `GET /admin/quizzes/{quiz_id}/preview`
  - authenticated only
  - uses quiz data from editor draft if available

### Editor integration
- Preview button available only when authenticated.
- Preview button disabled if quiz has zero stages (optional but recommended).

---

## 6) Rendering Strategy

### Recommended approach
- Reuse plugin rendering logic with a **PreviewContext**:
  - same payload shape as runtime
  - no lifecycle events (no on_stage_open side effects)
- Preview engine iterates stages sequentially and renders frames synchronously.

### Determinism
- Preview must be deterministic.
- No random_seed is required.
- No plugin state is persisted.

---

## 7) Files to Create / Modify

### Backend
- Create:
  - `quiz_engine/routers/quiz_preview.py`
  - `quiz_engine/services/quiz_preview_service.py`
- Modify:
  - quiz editor router to expose preview link
  - plugin registry to allow preview rendering

### Templates
- Create:
  - `quiz_engine/templates/admin/quiz_preview.html`
- Modify:
  - base layout to support preview mode (hide editor chrome)

### Static JS (minimal)
- Create:
  - `quiz_engine/static/js/quiz_preview.js`
  - handles:
    - current stage index
    - next / previous navigation
    - exit preview

---

## 8) Tests

### Backend tests
- Auth gating:
  - anonymous access to preview route redirects to login
- Preview service:
  - can load quiz data
  - can iterate through all stages without error

### UI tests (manual or automated)
- Preview shows first stage correctly
- Navigation works across all stages
- Exit preview returns to editor
- Unsaved changes are reflected in preview

---

## 9) Definition of Done (DoD)

- [ ] Preview button visible in quiz editor
- [ ] Preview route renders quiz stages sequentially
- [ ] SLIDE plugin renders correctly in preview
- [ ] No WebSocket or session logic involved
- [ ] Preview reflects unsaved draft changes
- [ ] Exit preview returns to editor safely
- [ ] No quiz data is modified or persisted during preview
- [ ] Tests and CI pass

---

## 10) Manual Validation Scenario

1) Login (dev mode acceptable)
2) Open quiz editor with multiple stages (including SLIDE)
3) Make unsaved edits (dirty state)
4) Click Preview
5) Navigate through all stages using Next/Previous
6) Verify content matches editor draft
7) Exit preview
8) Verify editor state and unsaved changes are preserved

---

## 11) Exit Rule

Sprint 6 ends when:
- quiz authors can reliably preview their quiz
- preview matches gameplay rendering visually
- no runtime or session code is involved
- preview flow is stable on mobile and desktop
