# Plugin Lifecycle V0

## High level
A stage is driven by one plugin runtime instance.

Engine flow:
1) engine selects StageDefinition
2) engine calls plugin.create_runtime(session_id, stage_definition)
3) engine calls runtime.on_stage_open(stage_context)
4) during stage:
   - engine receives PlayerEvent via WS
   - engine appends to StageTrace
   - engine calls runtime.on_player_event(event, trace)
   - engine broadcasts returned PluginFrames
5) engine closes stage when:
   - time limit elapsed OR
   - runtime.is_finished(trace) == True OR
   - host ends the quiz OR
   - plugin asks to close (via frames or internal flag; engine decides)
6) engine calls runtime.build_outcome(trace) and stores StageOutcome

---

## Interface expectations

### create_runtime(session_id, stage_definition)
- Should be deterministic given stage_definition (and random_seed if used)
- Should set up internal state for the stage

### on_stage_open(context) -> frames?
- Optional: send initial frames (prompt, layout, initial chart, etc.)

### on_player_event(event, trace) -> frames?
- May send live updates:
  - Mentimeter-like charts
  - "chaos" live tallies
  - gauges
  - progressive reveal changes

### on_host_action(action, trace) -> frames?
- Optional: host controls (reveal, next phase, lock answers, etc.)
- action payload is plugin-defined JSON-like

### is_finished(trace) -> bool
- For single-phase questions: often True after first submit per player AND close condition
- For multi-phase: False until phase transitions complete
- Engine may still close early if host stops the quiz

### build_outcome(trace) -> StageOutcome
- Must be deterministic from:
  - StageContext (including plugin_spec/random_seed)
  - StageTrace
  - plugin_state_in
- Must not depend on wall-clock or external side effects
- May produce:
  - score_deltas (game points)
  - grade_deltas (pedagogical grade)
  - render_summary (final chart / wordcloud results)
  - plugin_state_out (if stage has internal phases/resume)

---

## Multi-phase guidance (Dixit, progressive reveal, etc.)
Two valid patterns:

### Pattern A — Single stage, internal phases
- Use frames to change the UI across phases
- Use plugin_state_out to store phase state for replay
- Keep same stage_id and stage_index

### Pattern B — Multiple stages chained
- Split phases into separate StageDefinitions (submit -> vote -> reveal)
- Easier for engine replay and simpler runtime state

Pick A when you need "one question evolving".
Pick B when phases are conceptually different stages.
