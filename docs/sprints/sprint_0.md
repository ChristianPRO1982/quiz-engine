# Sprint 0 — Technical Foundation (Realtime Lobby)

## 1. Sprint Objective
Build a minimal but complete technical foundation proving that:

- The backend, frontend, and smartphones communicate correctly
- Real-time communication works reliably
- A live session can be created, joined, and controlled

This sprint validates the full technical chain without any quiz logic.

---

## 2. Scope — INCLUDED

### Backend
- FastAPI application
- REST endpoint to create a session
- WebSocket endpoint for real-time communication
- In-memory session management
- Explicit session state machine

### Frontend
- Minimal Host interface:
  - Create session
  - Display session code
  - Display QR code
  - Display live list of connected players
  - Start / End session buttons
- Minimal Player interface:
  - Join via session code (pre-filled from QR)
  - Enter nickname
  - Join / Leave session

### Realtime
- Live updates when:
  - A player joins
  - A player leaves
  - Session state changes

### Infrastructure
- HTTPS access via Traefik
- Docker-compatible service
- Works on desktop + smartphone browsers

---

## 3. Scope — EXCLUDED

- Quiz definition or execution
- Question logic
- Plugins
- Scoring
- Timers
- Persistence (PostgreSQL, Redis, files)
- Authentication (Google / email)
- RGPD consent management (placeholder only)

---

## 4. Session Model (Sprint 0)

### Session States
- `LOBBY`
- `RUNNING`
- `ENDED`

State transitions:
- LOBBY → RUNNING (host action)
- RUNNING → ENDED (host action)

No automatic transitions.

---

## 5. Event Protocol (Version 1)

All events MUST include:
- `v` (protocol version, `"1"`)
- `type`
- `session_code`
- `payload`

### Client → Server Events
- `create_session`
- `join_session`
- `leave_session`
- `host_start`
- `host_end`

### Server → Client Events
- `session_created`
- `lobby_snapshot`
- `player_joined`
- `player_left`
- `session_state_changed`
- `error`

---

## 6. Acceptance Criteria

The sprint is considered DONE if all conditions below are met:

1. A Host can create a session and receive a session code.
2. The Host interface displays a QR code pointing to the Player join page.
3. A Player can join the session using a smartphone via QR code.
4. The Host sees players joining and leaving in real time.
5. If a Player disconnects, the Host is notified.
6. The Host can start the session (state changes to RUNNING).
7. The Host can end the session (state changes to ENDED).
8. All state changes are broadcast to connected clients.
9. The system runs behind HTTPS via Traefik.
10. Automated tests cover:
    - Session creation
    - State transitions
    - WebSocket join/leave behavior

---

## 7. Non-Functional Requirements

- Code must respect the global project contract
- No hard-coded quiz or game logic
- Clear separation between engine core and future features
- Failures must return explicit error events (no silent failures)

---

## 8. Sprint Exit Rule

Sprint 0 ends when:
- The technical foundation is proven working end-to-end
- The system can be tested live with at least:
  - 1 host (desktop)
  - 2 players (smartphones)

No new features may be added once acceptance criteria are satisfied.
