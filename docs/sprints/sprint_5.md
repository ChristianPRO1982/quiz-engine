# Sprint 5 — Quiz Editor MVP (Manual Save, Collapse/Expand, Drag & Drop)

## 1) Sprint Objective

Deliver a first usable **Quiz Editor** experience that allows an authenticated user to:
- create a new quiz
- be redirected immediately into **edit mode**
- add questions via a **"+" modal** (question type picker)
- edit exactly one expanded question at a time (others collapsed)
- reorder questions using **drag & drop handle**
- delete questions with confirmation
- save changes manually with a **Save** button

No auto-save is implemented in this sprint.

This sprint aims for a reliable, mobile-first editing workflow without plugin complexity beyond listing question types.

---

## 2) Scope — INCLUDED

### A) Navigation and access rules
- Home page (`/`) is always accessible (anonymous or authenticated).
- Admin/editor routes require authentication:
  - quiz editor navigation is visible only when authenticated
  - anonymous access to admin/editor routes must redirect to `/login`

### B) Create -> Redirect to Edit
- Creating a new quiz redirects directly to the quiz editor page:
  - after `Create quiz`, redirect to `/admin/quizzes/{quiz_id}` (edit mode)

### C) Editor layout and behavior
- The editor displays a list of questions:
  - only **one question expanded** at a time (the "active question")
  - all other questions are collapsed and display:
    - question number
    - truncated title (compact display; ellipsis)
- Clicking a question title (collapsed header) sets it active and expands it.

### D) Add question via "+" modal
- A "+" button opens an overlay modal (sheet/dialog) to choose a question type.
- A single click on a type adds a question:
  - **after the currently selected question**
  - if there is no selected question (e.g., quiz has 0 questions), it creates the first question and selects it
- After adding, the new question becomes the active (expanded) question.

### E) Drag & drop reorder via handle
- Each question header includes a dedicated drag handle icon on the left.
- Dragging is done via the handle (not the title).
- During drag operation:
  - all questions are collapsed
- After drop:
  - the previously active question is expanded again (or the moved question becomes active; implementer may choose, but must be consistent)

### F) Title editing rule (two different titles)
- The header title area is used for:
  - display + expand click
  - drag & drop handle adjacency
- The **editable question title** is a field inside the expanded editor panel.
- The header title reflects the current saved/edited title but is not the editable control.

### G) Delete question with confirmation
- Deleting a question always requires confirmation (modal).
- After deletion:
  - if deleted question was active, select the next logical question:
    - prefer next question
    - else previous question
    - else no selection (empty quiz)

### H) Manual Save (no autosave)
- All modifications are local draft changes until user clicks **Save**.
- Save persists the full quiz state to the backend.

### I) Added minimal editor guardrails (required)
The following three rules are mandatory (simple, essential):

1) **Dirty state indicator**
- Any change sets an editor "dirty" state.
- UI must show a discreet status:
  - `Unsaved` when dirty
  - `Saved` when clean
- Save button is enabled only when dirty.

2) **Leave warning**
- If dirty and user attempts to navigate away/close tab:
  - show a confirmation: `Leave without saving?`
- If not dirty:
  - no warning.

3) **Save behavior contract**
- Save persists the full quiz state (metadata + ordered questions).
- On save success:
  - dirty resets to clean (`Saved`)
- On save failure:
  - remains dirty, show error message, no data loss in UI.

---

## 3) Scope — EXCLUDED

- Auto-save or per-field save
- Multi-device concurrency control
- Undo/redo
- Gameplay sessions and WebSocket runtime
- Advanced plugin-driven schemas or dynamic form generation
- Email, consent UI flows (unless already mandatory before admin access)

---

## 4) Data Model Requirements (Minimal)

### Quiz structure
- Quiz must include:
  - `quiz_id`
  - `title`
  - `description` (optional)
  - `schema_version`
  - `stages` / `questions` list (ordered)
- Each question must include:
  - `question_id` (stable id)
  - `type` (plugin_id; for this sprint, include at least `slide`)
  - `title` (string; editable inside expanded panel)
  - `spec` (plugin_spec JSON-like dict; may be minimal placeholder for most types)

### Ordering
- Ordering is defined by the list order in the quiz payload.
- Reorder operations update the order in the local draft until saved.

---

## 5) UX Requirements (Mobile-First)

- The editor must work on smartphone screens:
  - compact collapsed rows
  - large tap targets for title selection
  - drag handle must be easy to grab
