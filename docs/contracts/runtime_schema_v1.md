# Runtime Schema — v1
Authoritative runtime data structures for quiz-engine

Status: CANONICAL
Schema version: v1
Scope: Engine ↔ Plugin runtime contract

This document defines runtime data models only.
Scoring rules are defined in:
docs/contracts/scoreEntry_contract_v1.md

---

# 1. Design Principles

- Engine is dumb
- Plugins own all business logic
- Deterministic execution
- Immutable stage outcomes
- Integer-only scoring (via ScoreEntry)

---

# 2. Core Runtime Concepts

The runtime operates on:

- Session
- Player
- Stage
- StageOutcome
- ScoreEntry (external canonical reference)

Versioned payload structures in v1 are:

- StageOutcome
- ScoreEntry

Session, Player, and Stage are runtime entities
and do not include a schema_version field.

The engine orchestrates.
Plugins decide.

---

# 3. Session

```json
{
  "session_id": "string",
  "quiz_id": "string",
  "status": "LOBBY | RUNNING | FINISHED",
  "current_stage_index": "integer | null",
  "created_at": "timestamp",
  "started_at": "timestamp | null",
  "ended_at": "timestamp | null"
}
````

The engine manages lifecycle transitions.
Plugins do not control session state directly.

---

# 4. Player

```json
{
  "player_id": "string",
  "session_id": "string",
  "display_name": "string",
  "joined_at": "timestamp",
  "is_active": "boolean"
}
```

Players are session-scoped.
Engine owns player lifecycle.

---

# 5. Stage

A Stage represents one plugin execution unit.

```json
{
  "stage_id": "string",
  "session_id": "string",
  "plugin_key": "string",
  "stage_index": "integer",
  "config": "object",
  "seed": "integer",
  "status": "PENDING | ACTIVE | RESOLVED | FAILED"
}
```

Rules:

* `plugin_key` maps to a registered plugin.
* `config` is plugin-defined.
* `seed` must be used for deterministic behavior.
* Engine transitions status.
* `FAILED` means plugin/runtime error; no scoring recovery is allowed.

---

# 6. StageOutcome

StageOutcome is produced by the plugin
when the stage is resolved.

```json
{
  "schema_version": "v1",
  "stage_id": "string",
  "plugin_key": "string",
  "finished_at": "timestamp",
  "public_state": "object | null",
  "private_state": "object | null",
  "score_entries": "ScoreEntry[] | null",
  "metadata": "object | null"
}
```

---

# 7. StageOutcome Field Semantics

### stage_id

Must match the originating stage.

### plugin_key

Must match the stage plugin.

### public_state

State safe to broadcast to all players.

Example:

* correct answer
* statistics
* revealed values

Engine does not interpret content.

---

### private_state

Optional state visible only to host/admin.

Example:

* debugging info
* grading details
* hidden explanations

Engine does not interpret content.

---

### score_entries

List of ScoreEntry objects.

Definition:
docs/contracts/scoreEntry_contract_v1.md

Rules:

* May be null
* Must be deterministic
* Must contain only integer values
* Engine must not modify entries

---

### metadata

Optional plugin-defined information.
Engine stores but does not interpret.

---

# 8. Engine Snapshots (Derived, Not Authoritative)

The engine may maintain derived runtime snapshots:

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

These values are:

* Derived from ScoreEntry aggregation
* Not stored inside StageOutcome
* Not authoritative business logic
* Never interpreted beyond summation

Plugins remain source of truth for scoring semantics.

---

# 9. Determinism Requirements

For a given:

* Stage config
* Seed
* Player inputs

The plugin must produce identical:

* public_state
* private_state
* score_entries

Engine must never introduce randomness.

---

# 10. Explicit Non-Responsibilities of Engine

The engine must not:

* Rank players
* Compute percentages
* Apply multipliers
* Interpret grading scales
* Modify score_entries
* Inject scoring logic

---

# 11. Invariants

* All scoring is integer-only
* StageOutcome is immutable once stored
* Engine orchestration is state-machine based
* Plugin logic must be pure relative to input + seed

---

# 12. Future Versioning

Future versions may extend:

* Stage phases
* Snapshot structures
* Metadata formats

But must not break integer-only scoring.
