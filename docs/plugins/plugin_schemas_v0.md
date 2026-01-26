# Plugin schemas V0 (plugin-side)

## Purpose
A plugin is standalone and owns all business logic:
- answer interpretation
- scoring rules (Kahoot-like speed, inverses, group effects)
- grading (0/1, /20, custom scales)
- reveal and visuals (frames)
- any multi-phase logic

quiz-engine is dumb:
- it transports StageContext, PlayerEvent, and PluginFrame
- it stores StageTrace and StageOutcome for replay
- it aggregates ScoreDelta by summing delta_score
- it does not interpret payloads

---

## JSON-only rule (hard requirement)
All plugin-produced payloads MUST be JSON-like:
- dict, list, str, int/float (finite), bool, null
No custom objects, bytes, sets, datetime objects, or decimals.

Datetimes at transport boundaries are ISO 8601 UTC strings.
Within plugin runtime you may use datetime objects, but you must serialize them when sending frames/outcomes.

---

## Runtime Models (what the plugin sees/returns)

### StageContext (engine -> plugin)
Fields (relevant):
- session_id: str
- quiz_id: str
- server_now: datetime (server truth)
- players: list[{player_id, display_name, metadata?}]
- stage:
  - stage_id: str
  - stage_index: int
  - plugin_id: str
  - stage_kind: str
  - engine_prompt: dict (engine-provided content; plugin may render it)
  - plugin_spec: dict (plugin config)
  - time_limit_ms?: int | null
  - random_seed?: int | null
- scoreboard_snapshot?: dict | null (engine totals; optional helper)
- plugin_state_in?: dict | null (replay/resume input)

Plugin rules:
- Treat server_now as the only reliable reference time.
- If you use randomness/bots: require stage.random_seed.

---

### PlayerEvent (clients -> engine -> plugin)
Fields (relevant):
- player_id: str
- type: str  # SUBMIT / CHANGE / CLEAR (minimum)
- server_received_at: datetime (server truth)
- payload: dict (opaque, defined by plugin)
- client_sent_at?: datetime | null (untrusted)
- seq?: int | null

Plugin rules:
- You may allow unlimited CHANGE events.
- Use server_received_at for all timing-based scoring.

---

### PluginFrame (plugin -> engine -> clients)
Fields:
- audience: "HOST" | "PLAYERS" | "ALL"
- frame_type: str (free naming, e.g. VIEW_MODEL, PATCH, REVEAL)
- payload: dict (opaque view-model)
- sent_at: datetime (should be server time; plugin can omit and let engine fill if offered)

Plugin rules:
- Frames are for live rendering (Mentimeter-like).
- Keep payload small; send aggregates not raw full traces.

---

### StageOutcome (plugin -> engine)
Fields:
- score_deltas?: list[{player_id, delta_score, meta?, reason?}] | null
- grade_deltas?: list[{player_id, value, max_value?, scale?, meta?}] | null
- plugin_state_out?: dict | null (for replay/resume)
- render_summary?: dict | null (optional final visuals data)
- next_hint?: dict | null (engine may ignore)

Plugin rules:
- score_deltas are optional (slides/wordcloud/scoreboards may send none)
- grade_deltas are optional (pedagogical mode)
- Engine will only sum delta_score; it will not validate your rules.

---

## Forbidden assumptions
- Do NOT assume all stages are MCQ or have 4 choices.
- Do NOT rely on client clock for fairness.
- Do NOT require DB access to engine tables; plugin must be self-contained.

---

## Consent and Privacy Rules

Plugins receive player consent information via PlayerIdentity.

Available consent flags:
- gameplay_identity: allows display and processing of the player's pseudo
  within the scope of gameplay (leaderboards, scoring, statistics).
- email_results: allows sending session results by email (authenticated users only).

Rules for plugins:
- If gameplay_identity is false:
  - the player must not participate in the stage
- If email_results is false:
  - the plugin must not request or expect email delivery
- Plugins must never attempt to infer identity or link guest players
  to authenticated accounts.
