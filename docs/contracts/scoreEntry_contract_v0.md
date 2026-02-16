# ScoreEntry Contract — v1 (Strict Integer Edition)

## Purpose

Define the mandatory and strictly integer-based structure used by plugins
to report per-player scoring and grading at stage closure.

The engine:
- stores ScoreEntry objects as opaque JSON
- does NOT interpret or aggregate them
- does NOT compute ranking
- does NOT modify them

Score aggregation and interpretation belong to plugins (e.g., scoreboard plugin).

This version enforces integer-only scoring and grading.

---

# 1. Location in Runtime Flow

ScoreEntry objects are returned inside `StageOutcome`:

```json
{
  "score_entries": [ ScoreEntry, ... ],
  "render_summary": { ... },
  "plugin_state_out": { ... }
}
```

`score_entries` may be:

* a list of ScoreEntry
* or null (no scoring stage)

---

# 2. ScoreEntry Structure (Official — Strict)

```json
{
  "player_id": "string",
  "delta_score": 1000,
  "grade_value": 1,
  "grade_max": 1,
  "details": { ... }
}
```

---

# 3. Field Definitions

## 3.1 player_id (required)

* Stable session-level player identifier
* Must correspond to a known player in session
* Type: string

---

## 3.2 delta_score (required)

Represents the competitive score impact for this stage.

Type:

* INTEGER ONLY
* may be negative
* may be zero
* must be finite

Examples:

* 1000
* 850
* 0
* -200

Rules:

* No float allowed
* No decimal allowed
* Engine does not aggregate
* Interpretation belongs to scoring plugins

---

## 3.3 grade_value (required)

Represents pedagogical evaluation for this stage.

Type:

* INTEGER ONLY
* may be zero
* must be >= 0

Examples:

* 1
* 0
* 7
* 15

---

## 3.4 grade_max (required)

Represents maximum attainable grade for this stage.

Type:

* INTEGER ONLY
* must be >= grade_value
* must be > 0

Examples:

* 1
* 10
* 20
* 100

Purpose:
Allows later calculation of percentage:

grade_value / grade_max

Performed by scoring or analytics plugin, not engine.

---

## 3.5 details (optional)

Free-form JSON object for plugin-specific information.

Rules:

* JSON-only
* Informational only
* No engine interpretation
* No aggregation
* May contain strings, integers, booleans, arrays

Example:

```json
{
  "answer": "B",
  "good_answers": ["B", "C"],
  "timing_ms": 2230,
  "time_limit_ms": 10000,
  "phase": 2
}
```

details must not influence engine behavior.

---

# 4. Null Scoring Stage

If a stage has no scoring:

```json
{
  "score_entries": null,
  "render_summary": null,
  "plugin_state_out": null
}
```

---

# 5. Multiple Score Entries per Player

Allowed.

Example:

* multi-phase stage
* bonus + penalty
* partial credit + speed bonus

Engine stores entries as provided.
Interpretation delegated to scoring plugin.

---

# 6. Hard Constraints

## 6.1 Integer Only

The following fields MUST be integers:

* delta_score
* grade_value
* grade_max

Float values are forbidden.

If decimal precision is required in the future:

* Contract version must change
* Breaking change required

---

## 6.2 Deterministic

ScoreEntry must be reproducible from:

* StageContext
* StageTrace
* random_seed (if used)

---

## 6.3 No Hidden Engine Behavior

Engine MUST NOT:

* sum scores
* compute ranking
* normalize grades
* calculate percentages
* infer ties
* apply tie-breakers

All interpretation belongs to plugins.

---

# 7. Design Philosophy

ScoreEntry separates:

* Competitive scoring (delta_score)
* Pedagogical grading (grade_value / grade_max)
* Detailed justification (details)

Integer-only enforcement ensures:

* Predictable ranking
* Stable replay
* Deterministic aggregation
* Simpler frontend handling
* Easier analytics

Engine remains stable.
Plugins remain powerful.
Complexity scales in plugins, not in engine.
