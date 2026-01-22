# Session Lifecycle Contract — v2

## Status

**DRAFT**

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
  - Players may request to join and wait for Host approval

- `ENDED`
  - Session is terminated
  - No join/leave is accepted
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
- join the session (only in `LOBBY`, or in `RUNNING` with approval)
- leave the session (only in `LOBBY`)

The engine must reject any non-host attempt to change session state.

---

## Join / Leave Rules (Sprint 0)

### Join in LOBBY
- Allowed only when the session state is `LOBBY`
- Auto-accepted
- A `player_joined` event is broadcast

### Join in RUNNING (Waiting Room)
- Allowed when the session state is `RUNNING`
- The player is placed in a waiting room
- The Host receives a `join_requested` event with a `request_id`
- The player is NOT added to the lobby until approval
- Host may approve or reject the request

### Join in ENDED
- Rejected when the session state is `ENDED`

### Leave
- Allowed only when the session state is `LOBBY`
- If a player disconnects unexpectedly in `LOBBY`, the engine must treat it as a leave

---

## Join Request Lifecycle

1) Player sends `join_session` during `RUNNING`
2) Engine sends `join_requested` to Host with `request_id`
3) Host responds with `host_approve_join` or `host_reject_join`
4) On approval:
   - player becomes active
   - `player_joined` is broadcast
   - `join_approved` is sent to the player
5) On rejection:
   - player is not added
   - `join_rejected` is sent to the player

Pending join requests are not included in `lobby_snapshot`.

---

## Host Kick Rules

The Host may remove a player in:
- `LOBBY`
- `RUNNING`

When a player is kicked:
- `player_kicked` is sent to the removed player
- `player_left` is broadcast to other clients

---

## Disconnect Handling

### Player disconnect
- If a player disconnects in `LOBBY`, the engine must remove them from the lobby list
- The engine must broadcast a `player_left` event

### Host disconnect
- In Sprint 0, host disconnect does NOT automatically end the session
- The session remains in its current state
- Behavior may evolve in later versions (but not in this contract v2)

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
