# Runtime schemas V0 (quiz-engine only)

## Goal
quiz-engine is "dumb": it orchestrates stages and transports state, but it never interprets answers nor computes rules.
Plugins own all business logic (scoring, grading, reveal, visuals). quiz-engine only provides:
- stage lifecycle (open/run/close)
- WS transport for player events and plugin frames
- trace persistence for replay
- score aggregation from deltas (sum only)

All runtime objects MUST be serializable (JSON-like). Datetimes are ISO 8601 UTC strings at transport boundaries.

---

## Core Concepts
- A quiz is a list of **stages**.
- A stage is driven by a **plugin** (question, slide, scoreboard, wordcloud, etc.).
- Players emit **events** (submit/change/clear...) with opaque payload.
- Plugins may emit **frames** (live UI view-model) during the stage.
- A plugin returns a **stage outcome** when it yields control.

---

## Runtime Models (Python OOP)

### PluginManifest
Describes a plugin known by quiz-engine at boot time.

Fields:
- required: plugin_id:str, plugin_version:str, display_name:str, schema_version:str
- optional: description:str|None, capabilities:dict

Invariants:
- plugin_id unique and stable
- schema_version == "v0"

---

### StageDefinition
One item of a quiz, driven by a plugin.

Fields:
- required:
  - stage_id:str
  - stage_index:int
  - plugin_id:str
  - stage_kind:str
  - engine_prompt:dict   # engine-provided prompt when available (never interpreted at runtime)
  - plugin_spec:dict     # plugin-owned config
- optional:
  - time_limit_ms:int|None
  - random_seed:int|None  # required if plugin uses randomness/bots
  - metadata:dict

Invariants:
- stage_index >= 0
- engine_prompt and plugin_spec are JSON-like

---

### PlayerIdentity

Represents a player participating in a session.
A player may be authenticated via a central auth hub, but can still participate
in quiz-engine either as a logged player or as a guest.

Fields:
- required:
  - player_id: str
  - display_name: str
- optional:
  - is_authenticated: bool
  - participation_mode: "LOGGED" | "GUEST"
  - consents: dict
      - gameplay_identity: bool
      - email_results: bool
  - metadata: dict

Invariants:
- gameplay_identity consent is required to participate in a session.
- If is_authenticated is false:
  - participation_mode MUST be "GUEST"
  - email_results MUST be false or absent
- If participation_mode is "GUEST":
  - email_results MUST be false or absent
- email_results is meaningful only when is_authenticated is true.

---

### StageContext
Given to plugins when a stage starts.

Fields:
- required:
  - session_id:str
  - quiz_id:str
  - stage:StageDefinition
  - server_now:datetime
  - players:list[PlayerIdentity]
- optional:
  - scoreboard_snapshot:dict|None   # engine aggregated totals only
  - plugin_state_in:dict|None       # replay/continuation input
  - transport_hints:dict|None
  - session_flags:dict|None

Invariants:
- server_now comes from server clock

Notes:
- PlayerIdentity.consents MUST be passed to plugins as-is.
- The engine does not interpret consent values, but plugins must respect them
  (e.g. exclude from scoring, anonymize display, disable email features).

---

### PlayerEvent
Append-only timeline event from a player.

Fields:
- required:
  - event_id:str
  - session_id:str
  - stage_id:str
  - stage_index:int
  - player_id:str
  - type:str            # at least: SUBMIT / CHANGE / CLEAR
  - server_received_at:datetime
  - payload:dict        # opaque plugin-owned
- optional:
  - client_sent_at:datetime|None
  - seq:int|None
  - correlation_id:str|None

Invariants:
- append-only
- payload is JSON-like
- order by server_received_at (or seq if present)

---

### StageTrace
Timeline of a stage (all player events + engine events).

Fields:
- required:
  - session_id:str
  - stage_id:str
  - stage_index:int
  - started_at:datetime
  - events:list[PlayerEvent]
- optional:
  - ended_at:datetime|None
  - engine_events:list[dict]|None

Invariants:
- ids consistent for all contained events

---

### PluginFrame
Live render payload emitted by plugins (mentimeter-like, chaos live, reveal progressive, etc.).

Fields:
- required:
  - session_id:str
  - stage_id:str
  - stage_index:int
  - plugin_id:str
  - audience:str        # HOST / PLAYERS / ALL
  - frame_type:str      # VIEW_MODEL / PATCH / REVEAL / etc.
  - payload:dict        # opaque view-model
  - sent_at:datetime
- optional:
  - seq:int|None

Invariants:
- payload JSON-like
- sent_at server clock

---

### ScoreDelta
Only thing quiz-engine aggregates.

Fields:
- required: player_id:str, delta_score:float
- optional: meta:dict|None, reason:str|None

Invariants:
- delta_score is finite number

---

### GradeDelta
Optional pedagogical grade (independent from score).

Fields:
- required: player_id:str, value:float
- optional: max_value:float|None, scale:str|None, meta:dict|None

Invariants:
- if max_value is set, it must be > 0

---

### StageOutcome
Returned when plugin yields control.

Fields:
- required:
  - session_id:str
  - stage_id:str
  - stage_index:int
  - plugin_id:str
  - completed_at:datetime
- optional:
  - score_deltas:list[ScoreDelta]|None
  - grade_deltas:list[GradeDelta]|None
  - plugin_state_out:dict|None
  - render_summary:dict|None
  - attachments:dict|None
  - next_hint:dict|None

Invariants:
- score/grade are optional (slides/wordcloud/scoreboards may not provide them)
- all optional dict payloads are JSON-like

---

## Engine-readable vs Plugin-owned
Engine-readable:
- ids: session_id, quiz_id, stage_id, stage_index, plugin_id, stage_kind
- timestamps: server_now, started_at, ended_at, completed_at, server_received_at, sent_at
- scoring: ScoreDelta.delta_score (sum only), GradeDelta stored only
- transport: audience, frame_type

Plugin-owned opaque:
- StageDefinition.plugin_spec
- StageDefinition.engine_prompt (transport only at runtime)
- PlayerEvent.payload
- PluginFrame.payload
- plugin_state_in/out, render_summary, attachments, meta/metadata

---

## Serialization Rules
- At WS/HTTP boundaries, all models must serialize to JSON.
- datetime -> ISO 8601 UTC string.
- All "opaque" dicts must be JSON-like (no custom objects).
- Add top-level schema_version="v0" in transport envelopes when needed.
