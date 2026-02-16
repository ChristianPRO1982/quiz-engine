# Runtime Plugin I/O — v1
Engine ↔ Plugin ↔ WebSocket interaction model

Status: CANONICAL (flow-level)
Schema version: v1
Scope: Runtime orchestration and messaging

This document defines interaction flow only.

Data models are defined in:
- docs/contracts/runtime_schema_v1.md
- docs/contracts/scoreEntry_contract_v1.md

---

# 1. Architecture Overview

The engine orchestrates runtime.
Plugins implement stage logic.

The engine:
- Creates stages
- Activates stages
- Routes player inputs
- Calls plugin resolution
- Broadcasts outputs
- Persists outcomes

The plugin:
- Owns business logic
- Owns scoring logic
- Owns determinism
- Owns Host UI behavior
- Owns Player UI behavior
- Produces StageOutcome

---

# 2. WebSocket Envelope (Single Format)

All WebSocket messages must follow this structure:

```json
{
  "type": "EVENT_NAME",
  "payload": { ... }
}
````

Rules:

* `type` is uppercase snake_case
* `payload` is always an object
* Engine never infers meaning from payload
* Plugins define semantic meaning of payload

---

# 3. High-Level Runtime Flow

## 3.1 Session Start

1. Host starts session
2. Engine sets session.status = RUNNING
3. Engine activates first stage

No plugin logic executed yet.

---

## 3.2 Stage Activation

Engine performs:

1. Load Stage

2. Resolve plugin by `plugin_key`

3. Initialize plugin runtime with:

   * config
   * seed
   * player list

4. Broadcast:

```json
{
  "type": "STAGE_STARTED",
  "payload": {
    "stage_id": "...",
    "plugin_key": "...",
    "public_state": { ... }
  }
}
```

`public_state` is plugin-defined.

Engine does not interpret it.

---

## 3.3 Player Input

Players send:

```json
{
  "type": "PLAYER_ACTION",
  "payload": {
    "stage_id": "...",
    "action": { ... }
  }
}
```

Engine:

* Validates session + stage
* Forwards action to plugin runtime
* Does not interpret action content

Plugin may update internal state.

Plugin may emit intermediate public updates.

---

## 3.4 Intermediate Plugin Broadcast (Optional)

Plugin may request broadcast:

```json
{
  "type": "STAGE_UPDATE",
  "payload": {
    "stage_id": "...",
    "public_state": { ... }
  }
}
```

Engine only routes.

---

## 3.5 Stage Resolution

Triggered by:

* Host action (Next)
* Plugin condition satisfied
* Timeout
* Deterministic auto-resolution

Engine calls:

```
plugin.resolve()
```

Plugin returns:

StageOutcome (see runtime_schema_v1.md)

---

## 3.6 StageOutcome Broadcast

Engine:

1. Persists StageOutcome
2. Aggregates ScoreEntry mechanically
3. Broadcasts:

```json
{
  "type": "STAGE_RESOLVED",
  "payload": {
    "stage_id": "...",
    "public_state": { ... },
    "score_entries": [ ... ]
  }
}
```

Engine does not modify score_entries.

---

# 4. Host Overlay Events

The engine may emit host-only events:

```json
{
  "type": "HOST_SNAPSHOT",
  "payload": {
    "player_totals": { ... },
    "active_players": "...",
    "stage_index": "..."
  }
}
```

Rules:

* Snapshot is derived only
* No ranking
* No interpretation
* Integer-only totals

---

# 5. Determinism Requirements

Plugins must:

* Use provided seed
* Avoid non-deterministic randomness
* Avoid time-based randomness
* Avoid external IO during resolution

Given same:

* config
* seed
* player actions

Must produce identical StageOutcome.

---

# 6. Explicit Engine Non-Responsibilities

The engine must not:

* Rank players
* Decide winners
* Compute percentages
* Modify scoring values
* Apply scoring rules
* Interpret public_state
* Generate UI

---

# 7. Plugin Lifecycle (Simplified)

For each stage:

1. initialize(config, seed, players)
2. handle_player_action(action)
3. optionally emit updates
4. resolve() → StageOutcome

Engine never bypasses this lifecycle.

---

# 8. Error Handling

If plugin throws:

* Engine marks stage as FAILED
* Emits:

```json
{
  "type": "STAGE_ERROR",
  "payload": {
    "stage_id": "...",
    "message": "..."
  }
}
```

Engine does not attempt scoring recovery.

---

# 9. Immutability

Once StageOutcome is stored:

* It must not be modified
* score_entries must not be recalculated
* public_state must remain stable

Replays must produce identical results.

---

# 10. Versioning

schema_version applies to runtime structures (StageOutcome, ScoreEntry).

WebSocket envelope versioning is implicit in runtime version.
