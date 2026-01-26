# Codex Task List — Implement Runtime Contracts + Plugin Interfaces (quiz-engine only)

## Scope
Implement the V0 runtime contracts and engine↔plugin interfaces inside quiz-engine.
No plugin business logic. No concrete plugins required (use a dummy plugin for tests).

## Non-goals
- No scoring rules in engine (engine only sums ScoreDelta).
- No answer interpretation in engine.
- No full UI/templates work here (only transport-ready structures).

---

## Files to Create / Modify

### Create
- `quiz_engine/contracts/runtime_models.py`
- `quiz_engine/contracts/serialization.py`
- `quiz_engine/plugins/interfaces.py`
- `quiz_engine/plugins/registry.py`
- `quiz_engine/runtime/stage_runner.py`
- `quiz_engine/runtime/score_aggregator.py`
- `quiz_engine/runtime/trace_store.py`
- `quiz_engine/ws/messages.py`
- `tests/test_runtime_models.py`
- `tests/test_serialization.py`
- `tests/test_plugin_registry.py`
- `tests/test_stage_runner.py`
- `tests/test_score_aggregator.py`

### Modify (if exists)
- `quiz_engine/settings/...` (only if you need config for plugin discovery)
- `quiz_engine/app.py` / routers to wire WS routes (minimal)

---

## Implementation Plan (Phases)

## Phase A — Runtime Models (POO)
### Goal
Implement Python runtime contracts as models with validation and strict JSON-serializable payload constraints.

### Tasks
1. Implement models:
   - `PluginManifest`
   - `StageDefinition`
   - `PlayerIdentity`
   - `StageContext`
   - `PlayerEvent`
   - `StageTrace`
   - `PluginFrame`
   - `ScoreDelta`
   - `GradeDelta`
   - `StageOutcome`

2. Enforce invariants:
   - `stage_index >= 0`
   - `server_received_at` always required on `PlayerEvent` (engine assigns it)
   - payload dicts must be JSON-like (dict/list/str/int/float/bool/None)
   - `ScoreDelta.delta_score` finite (reject NaN/inf)
   - `GradeDelta.max_value > 0` if provided
   - ids non-empty strings

3. Add minimal helper methods (no business logic):
   - `to_transport_dict()` -> dict JSON-ready (datetime -> ISO 8601 string)
   - `from_transport_dict()` -> rehydrate (ISO -> datetime)

### Tests
- Create test cases for each invariant.
- Ensure transport round-trip works for all models.

---

## Phase B — Serialization Utilities
### Goal
Centralize serialization rules for datetime and JSON-like validation.

### Tasks
1. Implement:
   - `is_json_like(value) -> bool`
   - `ensure_json_like(value, path) -> None` (raises ValueError)
   - `datetime_to_iso(dt) -> str` (UTC, ISO 8601)
   - `iso_to_datetime(s) -> datetime`
   - `dump_model(model) -> dict` (calls model serializer)
   - `load_model(cls, data) -> cls`

2. Ensure no timezone ambiguity:
   - store UTC `Z` format consistently

### Tests
- Validate ISO formatting, timezone handling
- Validate deep JSON-like checking (nested lists/dicts)

---

## Phase C — Plugin Interfaces + Registry
### Goal
Define stable plugin-facing interfaces and a registry that loads plugins.

### Tasks
1. Implement interfaces:
   - `IPlugin` with `get_manifest()` and `create_runtime(...)`
   - `IStageRuntime` with:
     - `on_stage_open(context) -> list[PluginFrame] | None`
     - `on_player_event(event, trace) -> list[PluginFrame] | None`
     - `on_host_action(action, trace) -> list[PluginFrame] | None`
     - `is_finished(trace) -> bool`
     - `build_outcome(trace) -> StageOutcome`

2. Implement `PluginRegistry`:
   - register plugins in-memory
   - lookup by `plugin_id`
   - provide list of manifests for “load all plugins” step

3. Add a dummy plugin for tests (in tests only):
   - returns a manifest
   - stage runtime that echoes frames and returns an outcome

### Tests
- registry registers and resolves plugin_id
- manifest listing works
- dummy plugin runtime calls work

---

## Phase D — Stage Runner (Engine Orchestration)
### Goal
Orchestrate a stage in quiz-engine: accept events, append trace, call plugin runtime, emit frames, close stage.

### Tasks
1. Implement `StageRunner` responsibilities:
   - `open_stage(context) -> None`
   - `handle_player_event(event_payload_dict) -> list[PluginFrame]`
     - engine sets `server_received_at`
     - validates payload JSON-like
     - appends `PlayerEvent` to `StageTrace`
     - calls plugin runtime `on_player_event`
   - `handle_host_action(action_dict) -> list[PluginFrame]`
   - `maybe_close() -> StageOutcome | None`
     - checks time_limit_ms if set (engine)
     - checks plugin `is_finished(trace)`
     - if closed: calls `build_outcome(trace)` and returns it

2. Ensure runner is deterministic:
   - no random in engine
   - only plugin uses random_seed from StageDefinition

### Tests
- open -> handle events -> frames returned
- trace append-only and ordering respected
- closing returns StageOutcome

---

## Phase E — Trace Store + Score Aggregator
### Goal
Provide engine-owned persistence hooks and score aggregation.

### Tasks
1. `TraceStore` (in-memory first):
   - store per session_id per stage_id:
     - StageTrace
     - StageOutcome
2. `ScoreAggregator`:
   - apply `StageOutcome.score_deltas` by summing per player
   - store totals and per-stage totals if you want
   - store GradeDelta as recorded, no computation

### Tests
- aggregator sums correctly with multiple deltas
- handles missing score_deltas gracefully
- grade deltas stored but not aggregated unless explicitly requested later

---

## Phase F — WS Message Envelopes (quiz-engine side)
### Goal
Define consistent WS message shapes for engine and plugin frames.

### Tasks
1. Implement message helpers:
   - envelope: `{ "type": str, "payload": dict }`
2. Define constants:
   - `PLAYER_EVENT` (client -> server)
   - `PLUGIN_FRAME` (server -> clients)
   - `ENGINE_STAGE_OPENED`, `ENGINE_STAGE_CLOSED`, `ENGINE_SCORE_UPDATE`
3. Ensure payloads are JSON-only:
   - datetimes are strings

### Tests
- envelope builder returns valid JSON-like dicts

---

## Local Commands (dev + tests)
- Install deps:
  - `uv sync --dev`
- Run tests:
  - `uv run pytest -q`
- Lint/format (if enabled):
  - `uv run ruff check .`
  - `uv run ruff format --check .`

---

## Definition of Done (DoD)
- All runtime models exist with invariants enforced.
- Transport serialization round-trips for all contracts.
- Plugin interfaces exist and dummy plugin passes tests.
- StageRunner can process events and produce frames/outcome.
- ScoreAggregator sums score deltas only.
- TraceStore persists traces/outcomes (in-memory acceptable for now).
- All tests pass in CI.

---

## Notes / Guardrails
- Engine must never interpret `PlayerEvent.payload` content.
- Engine must never compute scoring rules; only sum `ScoreDelta`.
- Payload dicts must remain JSON-like for WS + replay.
- Any plugin requiring randomness must rely on `StageDefinition.random_seed`.
