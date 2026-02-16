# Codex Task List — quiz-engine
AI-safe development roadmap

Status: CANONICAL
Scope: Engine + Plugins evolution

All tasks must comply with:

- docs/CODEX_RULES.md
- docs/contracts/*

The engine is dumb.
Plugins own business logic.
Scoring is integer-only.

---

# Phase 1 — Core Runtime (Engine)

## 1. Session Lifecycle
- Implement session creation
- Implement state transitions:
  - LOBBY → RUNNING → FINISHED
- Persist timestamps

## 2. Player Management
- Register players
- Track active/inactive status
- Associate players with session

## 3. Stage Orchestration
- Create stages
- Assign plugin_key
- Provide deterministic seed
- Activate stage
- Trigger resolve()
- Persist StageOutcome

## 4. ScoreEntry Persistence
- Store ScoreEntry
- Aggregate delta_score mechanically
- Expose snapshot totals
- Do not implement ranking

---

# Phase 2 — WebSocket Runtime

## 5. WS Envelope
- Enforce { type, payload } structure
- Reject malformed messages

## 6. Action Routing
- Validate session/stage ownership
- Forward PLAYER_ACTION to plugin
- Do not interpret action content

## 7. Broadcast Flow
- STAGE_STARTED
- STAGE_UPDATE
- STAGE_RESOLVED
- STAGE_ERROR
- HOST_SNAPSHOT

No alternative envelope allowed.

---

# Phase 3 — Plugin System

## 8. Plugin Registration
- Map plugin_key → plugin class
- Enforce StageRuntime interface

## 9. Determinism Enforcement
- Provide seed to plugin
- Prevent engine-side randomness

## 10. StageOutcome Validation
- Validate structure
- Validate integer-only scoring
- Reject float values

---

# Phase 4 — Safety & Integrity

## 11. Contract Validation
- Ensure runtime_schema compliance
- Ensure ScoreEntry compliance

## 12. Snapshot Integrity
- Ensure pure summation aggregation
- Prevent ranking logic

## 13. Immutability
- Prevent modification of stored StageOutcome
- Prevent re-resolution of stages

---

# Phase 5 — Example Plugins

## 14. Minimal QCM Plugin
- Deterministic scoring
- Integer-only ScoreEntry

## 15. Zero-Score Informational Plugin
- No scoring
- Only public_state

---

# Explicit Non-Tasks

The following must never be implemented in the engine:

- Leaderboard ranking
- Podium calculation
- Percentage calculation
- Float-based scoring
- Business rule interpretation
- Game mechanics

All such logic belongs to plugins.

---

# Stability Rule

If a task requires modifying:

- StageOutcome structure
- ScoreEntry structure
- Engine responsibilities

The change must be made in contracts first,
then implemented in code.

Never modify code without updating contracts.
