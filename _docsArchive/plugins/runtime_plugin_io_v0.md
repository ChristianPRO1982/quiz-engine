````markdown
# Runtime Plugin I/O Contract — v0

## Purpose

This document defines the **single, stable contract** between:
- the **engine** (transport/orchestration + storage),
- the **WebSocket layer** (transport envelope),
- and **plugins** (business logic + rendering frames + outcomes).

**Goal:** any plugin can run in quiz-engine without inventing custom WS protocols.
Plugins do **not** speak WebSocket directly. Plugins speak:
- `StageContext` (engine → plugin)
- `PlayerEvent` / `HostAction` (clients → engine → plugin)
- `PluginFrame` (plugin → engine → clients)
- `StageOutcome` (plugin → engine → storage)

This contract is **versioned**. Any breaking change requires bumping contract version.

---

## Core Principles

### P1 — Engine is dumb
The engine:
- routes events to the active plugin runtime
- stores `StageTrace` and `StageOutcome`
- broadcasts `PluginFrame` to clients
- sums `delta_score` in `score_deltas`

The engine **does not interpret** plugin payloads or scoring rules.

### P2 — Plugin owns all logic
A plugin owns:
- answer interpretation
- scoring and grading
- reveal logic / multi-phase logic
- live visuals (frames)

### P3 — JSON-only (hard requirement)
All plugin-produced payloads MUST be JSON-like:
- dict, list, str, int/float (finite), bool, null  
No bytes, datetime objects, Decimal, sets, custom classes.

Datetimes at transport boundaries are ISO 8601 UTC strings.
Internally, a plugin may use datetime objects, but must serialize before output.

### P4 — Determinism
Plugin results must be deterministic given the same inputs:
- `StageContext` + `StageTrace` (+ `random_seed` if used)

If a plugin uses randomness:
- `StageDefinition.random_seed` MUST be present
- all randomness must derive from that seed only (no system time, no global RNG state)

---

## WebSocket Transport Contract (Engine Layer)

### WS Envelope (required)
All WebSocket messages are JSON objects:
```json
{ "type": "EVENT_NAME", "payload": { "...": "..." } }
```

The engine is responsible for translating WS messages into runtime objects
and calling plugin runtime methods.

---

## Runtime Objects (Plugin Contract)

### 1) StageContext (engine → plugin)

**When:** stage becomes active.

`StageContext` provides:

* stable identifiers (`session_id`, `quiz_id`)
* server truth time (`server_now`)
* current player roster (`players[]`)
* stage definition:

  * `stage_id`, `stage_index`
  * `plugin_id`, `stage_kind`
  * `engine_prompt` (engine-provided prompt content)
  * `plugin_spec` (plugin-owned config)
  * `time_limit_ms` (optional)
  * `random_seed` (optional, required if plugin uses randomness)
* optional snapshots:

  * `scoreboard_snapshot` (engine totals; helper only)
  * `plugin_state_in` (for replay/resume)

**Contract rule:** a plugin must treat `server_now` as the only reliable clock.

---

### 2) PlayerEvent (clients → engine → plugin)

**When:** players interact during an active stage.

Minimum event types:

* `SUBMIT` — first answer submission
* `CHANGE` — user changes their answer (optional per plugin)
* `CLEAR` — user clears answer (optional per plugin)

Required fields:

* `player_id` (stable)
* `type` (`SUBMIT|CHANGE|CLEAR`)
* `server_received_at` (server truth)
* `payload` (plugin-defined dict)
  Optional:
* `client_sent_at` (informational, untrusted)
* `seq` (optional client sequence id)

**Fairness rule:** timing-based logic MUST use `server_received_at`, not client time.

---

### 3) HostAction (clients → engine → plugin, optional)

**When:** host interacts with stage controls (reveal, next phase, lock, etc.)

Shape is plugin-defined, but must be JSON-like. Example:

```json
{ "action": "REVEAL" }
```

A plugin may ignore host actions if it does not support them.

---

### 4) PluginFrame (plugin → engine → clients)

**When:** plugin wants to update the UI (host, players, or both).

Required fields:

* `audience`: `"HOST" | "PLAYERS" | "ALL"`
* `frame_type`: string (free naming)
* `payload`: dict (plugin-defined view model)

Recommended frame patterns:

* `VIEW_MODEL` — full render snapshot
* `PATCH` — incremental updates
* `REVEAL` — reveal phase updates (optional)

**Contract rule:** frames must be small; send aggregates not full traces.

---

### 5) StageOutcome (plugin → engine)

