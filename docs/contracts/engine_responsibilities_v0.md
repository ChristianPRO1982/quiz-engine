# Engine Responsibilities — v0

## Purpose

This document defines what the Engine is responsible for.

The engine is deliberately dumb.
It orchestrates.
It does not interpret business logic.

---

# 1. Core Responsibilities

## 1.1 Session Lifecycle

The engine must be able to:

- Create a session from a quiz
- Generate a unique `session_code`
- Maintain session state:
  - `LOBBY`
  - `RUNNING`
  - `ENDED`
- End a session cleanly

The engine controls the global session state machine.

---

## 1.2 Player Management

The engine must:

- Allow players to join a session
- Assign a stable `player_id`
- Maintain a roster (`players[]`)
- Handle player disconnect / reconnect
- Broadcast lobby snapshots to clients

The engine does not interpret player answers.

---

## 1.3 Stage Orchestration

The engine must:

- Maintain `stage_index`
- Advance to next stage when host requests
- Close current stage when:
  - time limit reached
  - `runtime.is_finished(trace)` returns True
  - host forces advance
- Create plugin runtime per stage
- Build and provide `StageContext`
- Route:
  - `PlayerEvent`
  - `HostAction`
  to the active runtime

The engine never interprets plugin payloads.

---

## 1.4 Real-Time Transport

The engine must:

- Accept WebSocket connections
- Translate WS messages into:
  - `PlayerEvent`
  - `HostAction`
- Broadcast `PluginFrame` to appropriate audience
- Keep WS envelope stable

The engine does not inspect or modify `PluginFrame.payload`.

---

## 1.5 Persistence

The engine must:

- Store `qe_session`
- Store `qe_stage_event`
- Store `qe_stage_outcome`
- Store `StageTrace`

The engine stores plugin-produced data as opaque JSON.

It does not:
- calculate score
- calculate ranking
- interpret grade
- aggregate deltas

All scoring interpretation belongs to plugins.

---

## 1.6 Stage Gating (Host Control)

The engine must:

- Call `runtime.is_finished(trace)`
- If True → allow normal stage advance
- If False → allow advance only with confirmation

The engine may always force close a stage.

---

# 2. Explicit Non-Responsibilities

The engine MUST NOT:

- Compute score
- Rank players
- Interpret plugin view-model
- Render HTML
- Validate plugin scoring logic
- Modify plugin payloads
- Contain plugin-specific logic

All business rules belong to plugins.

---

# 3. Philosophy

Engine orchestrates.
Plugins think.
Clients render.

The engine must remain small, stable, and predictable.

Complexity scales with plugins, not with engine code.
