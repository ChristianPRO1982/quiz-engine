# Sprint 7 — First Live Session (Host + Players + Real-Time Stage Broadcasting)

## 1) Sprint Objective

Enable a real, end-to-end live session flow:

- A host can start a live session from a quiz
- Players can join from a smartphone via QR code and session code
- The current stage is broadcast in real-time to connected clients
- The host can advance the quiz stage-by-stage
- The session can be ended cleanly
- Minimal persistence is recorded for replay foundations

This sprint validates the full chain:
**quiz → session → real-time → clients**, using the plugin lifecycle as the runtime driver.

---

## 2) Scope — INCLUDED

### A) Start session from a quiz (host)
- From the quiz list or quiz detail/editor, the host can click **Start session**.
- Starting a session creates:
  - a session record in DB (`qe_session`)
  - a unique human-friendly `session_code`
- Host is redirected to the host screen:
  - `/host/s/{session_code}`

### B) Join session (players)
- Host screen shows:
  - `session_code`
  - QR code pointing to `/join/{session_code}`
- Players can:
  - open the join page (mobile)
  - enter nickname
  - join the session
- Connected player list is visible to the host and updates in real-time.

### C) Real-time transport (WebSocket)
- Both host and players connect via WebSocket:
  - `/ws/s/{session_code}?role=host|player`
- The engine maintains in-memory live state for:
  - connected clients
  - current stage pointer
  - session lifecycle state (`LOBBY`, `RUNNING`, `ENDED`)

### D) Session lifecycle controls (host)
- Host actions:
  - Start session (LOBBY → RUNNING)
  - Next stage (advance to next quiz stage)
  - End session (RUNNING → ENDED or LOBBY → ENDED)
- State changes are broadcast to all clients in real-time.

### E) Stage runtime + broadcasting
- When a stage becomes active:
  - engine loads StageDefinition from the quiz payload
  - engine creates the plugin runtime for that stage
  - engine calls `on_stage_open(stage_context)`
  - returned frames are broadcast to clients via WS

Clients render the received view-model frames.

### F) Minimal trace & outcome persistence
- For each stage:
  - engine stores a stage event record (`qe_stage_event`) for lifecycle markers:
    - stage opened
    - stage closed
  - engine stores the StageOutcome returned by `build_outcome(trace)` into `qe_stage_outcome`
- No scoring is required in this sprint.

### G) Basic templates (mobile-first)
- Host page:
  - shows session code + QR
  - shows player list
  - has buttons: Start / Next / End
- Player page:
  - join form (nickname)
  - waiting screen
  - renders stage frames when received

### H) Guardrails
- All WS messages must follow the envelope:
  `{ "type": "EVENT_NAME", "payload": { ... } }`
- All plugin payloads must be JSON-like.
- Engine must remain dumb:
  - it routes events, stores traces, broadcasts frames
  - it does not interpret plugin payload meaning

---

## 3) Scope — EXCLUDED

- Scoring and ranking
- Timers and time limits (optional placeholders only)
- Player answer submission flow (unless required by a stage, but should be deferred)
- Moderation tools (kick/ban)
- Advanced auth hub integration beyond current authentication baseline

---

## 4) WebSocket Protocol (Minimal Set)

### Client → Server
- `CONNECT`
  - payload includes role and (for players) nickname
- `JOIN_SESSION`
  - payload includes nickname (player only)
- `LEAVE_SESSION`
- `HOST_START`
- `HOST_NEXT_STAGE`
- `HOST_END`

### Server → Client
- `SESSION_CREATED`
- `LOBBY_SNAPSHOT`
  - players list + session state
- `PLAYER_JOINED`
- `PLAYER_LEFT`
- `SESSION_STATE_CHANGED`
- `STAGE_CHANGED`
  - includes stage index/id
- `PLUGIN_FRAME`
  - broadcast frames from plugin runtime
- `ERROR`

All messages use the standard envelope.

---

## 5) Data Model Notes (qe_* only)

This sprint assumes the Sprint 1 tables exist and are usable:

- `qe_session`
- `qe_player`
- `qe_stage_event`
- `qe_stage_outcome`

Constraints:
- No foreign keys to external tables
- Only `qe_*` tables touched

---

## 6) Engine Runtime Flow

### Host starts session
1) Create session record
2) Initialize live state (in-memory)
3) Broadcast lobby snapshot

### Host starts running
1) Set state RUNNING
2) Set stage_index = 0
3) Open stage:
   - create plugin runtime
   - call on_stage_open
   - broadcast frames

### Host advances stage
1) Close current stage:
   - call build_outcome(trace)
   - persist outcome
2) Increment stage_index
3) If stage exists:
   - open next stage (same as above)
4) If no stage remains:
   - end session

### Host ends session
- Set state ENDED
- Close current stage if any (build outcome + persist)
- Broadcast state change

---

## 7) Files to Create / Modify

### Backend
- Create:
  - `quiz_engine/routers/host.py`
  - `quiz_engine/routers/join.py`
  - `quiz_engine/routers/ws.py`
  - `quiz_engine/services/session_live_service.py` (in-memory live state)
  - `quiz_engine/services/session_persist_service.py` (DB persistence helpers)
  - `quiz_engine/services/stage_orchestrator_service.py` (open/close stages)
- Modify:
  - plugin registry integration (load runtime by plugin_id)
  - existing quiz repository to fetch quiz payload by id

### Templates
- Create:
  - `quiz_engine/templates/host/session.html`
  - `quiz_engine/templates/player/join.html`
  - `quiz_engine/templates/player/session.html`

### Static JS
- Create:
  - `quiz_engine/static/js/ws_client.js` (shared WS helper)
  - `quiz_engine/static/js/host_session.js`
  - `quiz_engine/static/js/player_session.js`

---

## 8) Tests

### Unit tests
- session_code generation uniqueness and format
- live state transitions (LOBBY → RUNNING → ENDED)
- stage open/close orchestration calls plugin lifecycle correctly

### Integration tests
- create session from quiz
- join session (player)
- broadcast lobby snapshot
- host start triggers stage broadcast
- host next triggers stage advance and outcome persistence
- host end closes and persists final stage

---

## 9) Definition of Done (DoD)

- [ ] Host can start a session from a quiz and obtain a session_code
- [ ] Host screen shows QR + session_code
- [ ] Players can join via smartphone and appear in host list live
- [ ] Host can start, advance stages, and end session
- [ ] Current stage frames are broadcast in real-time to all clients
- [ ] Minimal stage lifecycle events and outcomes are persisted (`qe_stage_event`, `qe_stage_outcome`)
- [ ] System works behind Traefik HTTPS
- [ ] Tests and CI pass

---

## 10) Manual Validation Scenario

1) Login (dev mode acceptable)
2) Create or select a quiz with multiple stages
3) Click Start session → host screen shows QR + code
4) Join with 2 smartphones using QR
5) Host sees live player list updates
6) Host starts session → players see stage content
7) Host advances stages → players update in real-time
8) Host ends session → players see ended state
9) Verify DB contains session + stage events/outcomes

---

## 11) Exit Rule

Sprint 7 ends when:
- a real live session flow works end-to-end (host + players + real-time stages)
- plugin lifecycle is used to render stages via frames
- persistence records the minimal trace/outcome backbone
- CI is green and the feature is stable on mobile