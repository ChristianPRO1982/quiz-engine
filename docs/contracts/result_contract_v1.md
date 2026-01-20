# Result Contract — v1

## Status

**DRAFT**

This contract defines the structure of results produced by plugins
and stored by the quiz-engine.

It is central to:
- score aggregation
- session replay
- statistics and visualization

The engine must never interpret result semantics.

---

## Purpose

A `QuestionResult` represents the **complete, final outcome of one question**
as produced by a plugin.

Results are:
- immutable once produced
- ordered in session history
- the only source of truth for post-session replay

---

## Core Principles

- Results are **plugin-owned**
- The engine stores and aggregates, but does not interpret
- All results must be JSON-serializable
- All numeric score impacts must be explicit

---

## QuestionResult (Top-Level Object)

Each question MUST produce exactly one `QuestionResult`.

Mandatory fields:

- `question_id`
- `plugin_id`
- `plugin_version`
- `schema_version`
- `timestamp`

Optional fields:

- `scoring_rule_id`
- `reveal_style_id`
- `metadata`
- `reveal_payload`

The engine must treat all optional fields as opaque.

---

## PlayerResult

Each `QuestionResult` MUST include a list of `PlayerResult` entries.

Each `PlayerResult` represents the impact of this question
on a single player.

Mandatory fields:

- `player_id`
- `delta_score`

Optional fields:

- `is_correct`
- `answer_summary`
- `details`

The engine must:
- aggregate `delta_score`
- ignore all other fields

---

## Score Aggregation Rule

The engine maintains a per-player score using the following rule:
```
total_score[player] = sum(delta_score for each QuestionResult)
```


The engine must not:
- clamp values
- apply weighting
- interpret correctness
- infer missing data

If a player has no `PlayerResult` for a question,
their `delta_score` is implicitly `0`.

---

## Reveal Payload

`reveal_payload` contains data required for result visualization.

This payload:
- is plugin-specific
- may contain layout or animation hints
- may contain aggregated statistics

The engine:
- transports the payload
- associates it with the question
- never interprets its contents

---

## Answer Summary

`answer_summary` MAY be provided for replay and statistics.

Examples:
- histogram of choices
- count of correct / incorrect answers
- distribution of response times

The structure is plugin-defined and opaque to the engine.

---

## Metadata

`metadata` MAY include:
- configuration echoes
- scoring parameters
- human-readable labels

Metadata must not be required for score computation.

---

## Immutability Rule

Once a `QuestionResult` is produced:
- it must not be modified
- it must not be recomputed
- it must not be partially updated

Corrections require producing a new result entry.

---

## Error Results

If a plugin fails during finalization:
- it must produce a structured error result
- the engine must store and broadcast the error
- partial or silent failures are forbidden

---

## Versioning

- `schema_version` identifies the result schema version
- Breaking changes require:
  - schema version bump
  - updated documentation
  - updated fixtures
  - updated tests

---

## Final Rule

> The engine remembers results.
> Plugins give them meaning.

