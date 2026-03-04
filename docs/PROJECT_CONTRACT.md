# PROJECT CONTRACT — quiz-engine
Architectural constitution of the project

Status: CANONICAL
Scope: Entire repository

This document defines the non-negotiable principles of quiz-engine.

Detailed technical contracts are defined in:
- docs/contracts/*
- docs/CODEX_RULES.md

Plugin discovery and catalog synchronization are defined in:
- docs/contracts/plugin_catalog_sync_contract_v1.md

If a contradiction appears, contracts prevail.

---

# 1. Project Philosophy

quiz-engine is built around one core idea:

The engine is dumb.
Plugins are smart.

The engine orchestrates.
Plugins implement game logic.

This separation is absolute.

---

# 2. Engine Responsibilities (High-Level)

The engine manages:

- Sessions
- Players
- Stages
- WebSocket routing
- Persistence
- Mechanical aggregation of integer score deltas
- Host overlay snapshots

The engine does NOT:

- Compute scoring logic
- Interpret answers
- Rank players
- Decide winners
- Apply grading formulas
- Render UI
- Define Host UI behavior
- Define Player UI behavior
- Implement game mechanics

All business logic belongs to plugins.

---

# 3. Plugin Responsibilities

Plugins are responsible for:

- Game rules
- Stage logic
- Player action interpretation
- Host UI behavior
- Player UI behavior
- Scoring logic
- Grading logic
- Determinism
- Stage resolution
- Producing ScoreEntry
- Defining stage authoring contract metadata
  (`stage_config_schema`, `default_stage_config`)

Plugins must:

- Be deterministic
- Use provided seed
- Produce integer-only scoring
- Return valid StageOutcome
- Declare a general plugin type for cataloging (`info`, `quiz`, `scoreboard`, `form`)

Plugins must not:

- Modify session lifecycle
- Access engine persistence
- Introduce floats in scoring

---

# 4. Scoring Model

Scoring is defined by:

docs/contracts/scoreEntry_contract_v1.md

Rules:

- Integer-only
- No floats
- No percentages
- No ranking inside engine
- Engine aggregates mechanically only

Ranking, if needed, must be implemented at plugin level
or in external presentation layers.

---

# 5. Runtime Model

Runtime structures are defined in:

docs/contracts/runtime_schema_v1.md

WebSocket interaction is defined in:

docs/contracts/runtime_plugin_io_v1.md

These contracts are authoritative.

Plugin manifest evolution and plugin catalog synchronization are defined in:

- docs/contracts/plugin_manifest_contract_v2.md
- docs/contracts/plugin_catalog_sync_contract_v1.md

---

# 6. Determinism Guarantee

Given identical:

- Stage configuration
- Seed
- Player actions

The plugin must produce identical StageOutcome.

The engine must not inject randomness.

Determinism is mandatory.

---

# 7. Architectural Boundaries

The following must never occur:

- Business logic inside engine
- Scoring formulas inside engine
- Ranking logic inside engine
- Float-based scoring anywhere
- Duplicate runtime schemas
- Alternative WebSocket envelopes
- Plugin-specific hardcoded authoring behavior inside engine/editor
  (for example `if question.type == "slide"`)

All runtime communication must follow:

{
  "type": "EVENT_NAME",
  "payload": { ... }
}

---

# 8. Contract-Driven Development

All changes must follow this order:

1. Update contract in docs/contracts/
2. Review architectural impact
3. Update implementation
4. Update tests

Code must never drift from contracts.

Contracts are the source of truth.

---

# 9. Small-Scale Target

quiz-engine targets:

- 10–80 concurrent players
- Smartphone-first experience
- QR-based joining
- Real-time interaction
- Post-session replay / review

It is not designed for massive scale.

Simplicity > premature optimization.

---

# 10. Long-Term Stability

Future evolution must preserve:

- Dumb engine philosophy
- Plugin-owned business logic
- Integer-only scoring
- Deterministic execution
- Contract-driven architecture

Breaking these principles breaks the project.

---

# 11. Authority Hierarchy

The canonical authority hierarchy is defined in:

docs/contracts/README.md (section: Contract Hierarchy)

In case of ambiguity, apply that hierarchy exactly.

PROJECT_CONTRACT.md defines philosophy and guardrails.
Contracts in docs/contracts/* define runtime structure.

---

# 12. Architecture Freeze (v1)

Runtime contracts under schema_version "v1" are frozen.

No structural change is allowed without:
- creating a new schema_version (v2, v3, ...)
- keeping v1 documents unchanged (archived but still readable)
- updating documentation before code

Guidance documents (docs/plugins/*, docs/runbooks/*) may evolve
without a schema_version bump, as long as they do not redefine contracts.
