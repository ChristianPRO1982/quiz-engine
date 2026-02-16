# Runtime Plugin I/O Contract — v0 (Refined)

## 1. Purpose

This document defines the single stable contract between:

- The Engine (transport + orchestration + storage)
- The WebSocket layer (transport envelope)
- Plugins (business logic + scoring + rendering view-models)

The engine is deliberately dumb.
Plugins are fully responsible for logic and scoring.

This contract governs:
- Data entering a plugin
- Data leaving a plugin
- Runtime lifecycle
- Scoring normalization
- Determinism guarantees

---

# 2. Architectural Principles

## P1 — Engine is Dumb

The engine:
- Routes WS messages
- Instantiates plugin runtimes
- Stores StageTrace
- Stores StageOutcome
- Broadcasts PluginFrame
- Does NOT interpret payloads
- Does NOT calculate score
- Does NOT rank players
- Does NOT render HTML

The engine never interprets plugin logic.

---

## P2 — Plugins Own Logic

A plugin owns:

- Answer interpretation
- Scoring rules
- Grading rules
- Multi-phase logic
- Reveal logic
- View-model generation
- Finish conditions

---

## P3 — JSON-Only Rule (Hard Requirement)

All plugin-produced outputs MUST be JSON-like:

Allowed types:
- dict
- list
- string
- int / float (finite only)
- bool
- null

Forbidden:
- datetime objects
- bytes
- Decimal
- custom classes
- sets
- HTML blobs

If datetime is needed internally:
- Convert to ISO 8601 UTC string before transport.

---

## P4 — Determinism

Plugin results must be deterministic given:

- StageContext
- StageTrace
- random_seed (if used)

If randomness is used:
- stage.random_seed MUST be present
- All randomness derives only from that seed
- No system clock
- No external calls

---

# 3. WebSocket Envelope (Transport Layer)

All WebSocket messages follow:

```json
{ "type": "EVENT_NAME", "payload": { ... } }
```

Plugins do NOT speak WebSocket directly.
Engine converts WS messages into runtime objects.

---

# 4. Runtime Data Flow

## 4.1 Engine → Plugin

### StageContext

Provided at stage open.

Contains:

* session_id
* quiz_id
* server_now (server truth time)
* players: list of { player_id, display_name, metadata? }
* stage:

  * stage_id
  * stage_index
  * plugin_id
  * stage_kind
  * engine_prompt (engine-provided content)
  * plugin_spec (plugin configuration, opaque to engine)
  * time_limit_ms (optional)
  * random_seed (optional)
* scoreboard_snapshot (optional helper)
* plugin_state_in (optional resume input)

Rule:
Plugin must treat server_now as the only reliable clock.

---

## 4.2 Clients → Engine → Plugin

### PlayerEvent

Represents player actions.

Fields:

* player_id
* type: "SUBMIT" | "CHANGE" | "CLEAR"
* server_received_at (server truth)
* payload (plugin-defined JSON dict)
* client_sent_at (optional, untrusted)
* seq (optional)

Fairness rule:
Timing logic must use server_received_at.

---

### HostAction (Optional)

Plugin-defined actions:

Example:

```json
{ "action": "REVEAL" }
```

Engine routes HostAction to runtime.on_host_action().

---

## 4.3 Plugin → Engine → Clients

### PluginFrame

Used to update UI in real-time.

Structure:

```json
{
  "audience": "HOST" | "PLAYERS" | "ALL",
  "frame_type": "VIEW_MODEL" | "PATCH" | "REVEAL" | "...",
  "payload": { ... JSON view-model ... }
}
```

IMPORTANT:

* payload must be pure JSON view-model
* No HTML allowed
* Rendering is client responsibility

Recommended patterns:

* VIEW_MODEL → full snapshot
* PATCH → incremental update

---

## 4.4 Plugin → Engine (Stage Close)

### StageOutcome

Returned when stage closes.

Structure:

```json
{
  "score_entries": [
    {
      "player_id": "p1",
      "delta_score": 900,
      "grade_value": 1,
      "grade_max": 1,
      "details": {
        "answer": "B",
        "good_answers": "B ; C",
        "timing": "2.23s",
        "time_max": "10s"
      }
    }
  ],
  "render_summary": { ... optional final visual data ... },
  "plugin_state_out": { ... optional resume data ... }
}
```

Rules:

* score_entries may be null
* delta_score is numeric
* grade_value and grade_max are numeric
* details is optional and JSON-only
* Engine stores score_entries as-is
* Engine does NOT sum, rank, or interpret

Scoring aggregation is delegated to a plugin (e.g., scoreboard plugin).

---

# 5. Stage Lifecycle

Engine flow:

