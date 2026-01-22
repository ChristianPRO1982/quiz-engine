# WebSocket Protocol Contract — v2

## Status

**DRAFT**

This contract defines the WebSocket protocol used by quiz-engine.
All real-time communication MUST comply with this specification.

If a message does not conform to this protocol, it is invalid.

---

## Purpose

The WebSocket protocol is the single mechanism for:
- real-time session updates
- player join/leave notifications
- host commands
- error propagation
- join approvals when a session is already RUNNING

The server is the **single source of truth**.

---

## Global Envelope (MANDATORY)

All WebSocket messages MUST follow this envelope:

- `v` — protocol version (string)
- `type` — event name (string)
- `session_code` — session identifier (string)
- `payload` — event-specific data (object)

No message may omit or rename these fields.

---

## Protocol Versioning

- Current version: `"2"`
- All clients and servers MUST explicitly send `v: "2"`
- Incompatible versions MUST be rejected explicitly

Silent fallback is forbidden.

---

## Event Naming Rules

- Event names are lowercase
- Words are snake_case
- No namespaces or prefixes

Examples:
- `join_session`
- `player_left`
- `session_state_changed`

---

## Client → Server Events

### create_session

Creates a new session.

Payload:
- empty object `{}`

Notes:
- Typically initiated via REST, but allowed over WS
- Server must respond with `session_created`

---

### join_session

Requests to join an existing session.

Payload:
- `nickname` (string)

Rules:
- Allowed in `LOBBY` (auto-accepted)
- Allowed in `RUNNING` (requires host approval)
- Rejected in `ENDED`

---

### leave_session

Requests to leave a session.

Payload:
- empty object `{}`

Rules:
- Allowed only in `LOBBY`
- Idempotent behavior is recommended

---

### host_start

Requests to start the session.

Payload:
- empty object `{}`

Rules:
- Allowed only for the Host
- Valid only in `LOBBY`

---

### host_end

Requests to end the session.

Payload:
- empty object `{}`

Rules:
- Allowed only for the Host
- Valid only in `RUNNING`

---

### host_approve_join

Approves a pending join request while the session is RUNNING.

Payload:
- `request_id` (string)

Rules:
- Allowed only for the Host
- Valid only in `RUNNING`

---

### host_reject_join

Rejects a pending join request while the session is RUNNING.

Payload:
- `request_id` (string)

Rules:
- Allowed only for the Host
- Valid only in `RUNNING`

---

### host_kick

Removes a player from the session.

Payload:
- `player_id` (string)

Rules:
- Allowed only for the Host
- Valid in `LOBBY` and `RUNNING`

---

## Server → Client Events

### session_created

Sent after successful session creation.

Payload:
- `session_code` (string)

---

### lobby_snapshot

Represents the full current lobby state.

Payload:
- `players` (array)
  - each entry includes:
    - `player_id`
    - `nickname`

Notes:
- Must be broadcast after any join or leave
- Used for client resynchronization

---

### session_status

Sent to inform a client of the current session state.

Payload:
- `current_state` (`LOBBY`, `RUNNING`, or `ENDED`)

Notes:
- SHOULD be sent to players after they connect or submit `join_session`

---

### join_requested

Sent to the Host when a player requests to join during RUNNING.

Payload:
- `request_id`
- `nickname`

---

### join_approved

Sent to the requesting player after host approval.

Payload:
- `request_id`
- `player_id`
- `nickname`

---

### join_rejected

Sent to the requesting player after host rejection.

Payload:
- `request_id`
- `reason` (string)

---

### player_joined

Sent when a player joins the lobby.

Payload:
- `player_id`
- `nickname`

---

### player_left

Sent when a player leaves or disconnects.

Payload:
- `player_id`

---

### player_kicked

Sent to a player when the Host removes them.

Payload:
- `player_id`

---

### session_state_changed

Sent when the session state changes.

Payload:
- `previous_state`
- `current_state`

---

### error

Sent when an error occurs.

Payload:
- `code` (string)
- `message` (string)
- `details` (optional, object)

Rules:
- Errors must be explicit
- Silent failures are forbidden

---

## Ordering and Delivery

- Message ordering is guaranteed **per connection**
- Global ordering across connections is not guaranteed
- Clients must be able to handle out-of-order updates using snapshots

---

## Validation Rules

The engine MUST validate:
- envelope structure
- protocol version
- event type validity
- session state compatibility

Invalid messages MUST result in an `error` event.

---

## Security Notes (Sprint 0)

- No authentication is required
- Host identity is implicit (connection-based)
- Security hardening may be added in later versions

This contract does not define authentication mechanisms.

---

## Final Rule

> Real-time systems fail when protocols are vague.
> This protocol is intentionally strict.