- The "+" modal:
  - full-width or bottom sheet overlay
  - simple list of question types with short labels
- The Save action:
  - always visible (sticky footer or sticky top bar)
  - shows status (`Unsaved` / `Saving...` / `Saved`)

---

## 6) Routes (Jinja pages)

### Required
- `GET /admin/quizzes/{quiz_id}` — quiz editor (authenticated)
- `POST /admin/quizzes` — create quiz (authenticated) -> redirect to editor
- `GET /admin/quizzes` — quiz list (authenticated)

### API (REST)
- `GET /api/quizzes/{quiz_id}` — fetch quiz
- `PUT /api/quizzes/{quiz_id}` (or `PATCH`) — update full quiz payload
  - must validate JSON-only payload rules

---

## 7) Question Types Picker (Plugins)

- The editor must show a list of available question types.
- For Sprint 5, minimum:
  - `slide` must appear and be selectable.
- Additional types may appear as placeholders if available, but must not block editing.

The picker is UI-only; no runtime gameplay is required.

---

## 8) Files to Create / Modify

### Backend
- Create/Modify routers:
  - `quiz_engine/routers/admin_quiz_editor.py` (Jinja editor pages)
  - `quiz_engine/routers/quizzes_api.py` (GET/PUT quiz)
- Services:
  - `quiz_engine/services/quiz_editor_service.py` (load/save quiz payload)
  - `quiz_engine/services/plugin_registry_service.py` (list question types for picker)
- Schemas:
  - `quiz_engine/schemas/quiz_editor_schemas.py` (editor payload validation)
- Repository:
  - `quiz_engine/repositories/quiz_repository.py` (persist full payload)

### Templates
- Create/Modify:
  - `quiz_engine/templates/admin/quizzes_editor.html`
  - `quiz_engine/templates/admin/quizzes_list.html` (CTA "New quiz")
  - `quiz_engine/templates/partials/question_type_picker_modal.html`

### Static JS (vanilla)
- Create:
  - `quiz_engine/static/js/quiz_editor.js`
  - Must handle:
    - local draft state
    - collapse/expand selection
    - add question after selected
    - drag & drop reorder via handle
    - delete confirmation
    - dirty state + leave warning
    - save call

### CSS (if needed)
- Minimal additions only; respect existing design tokens if present.

---

## 9) Tests

### Backend tests
- Auth gating:
  - anonymous cannot access editor routes (redirect to login)
- API:
  - GET quiz returns expected payload
  - PUT quiz updates payload, preserves ordering

### UI behavior tests (lightweight)
- Draft dirty state changes after edit
- Save resets dirty state
- Delete confirmation required

If browser-based UI tests are not present in the repo:
- implement deterministic unit tests for JS state logic (if feasible)
- otherwise, document a manual validation checklist

---

## 10) Definition of Done (DoD)

### Editor flow
- [ ] Create quiz redirects directly to editor
- [ ] Editor shows list of questions with 1 expanded at a time
- [ ] Clicking title expands and collapses others
- [ ] "+" modal adds question after selected (or creates first if empty)
- [ ] Drag handle reorders questions; during drag all collapsed; after drop active expands
- [ ] Delete requires confirmation; selection updates logically

### Save & safety
- [ ] Dirty indicator (`Unsaved`/`Saved`) works
- [ ] Leave warning when dirty works
- [ ] Save persists full quiz and clears dirty state
- [ ] Save failure keeps draft and displays error

### Access rules
- [ ] Admin/editor navigation visible only when authenticated
- [ ] Home page accessible for everyone

---

## 11) Manual Validation Scenario

1) Login (dev mode is acceptable)
2) Go to quizzes list, click "New quiz"
3) Confirm redirect to editor
4) Add first question via "+" modal -> becomes expanded
5) Add second question after selected
6) Collapse/expand by clicking titles
7) Reorder using drag handle
8) Edit title inside expanded panel; verify dirty indicator shows Unsaved
9) Try to close tab; confirm leave warning
10) Click Save; indicator becomes Saved
11) Delete a question; confirm modal required; selection updates
12) Save again; list page shows updated quiz title

---

## 12) Exit Rule

Sprint 5 ends when:
- quiz editor MVP is usable end-to-end
- manual save + safety rules are implemented
- question list UX (collapse/expand + DnD) is stable on mobile
- authenticated gating rules are enforced
- tests/CI are green