1. Engine selects StageDefinition
2. Engine calls create_runtime()
3. Engine calls on_stage_open()
4. During stage:

   * Engine receives PlayerEvent
   * Appends to StageTrace
   * Calls on_player_event()
   * Broadcasts PluginFrame
5. Stage closure occurs if:

   * time limit reached
   * runtime.is_finished(trace) == True
   * host forces next
6. Engine calls build_outcome(trace)
7. Engine stores StageOutcome

---

# 6. Finish Control (Host Gating)

Plugin indicates completion via:

```
runtime.is_finished(trace) -> bool
```

Host behavior rule:

* If True → Next button normal
* If False → Next button allowed but requires confirmation

Engine may always force stage close.

---

# 7. Rendering Model (Strict JSON View-Model)

Plugins MUST return view-model JSON only.

Example Slide:

```json
{
  "view": "slide",
  "title": "Welcome",
  "body": "Markdown text here",
  "media": { "type": "image", "src": "/assets/img1.png" }
}
```

Example MCQ Live:

```json
{
  "view": "mcq",
  "question": "Your question?",
  "choices": [
    { "id": "A", "label": "Option A", "count": 12 },
    { "id": "B", "label": "Option B", "count": 5 }
  ]
}
```

Client renders based on "view".

No HTML injection from plugin.

---

# 8. Plugin Assets (Manifest Extension)

Plugins may declare assets in their manifest:

```json
{
  "plugin_id": "mcq",
  "plugin_version": "1.0.0",
  "schema_version": "v0",
  "assets": {
    "js": ["/plugins/mcq/mcq.js"],
    "css": ["/plugins/mcq/mcq.css"]
  }
}
```

Engine responsibility:

* Load assets when plugin stage becomes active
* Avoid duplicate loading

Plugins remain fully self-contained.

---

# 9. Responsibilities Summary

## Engine MUST

* Route WS messages
* Instantiate runtime
* Store StageTrace
* Store StageOutcome
* Broadcast PluginFrame
* Remain logic-agnostic

## Plugin MUST

* Validate plugin_spec
* Be deterministic
* Emit JSON view-model only
* Produce structured score_entries
* Respect JSON-only rule

## Client MUST

* Render based on view-model
* Never compute score
* Never interpret plugin business rules

---

# 10. Versioning

Contract version: v0

Any breaking change requires:

* schema_version bump
* documentation update
* migration strategy

Formats rule everything.
Engine orchestrates.
Plugins think.
Clients render.

## Host Surface Composition — v0

### Principle

The Host surface is composed of two independent layers:

1) Plugin Rendering Layer (game display)
2) Engine Admin Overlay Layer (session control)

The plugin controls only the game display layer.
The engine controls only the admin overlay layer.

The two layers must not interfere logically.

---

# 1. Plugin Rendering Layer

Controlled entirely by the plugin.

Responsible for:
- Question display
- Animations
- Live aggregated data
- Reveal states
- Stage visuals

The engine does not modify plugin-rendered view-model.

---

# 2. Engine Admin Overlay Layer

Controlled entirely by the engine.

Always visible on Host surface.
Never visible to players.

Responsibilities:

- "Next Stage" button
  - Normal when `runtime.is_finished(trace) == True`
  - Confirmation required otherwise
- Session state display (LOBBY / RUNNING / ENDED)
- Player presence indicator
- Live player count
- Incoming player requests (waiting queue)
- Ability to accept/reject players (future extension)

The admin overlay must not depend on plugin payload.

---

# 3. Visual Design Constraint (Host Overlay)

The admin overlay must:

- Be visually discrete
- Not interfere with stage content
- Occupy minimal screen space by default
- Expand on hover or interaction

Recommended behavior:

- Narrow vertical bar on right side
- Shows:
  - Small player presence dots
  - Total connected count
  - Pending join indicator (highlighted)
- Expands on hover/click to reveal:
  - Full player list
  - "Next Stage" control
  - Session control buttons

This ensures:
- Stage remains visually dominant
- Admin tools remain accessible
- Cognitive load remains low

---

# 4. Player Join Management

Engine must:

- Distinguish between:
  - Connected players
  - Waiting players (joining mid-stage)
- Notify host when new players attempt to join
- Highlight pending join requests in overlay

Plugin does not manage player admission.

---

# 5. Separation of Concerns

Plugin must NOT:

- Control stage advancement
- Control player admission
- Render admin controls

Engine must NOT:

- Render stage visuals
- Interpret plugin view-model
- Override plugin display logic

The two layers coexist but remain logically isolated.

---

# 6. Philosophy

Host surface = Stage + Control

Stage is emotional.
Control is operational.

The engine manages operation.
Plugins manage emotion and gameplay.