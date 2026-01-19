# Session Lifecycle Contract — v1

## Status

**STABLE**

This contract defines the official session lifecycle for quiz-engine.
The engine MUST strictly enforce these states and transitions.

If behavior is not described here, it is invalid.

---

## Purpose

A session is a finite, explicit lifecycle controlled by the Host.

The lifecycle must be:
- deterministic
- simple
- resilient to disconnects
- enforced server-side (server is the source of truth)

This contract applies to:
- REST commands that affect session state
- WebSocket events that affect session state
- broadcasted session state updates

---

## Session States

A session MUST be in exactly one of these states:

- `LOBBY`
- `RUNNING`
- `ENDED`

### State Meaning

- `LOBBY`
  - Players may join and leave
  - Host may start the session
  - No quiz execution occurs in Sprint 0

- `RUNNING`
  - Session is active
  - In Sprint 0, this is only a state flag (no quiz logic)

- `ENDED`
  - Session is terminated
  - No join/leave is accepted (Sprint 0 default behavior)
  - No state transition out of ENDED is allowed

---

## Valid Transitions

Only these transitions are valid:

- `LOBBY` → `RUNNING` (Host action)
- `RUNNING` → `ENDED` (Host action)

### Forbidden Transitions

All other transitions are invalid, including:

- `LOBBY` → `ENDED` (direct end)
- `RUNNING` → `LOBBY` (rollback)
- `ENDED` → anything (terminal state)

---

## Host Authority

Only the Host can trigger state transitions.

Players can:
- join the session (only in `LOBBY`)
- leave the session (only in `LOBBY`)

The engine must reject any non-host attempt to change session state.

---

## Join / Leave Rules (Sprint 0)

### Join
- Allowed only when the session state is `LOBBY`
- Rejected when the session state is `RUNNING` or `ENDED`

### Leave
- Allowed only when the session state is `LOBBY`
- If a player disconnects unexpectedly, the engine must treat it as a leave

---

## Disconnect Handling

### Player disconnect
- If a player disconnects in `LOBBY`, the engine must remove them from the lobby list
- The engine must broadcast a `player_left` event

### Host disconnect
- In Sprint 0, host disconnect does NOT automatically end the session
- The session remains in its current state
- Behavior may evolve in later versions (but not in this contract v1)

---

## Idempotency

To ensure robustness, the engine SHOULD support idempotent behavior:

- `leave_session` for a non-existing player
  - should not crash the server
  - should result in either a no-op or an explicit error event

- repeated `host_start` in `RUNNING`
  - must be rejected as invalid transition

- repeated `host_end` in `ENDED`
  - must be rejected as invalid transition

---

## Required Broadcasts

Whenever the session state changes, the engine MUST broadcast:

- `session_state_changed`

The payload MUST include:
- `previous_state`
- `current_state`

The engine SHOULD also broadcast a `lobby_snapshot` after state changes
to resync all clients.

---

## Safety Rule

The engine must prefer explicit errors over silent behavior.

On invalid actions:
- reject the request
- broadcast an `error` event (when applicable)
- never mutate session state

---

## Final Rule

> The session lifecycle is small on purpose.
> Complexity belongs in plugins, not in the engine.