**When:** stage closes (time elapsed OR host ends OR plugin finished).

Fields:

* `score_deltas`: list or null
* `grade_deltas`: list or null
* `render_summary`: dict or null (final visuals)
* `plugin_state_out`: dict or null (for replay/resume)
* `next_hint`: dict or null (engine may ignore)

Notes:

* No-score stages MUST return `score_deltas=null` and `grade_deltas=null`.
* Engine will only sum `delta_score`. It will not validate your rules.

---

## Engine ↔ Plugin Lifecycle (V0)

A stage is driven by one plugin runtime instance.

Engine flow:

1. Engine selects `StageDefinition`
2. Engine calls plugin `create_runtime(session_id, stage_definition)`
3. Engine calls runtime `on_stage_open(stage_context)` (optional frames)
4. During stage:

   * Engine receives WS player events
   * Engine appends to `StageTrace`
   * Engine calls runtime `on_player_event(event, trace)` (optional frames)
   * Engine broadcasts returned frames
5. Engine closes stage:

   * time limit elapsed OR `is_finished(trace)` OR host stops
6. Engine calls runtime `build_outcome(trace)` and stores `StageOutcome`

Optional:

* `on_host_action(action, trace)` if stage supports host controls.

---

## Standard WS Event Types (Engine Layer)

### Incoming (Client → Engine)

These WS messages are standardized at engine level:

#### PLAYER_EVENT

Payload maps to `PlayerEvent` fields:

```json
{
  "type": "PLAYER_EVENT",
  "payload": {
    "player_id": "p1",
    "event_type": "SUBMIT",
    "payload": { "selected": ["A"] },
    "client_sent_at": "2026-02-10T09:00:00Z",
    "seq": 12
  }
}
```

#### HOST_ACTION (optional)

```json
{
  "type": "HOST_ACTION",
  "payload": {
    "action": "REVEAL"
  }
}
```

### Outgoing (Engine → Clients)

#### PLUGIN_FRAME

The engine broadcasts frames returned by plugin callbacks:

```json
{
  "type": "PLUGIN_FRAME",
  "payload": {
    "audience": "ALL",
    "frame_type": "VIEW_MODEL",
    "payload": {
      "view": "mcq",
      "data": { "title": "Question?", "choices": [ ... ] }
    }
  }
}
```

---

## Responsibilities Matrix

### Plugin MUST

* Validate `plugin_spec` it receives
* Be deterministic (and require `random_seed` if randomness is used)
* Accept `PlayerEvent` and optionally `HostAction`
* Emit `PluginFrame` updates as needed (JSON-like only)
* Produce `StageOutcome` (JSON-like only)

### Engine MUST

* Keep WS envelope stable
* Convert WS messages into `PlayerEvent` / `HostAction`
* Store `StageTrace` and `StageOutcome` (opaque plugin-owned payloads)
* Broadcast `PluginFrame` to clients without interpreting payloads
* Enforce transport safety (JSON-only)

### Clients MUST

* Send user actions as `PLAYER_EVENT`
* Render frames based on `frame_type` and payload (plugin view model)
* Never assume scoring logic client-side

---

## Minimal Examples (Plugin-owned payloads)

### Example A — MCQ Single

PlayerEvent payload:

```json
{ "selected": ["A"] }
```

Frame VIEW_MODEL:

```json
{
  "prompt": { "title": "Your question..." },
  "choices": [
    { "id": "A", "label": "Option A", "count": 12 },
    { "id": "B", "label": "Option B", "count": 5 }
  ],
  "total_responses": 17
}
```

Outcome (with score):

```json
{
  "score_deltas": [
    { "player_id": "p1", "delta_score": 850, "meta": { "time_ms": 1200 } }
  ],
  "grade_deltas": [
    { "player_id": "p1", "value": 1, "max_value": 1, "scale": "points" }
  ],
  "render_summary": { "correct_choice": "B" },
  "plugin_state_out": null
}
```

### Example B — No-score stage (e.g., slide)

Outcome:

```json
{
  "score_deltas": null,
  "grade_deltas": null,
  "render_summary": null,
  "plugin_state_out": null
}
```

---

## Compatibility Notes

* Plugins may choose to support `CHANGE` and `CLEAR` events.
* Plugins may implement multi-phase stages using either:

  * internal phases (frames + plugin_state_out)
  * multiple stages chained (preferred for simplicity)

---

## Versioning

This contract is version `v0`.

Any change that modifies:

* required fields,
* WS envelope,
* lifecycle expectations,
* or JSON-only / determinism constraints

is a breaking change and requires a new contract version.
