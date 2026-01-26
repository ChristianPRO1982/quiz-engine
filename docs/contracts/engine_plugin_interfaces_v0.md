# Engine ↔ Plugin Interfaces V0 (quiz-engine only)

## Goal
Define stable Python interfaces in quiz-engine so plugins can be developed against runtime contracts.
quiz-engine remains dumb: it never interprets payloads or rules.

Plugins are loaded at startup. During a session, the active plugin handles a stage:
- receives StageContext
- receives PlayerEvent stream (from WS)
- optionally emits PluginFrame live (to WS)
- finally returns StageOutcome when done

---

## Mandatory Responsibilities in quiz-engine
1) Plugin registry: load manifests and provide plugin lookup by plugin_id.
2) Stage lifecycle: open stage, route player events, close stage, advance to next stage.
3) Trace store: persist StageTrace + outcomes for replay.
4) Score aggregation: sum ScoreDelta per player; store GradeDelta but do not compute meaning.
5) WS protocol:
   - receive PlayerEvent from clients
   - broadcast PluginFrame to clients (audience filtering)
   - broadcast stage lifecycle events (opened/closed)

---

## Python Interfaces (to implement inside quiz-engine)

### IPlugin
Minimal plugin API for quiz-engine.

Methods (no business logic in engine):
- get_manifest() -> PluginManifest
- create_runtime(session_id:str, stage:StageDefinition) -> IStageRuntime

Notes:
- plugin runtime must be deterministic if random_seed provided in stage definition.

---

### IStageRuntime
Runtime controller for one stage instance.

Lifecycle:
- on_stage_open(context:StageContext) -> list[PluginFrame] | None
- on_player_event(event:PlayerEvent, trace:StageTrace) -> list[PluginFrame] | None
- on_host_action(action:dict, trace:StageTrace) -> list[PluginFrame] | None
- is_finished(trace:StageTrace) -> bool
- build_outcome(trace:StageTrace) -> StageOutcome

Rules:
- quiz-engine calls is_finished to decide when to close automatically (time limit or plugin driven).
- plugin may also request close by emitting a PluginFrame or setting an internal flag; engine decides.
- build_outcome must be side-effect free and deterministic from (context + trace + plugin_state_in).

---

## Engine Event Routing Rules
- PlayerEvent is appended to StageTrace (append-only).
- Engine forwards the event to active stage runtime.
- Any PluginFrame returned is broadcast according to audience.
- Engine stores trace snapshots as needed (or store events and rebuild).

---

## Determinism Rules
- If a plugin uses random/bots, StageDefinition.random_seed MUST be set.
- Plugin must derive any randomness only from that seed.

---

## Validation Rules inside quiz-engine
- Validate all incoming WS payloads can be parsed into PlayerEvent.
- Reject non-JSON-like payload in PlayerEvent.payload and PluginFrame.payload.
- Enforce monotonic ordering: server_received_at is assigned by server.
- Optional: enforce per-player per-stage seq monotonic if seq is used.

---

## Persistence (quiz-engine only, no storage schema here)
Persist at minimum:
- session_id, quiz_id
- stages list (StageDefinition) for the session
- StageTrace events per stage
- StageOutcome per stage
- aggregated totals per player (score sum)

Replay requires:
- rebuilding StageContext (including plugin_state_in if needed)
- replaying StageTrace events in order
- letting plugin rebuild frames/outcome if desired

---

## WS Envelope Convention (transport)
All WS messages use:
{ "type": "EVENT_NAME", "payload": { ... } }

Recommended event names:
- ENGINE_STAGE_OPENED
- ENGINE_STAGE_CLOSED
- ENGINE_SCORE_UPDATE
- PLAYER_EVENT (client -> server)
- PLUGIN_FRAME (server -> clients)

Payloads must be JSON-only (no datetimes: use ISO 8601 strings).
