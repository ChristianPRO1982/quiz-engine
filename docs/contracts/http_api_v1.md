# HTTP API Contract — v1

## Status

**DRAFT**

This contract defines the HTTP endpoints and payload formats
used by quiz-engine in Sprint 0.

If a behavior or format is not described here, it is invalid.

---

## Purpose

The HTTP API is used for:
- session creation
- serving the minimal Host and Player pages
- serving the QR code PNG

---

## Base Rules

- All JSON responses are UTF-8 encoded.
- All JSON formats are versioned.
- All session identifiers are `session_code` strings.

---

## Create Session

### Endpoint

`POST /api/sessions`

### Request

- No request body

### Response — CreateSessionResponse

Fields:
- `schema_version` (string, must be `"1"`)
- `session_code` (string)
- `join_url` (string)

Example:
```
{
  "schema_version": "1",
  "session_code": "ABC123",
  "join_url": "https://quiz-engine.localhost/join/ABC123"
}
```

---

## Host Page

### Endpoint

`GET /`

Returns the Host HTML page.

---

## Player Page

### Endpoint

`GET /join/{session_code}`

Returns the Player HTML page.

---

## QR Code

### Endpoint

`GET /qr/{session_code}.png`

Returns a PNG QR code pointing to `/join/{session_code}`.

---

## WebSocket Endpoint (Transport)

### Endpoint

`GET /ws` (WebSocket)

Query params:
- `role` (optional, `host` or `player`, defaults to `player`)
- `session_code` (optional; required for host connections to existing sessions)

Notes:
- The WebSocket message envelope is defined by `ws_protocol_v2.md`.
- Host connections without a `session_code` must create a session via
  the `create_session` WebSocket event before sending host commands.
