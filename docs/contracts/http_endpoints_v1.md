# HTTP Endpoints — v1
Authoritative REST API contract

Status: CANONICAL
Schema version: v1
Scope: Engine REST surface

WebSocket runtime is defined in:
docs/contracts/runtime_plugin_io_v1.md

Runtime structures are defined in:
docs/contracts/runtime_schema_v1.md

---

# 1. Design Principles

- REST manages lifecycle and configuration
- WebSocket handles live gameplay
- Engine remains dumb
- No ranking endpoints
- No computed percentages
- No float-based responses

---

# 2. Session Endpoints

## 2.1 Create Session

POST /sessions

Request:

```json
{
  "quiz_id": "string"
}
```

Response:

```json
{
  "session_id": "string",
  "status": "LOBBY"
}
```

Engine:

* Generates session_id
* Sets status to LOBBY
* Does not start automatically

---

## 2.2 Get Session

GET /sessions/{session_id}

Response:

```json
{
  "session_id": "string",
  "quiz_id": "string",
  "status": "LOBBY | RUNNING | FINISHED",
  "current_stage_index": "integer | null"
}
```

No ranking data included.

---

## 2.3 Start Session

POST /sessions/{session_id}/start

Response:

```json
{
  "session_id": "string",
  "status": "RUNNING"
}
```

Engine:

* Activates first stage
* WS handles live broadcast

---

## 2.4 Finish Session

POST /sessions/{session_id}/finish

Response:

```json
{
  "session_id": "string",
  "status": "FINISHED"
}
```

Engine does not compute winners.

---

# 3. Player Endpoints

## 3.1 Join Session

POST /sessions/{session_id}/players

Request:

```json
{
  "display_name": "string"
}
```

Response:

```json
{
  "player_id": "string"
}
```

Engine:

* Registers player
* Does not assign score

---

## 3.2 List Players

GET /sessions/{session_id}/players

Response:

```json
[
  {
    "player_id": "string",
    "display_name": "string",
    "is_active": "boolean"
  }
]
```

No score totals included.

Snapshots are available via WebSocket
and via GET /sessions/{session_id}/snapshot (optional read-only endpoint).

---

# 4. Stage Endpoints

## 4.1 Get Stage

GET /sessions/{session_id}/stages/{stage_index}

Response:

```json
{
  "stage_id": "string",
  "plugin_key": "string",
  "status": "PENDING | ACTIVE | RESOLVED | FAILED"
}
```

No scoring data returned.

---

## 4.2 Advance Stage

POST /sessions/{session_id}/stages/{stage_index}/next

Behavior:

* Triggers resolve() if ACTIVE
* Activates next stage if exists

Response:

```json
{
  "message": "stage_transition_triggered"
}
```

Actual results delivered via WebSocket.

---

# 5. StageOutcome Retrieval

## 5.1 Get StageOutcome

GET /sessions/{session_id}/stages/{stage_index}/outcome

Response:

StageOutcome structure as defined in runtime_schema_v1.md

Includes:

* public_state
* score_entries

Engine does not compute totals here.

---

# 6. Snapshot Endpoint (Optional Read-Only)

GET /sessions/{session_id}/snapshot

Response:

```json
{
  "player_totals": {
    "player_id": {
      "total_score": "integer",
      "total_grade_value": "integer",
      "total_grade_max": "integer"
    }
  }
}
```

Rules:

* Pure summation
* No ranking
* No ordering
* No percentages
* Player order is undefined and must not be interpreted as ranking.

---

# 7. Plugin Registry Endpoint

## 7.1 List Plugins

GET /plugins

Response:

```json
[
  {
    "plugin_key": "string",
    "name": "string",
    "version": "string"
  }
]
```

No runtime state included.

---

# 8. Explicit Non-Endpoints

The engine must not expose:

* /leaderboard
* /ranking
* /winners
* /percentages
* /podium
* /scoreboard (ranked)

Ranking belongs to plugins if needed.

---

# 9. Error Model

All errors must follow:

```json
{
  "error": "string",
  "message": "string"
}
```

No business interpretation in error messages.

---

# 10. Versioning

Versioning handled via:

* URL prefix (optional future)
* Contract version inside runtime structures

Endpoints are stable under v1.
