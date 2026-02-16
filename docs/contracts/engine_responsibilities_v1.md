# Engine Responsibilities — v1
Authoritative definition of engine scope

Status: CANONICAL
Schema version: v1
Scope: Runtime orchestration layer

This document defines what the engine MUST and MUST NOT do.

Data models:
- docs/contracts/runtime_schema_v1.md
- docs/contracts/scoreEntry_contract_v1.md

Flow model:
- docs/contracts/runtime_plugin_io_v1.md

---

# 1. Core Philosophy

The engine is intentionally dumb.

It orchestrates execution.
It does not contain business logic.

Plugins define:
- game rules
- scoring rules
- grading logic
- determinism
- resolution logic

The engine executes.

---

# 2. Engine Responsibilities (Mandatory)

## 2.1 Session Management

The engine must:

- Create sessions
- Transition session states:
  - LOBBY
  - RUNNING
  - FINISHED
- Persist session lifecycle timestamps

The engine does not decide game outcome.

---

## 2.2 Player Management

The engine must:

- Register players
- Track active/inactive status
- Associate players to sessions

The engine does not score players.

---

## 2.3 Stage Orchestration

The engine must:

- Create stages
- Assign plugin_key
- Provide seed
- Activate stages
- Trigger resolution
- Persist StageOutcome

The engine does not compute resolution logic.

---

## 2.4 Plugin Invocation

The engine must:

- Resolve plugin by plugin_key
- Initialize plugin with:
  - config
  - seed
  - player list
- Route player actions to plugin
- Call resolve()

The engine must not alter plugin state.

---

## 2.5 WebSocket Routing

The engine must:

- Accept client messages
- Validate session/stage ownership
- Forward actions to plugin
- Broadcast plugin outputs
- Emit host snapshots

The engine must not interpret payload semantics.

---

## 2.6 ScoreEntry Persistence

The engine must:

- Persist ScoreEntry objects
- Keep them immutable
- Aggregate delta_score mechanically

Aggregation rules are defined in:
docs/contracts/scoreEntry_contract_v1.md

The engine must not:
- Apply multipliers
- Normalize scores
- Convert grades
- Rank players
- Decide winners

---

## 2.7 Snapshot Aggregation (Mechanical Only)

The engine may compute derived snapshots:

- total_score per player
- total_grade_value per player
- total_grade_max per player

Snapshots must:

- Be integer-only
- Be pure summations
- Not contain ranking logic
- Not contain percentages

Snapshots are non-authoritative views.

---

## 2.8 Persistence Layer

The engine must:

- Persist sessions
- Persist players
- Persist stages
- Persist StageOutcome
- Persist ScoreEntry

The engine must not:

- Recompute past outcomes
- Re-open resolved stages
- Mutate stored outcomes

---

# 3. Explicit Non-Responsibilities

The engine must never:

- Contain scoring formulas
- Contain grading formulas
- Render HTML
- Decide UI behavior
- Render Host UI
- Render Player UI
- Define Host UI behavior
- Define Player UI behavior
- Implement game mechanics
- Apply time-based bonuses
- Interpret correctness
- Resolve ties
- Determine podiums
- Calculate percentages
- Apply difficulty modifiers

All such logic belongs to plugins.

---

# 4. Determinism Enforcement

The engine must:

- Provide seed to plugins
- Avoid injecting randomness
- Ensure replay reproducibility

The engine must not:

- Add randomization
- Inject timestamps into scoring
- Modify StageOutcome

---

# 5. Failure Handling

If plugin resolution fails:

- Mark stage as FAILED
- Emit STAGE_ERROR
- Do not fabricate scoring

The engine must not attempt recovery scoring.

---

# 6. Security Boundary

The engine enforces:

- Session isolation
- Stage ownership
- Player identity

The engine does not validate:
- correctness of answers
- scoring fairness
- plugin business rules

---

# 7. Authority Hierarchy

Global contract hierarchy is defined in:

docs/contracts/README.md (section: Contract Hierarchy)

For this document scope:
runtime_schema_v1.md prevails for data,
scoreEntry_contract_v1.md prevails for scoring.

---

# 8. Future Extensions

Future versions may introduce:

- audit trails
- replay modes
- monitoring hooks

But must preserve:

- Dumb engine philosophy
- Integer-only scoring
- Plugin-owned business logic
