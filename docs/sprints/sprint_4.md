Parfait 👍
Voici **le fichier `sprint_4.md` prêt à être donné tel quel à Codex dans VSCode**, construit **strictement à partir de vos documents de travail** (plugin lifecycle, schemas v0, WS messages, determinism, packaging).
Aucun code, uniquement du cadrage normatif et exécutable pour Codex.

---

````markdown
# Sprint 4 — First Plugin: SLIDE (Zero-Logic, Zero-Score)

## 1) Sprint Objective

Implement the **first quiz-engine plugin**: **SLIDE**.

The SLIDE plugin is intentionally simple and non-interactive:
- no player input
- no scoring
- no randomness
- no host action required

Its purpose is to:
- validate the **plugin architecture end-to-end**
- validate **plugin lifecycle integration** with the engine
- serve as a pedagogical and technical reference for future plugins

This sprint has **no gameplay stake** and must favor clarity, determinism, and simplicity.

---

## 2) Plugin Definition — SLIDE

### Functional intent
- Display a static slide (text / markdown / image reference)
- Visible to all players and the host
- Automatically completes when the host advances the quiz

### Non-goals
- No interaction
- No timing logic
- No animation logic
- No score or grade
- No persistence beyond standard StageTrace / StageOutcome

---

## 3) Scope — INCLUDED

### A) Plugin packaging
- Create a standalone plugin package:
  - plugin_id: `slide`
  - schema_version: `v0`
- Provide a valid plugin manifest
- Plugin must be loadable by explicit registration in the engine

### B) Plugin lifecycle (V0)
The SLIDE plugin must correctly implement:

- `create_runtime(session_id, stage_definition)`
- `on_stage_open(stage_context)`
- `is_finished(trace)`
- `build_outcome(trace)`

No other lifecycle hooks are required.

### C) Rendering behavior
- On stage open, the plugin emits **one PluginFrame**:
  - audience: `ALL`
  - frame_type: `VIEW_MODEL`
  - payload: slide content
- No PATCH frames
- No progressive updates

### D) Stage completion
- `is_finished(trace)` must return:
  - `False` by default
  - engine closes the stage via host action / quiz flow
- Plugin must not self-close the stage

### E) Outcome
- `build_outcome()` must return:
  - `score_deltas = null`
  - `grade_deltas = null`
  - `render_summary = null`
  - `plugin_state_out = null`

This stage is explicitly **no-score**.

---

## 4) Scope — EXCLUDED

- PlayerEvent handling
- HostAction handling
- Random seed usage
- Deterministic scoring
- Replay complexity
- Multi-phase logic
- Any DB access

---

## 5) Data Contracts

### A) StageDefinition.plugin_spec (SLIDE)
The SLIDE plugin expects the following minimal plugin_spec:

```json
{
  "schema_version": "v0",
  "type": "slide",
  "content": {
    "title": "string",
    "body": "string",
    "media": {
      "type": "image | none",
      "src": "string | null"
    }
  }
}
```

Rules:

* All fields are JSON-serializable
* `media` is optional
* No implicit defaults outside this spec

### B) PluginFrame payload

Emitted frame payload shape:

```json
{
  "title": "string",
  "body": "string",
  "media": {
    "type": "image | none",
    "src": "string | null"
  }
}
```

---

## 6) Determinism Rules

* SLIDE plugin **must not use randomness**
* `random_seed` must be ignored if present
* Output must depend only on:

  * `StageContext.stage.plugin_spec`

This plugin serves as the baseline deterministic reference.

---

## 7) Engine Integration Rules

* Engine must treat SLIDE as a normal stage:

  * included in quiz stages
  * opened and closed like any other plugin
* Engine must not assume:

  * player submissions
  * scoring
  * interactive lifecycle

SLIDE must prove that **non-interactive stages are first-class citizens**.

---

## 8) Files to Create / Modify

### Plugin

* `plugins/slide/`

  * `__init__.py`
  * `manifest.py`
  * `runtime.py`
  * `schemas.py` (plugin-owned schema validation)
  * `README.md` (plugin description)

### Engine

* Register `slide` plugin in plugin registry (explicit)
* Allow stages with:

  * no PlayerEvent
  * no score output

### Docs

* Add SLIDE plugin reference to plugin documentation index

---

## 9) Tests

### Unit tests (plugin)

* Runtime creation with valid plugin_spec
* `on_stage_open()` emits exactly one frame
* `build_outcome()` returns a no-score outcome

### Integration tests (engine)

* Quiz with a single SLIDE stage:

  * stage opens correctly
  * slide is broadcast to players
  * stage closes without error
  * session continues to next stage

---

## 10) Definition of Done (DoD)

* [ ] SLIDE plugin loads via manifest without engine modification
* [ ] Stage with SLIDE renders correctly for host and players
* [ ] No PlayerEvent is required or processed
* [ ] No score or grade is produced
* [ ] Stage closes cleanly via engine flow
* [ ] Tests pass (plugin + engine)
* [ ] SLIDE plugin can be used as documentation reference

---

## 11) Exit Rule

Sprint 4 ends when:

* The SLIDE plugin runs end-to-end in a real session
* Plugin lifecycle V0 is validated in production-like conditions
* The plugin architecture is proven usable for future interactive plugins
