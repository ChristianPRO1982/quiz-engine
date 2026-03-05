# ScoreEntry Contract — v1
Authoritative scoring structure for quiz-engine runtime

Status: CANONICAL
Schema version: v1
Scope: Runtime (Engine ↔ Plugin)

---

# 1. Purpose

ScoreEntry is the only structure allowed for scoring or grading effects
produced by plugins during stage resolution.

The engine does not compute scores.
The engine only stores and aggregates integer deltas without interpretation.

ScoreEntry is strictly integer-only.

No floats.
No percentages.
No derived values.

---

# 2. Design Principles

- Deterministic
- Integer-only
- Append-only (immutable once emitted)
- Plugin-owned semantics
- Engine-agnostic

The engine must never interpret the meaning of a score.
It only aggregates integer deltas per player.

---

# 3. Schema Definition

```json
{
  "schema_version": "v1",
  "player_id": "string",
  "delta_score": "integer | null",
  "grade_value": "integer | null",
  "grade_max": "integer | null",
  "reason": "string | null"
}
```

---

# 4. Field Semantics

### player_id (required)

Unique identifier of the player affected.

### delta_score (optional)

Signed integer.
Represents a change in total score.

Examples:

* +10
* -5
* 0

If null → no score change.

---

### grade_value (optional)

Integer grade value awarded for this stage.

Must be used with `grade_max`.

Example:
5 (out of 10)

---

### grade_max (optional)

Maximum possible grade value.

Must be used with `grade_value`.

Example:
10

---

### reason (optional)

Human-readable explanation.
For logging, debugging, or UI display.

The engine does not parse this field.

---

# 5. Validation Rules

1. At least one of:

   * delta_score
   * grade_value

   must be non-null.

2. If grade_value is present:

   * grade_max must also be present
   * grade_value must be <= grade_max
   * both must be >= 0

3. delta_score may be negative.

4. All numeric values must be integers.

---

# 6. Engine Responsibilities

The engine may:

* Persist ScoreEntry
* Aggregate delta_score per player
* Expose total_score snapshot
* Expose total_grade_value and total_grade_max snapshots (pure summation only)

The engine must not:

* Rank players
* Apply multipliers
* Normalize grades
* Convert to percentages
* Compute business logic

---

# 7. Aggregation Model

Engine aggregation is purely mechanical:

total_score[player] = SUM(delta_score)

total_grade_value[player] = SUM(grade_value)
total_grade_max[player] = SUM(grade_max)

No additional transformation allowed.

---

# 8. Determinism

ScoreEntry must be fully deterministic.

Given:

* same stage config
* same seed
* same player inputs

The plugin must produce identical ScoreEntry output.

---

# 9. Non-Goals

ScoreEntry is NOT:

* A ranking system
* A leaderboard definition
* A percentage calculation
* A UI artifact
* A float-based metric

---

# 10. Future Extensions

Future versions may introduce:

* category scoring
* multi-axis grading
* tagging

But must remain integer-only.

---

# 🎯 Definition of Done

This file becomes:

- The single source of truth for scoring
- Referenced by `runtime_schema`
- Used by `StageOutcome`
- Aligned with the "engine dumb" principle
- Float-free
- Without concurrent `ScoreDelta`
