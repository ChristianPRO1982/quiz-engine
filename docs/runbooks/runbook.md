# Runbook — quiz-engine
Operational guide for engine runtime

Status: REFERENCE
Scope: Runtime operations only

Authoritative architecture:
- docs/PROJECT_CONTRACT.md
- docs/contracts/*

This runbook covers operational procedures.
It does not redefine contracts.

---

# 1. Runtime Overview

The engine:

- Manages sessions
- Orchestrates stages
- Routes WebSocket messages
- Persists StageOutcome and ScoreEntry
- Aggregates integer deltas mechanically

Plugins:

- Implement game logic
- Produce StageOutcome
- Produce ScoreEntry

---

# 1.1 Runtime vs Persistence Mapping

Runtime contracts describe API/runtime entities.
PostgreSQL uses persistence names in `qe.*` tables.

Canonical examples:

- Session `status` (runtime) ↔ `qe_session.state` (DB enum)
- Session `session_id` (runtime string id) ↔ `qe_session.session_code` (external code)
- Session internal PK ↔ `qe_session.id` (DB integer key)
- Player action stream ↔ `qe_stage_event` (`payload`, `created_at`, stage identifiers)
- StageOutcome (runtime) ↔ `qe_stage_outcome.payload` (stored JSON)
- ScoreEntry (runtime) ↔ `qe_score_entry` columns (`delta_score`, `grade_value`, `grade_max`, ...)

This mapping is operational guidance only.
Runtime contracts in `docs/contracts/*` remain authoritative.

---

# 2. Session Lifecycle Operations

## Create Session
POST /sessions

Result:
- status = LOBBY

---

## Start Session
POST /sessions/{session_id}/start

Result:
- status = RUNNING
- First stage activated

---

## Finish Session
POST /sessions/{session_id}/finish

Result:
- status = FINISHED

Engine does not compute winners.

---

# 3. Stage Runtime Operations

For each stage:

1. Engine instantiates plugin runtime
2. Engine calls initialize()
3. Engine routes PLAYER_ACTION
4. Engine triggers resolve()
5. Engine persists StageOutcome
6. Engine aggregates ScoreEntry

If resolve() fails:

- Mark stage FAILED
- Emit STAGE_ERROR
- Do not fabricate scoring

---

# 4. Snapshot Inspection

Snapshots represent:

- total_score per player
- total_grade_value per player
- total_grade_max per player

Snapshots are:

- Derived
- Integer-only
- Pure summations
- Not authoritative

No ranking must be inferred.

---

# 5. Common Operational Issues

## 5.1 Plugin Resolution Failure

Symptoms:
- STAGE_ERROR event
- Stage remains unresolved

Actions:
- Check plugin entrypoint
- Verify StageRuntime interface compliance
- Validate determinism constraints
- Trigger admin plugin scan (admin-only) to refresh catalog and registry

---

## 5.2 Non-Deterministic Behavior

Symptoms:
- Different StageOutcome for same seed
- Inconsistent scoring

Actions:
- Check random usage
- Ensure seed usage
- Remove time-based logic
- Remove external I/O from resolve()

---

## 5.3 Float-Based Scoring Detected

Symptoms:
- Validation failure
- StageOutcome rejected

Actions:
- Verify ScoreEntry integer-only rule
- Remove float accumulation
- Replace percentage with integer scale

---

## 5.4 Plugin Catalog Drift

Symptoms:
- Plugin appears in DB catalog but not on disk
- New plugin exists on disk but not shown in admin/UI

Actions:
- Login with an admin user
- Trigger Admin plugin scan
- Confirm sync result (added/updated/removed)
- Verify `qe_plugin_catalog` now matches filesystem plugins

Admin role provisioning (PostgreSQL):

```sql
SET search_path TO qe, public;
INSERT INTO qe_user_role (user_id, role)
VALUES (<user_id>, 'admin')
ON CONFLICT (user_id, role) DO NOTHING;
```

---

# 6. Data Integrity Rules

Never:

- Modify stored StageOutcome
- Recompute past scoring
- Re-run resolve() for resolved stage

StageOutcome is immutable.

---

# 7. Recovery Strategy

If engine crashes mid-stage:

- Restore session state
- Reload active stage
- Re-instantiate plugin
- Replay stored player actions from `qe_stage_event` in deterministic order (`created_at`, `id`)
- Call resolve()

Determinism guarantees consistency.

---

# 8. Logging Guidelines

Engine logs must include:

- session_id
- stage_id
- plugin_key
- lifecycle transitions
- error events

Engine logs must not:

- Log ranking decisions
- Log computed winners
- Log derived percentages

---

# 9. Operational Boundaries

Engine must not:

- Inject scoring corrections
- Adjust totals manually
- Modify ScoreEntry post-persistence

All scoring integrity belongs to plugin logic.

---

# 10. Future Extensions

Future runbook sections may include:

- Replay tooling
- Monitoring metrics
- Health checks
- Performance tuning

But must preserve:

- Dumb engine philosophy
- Integer-only scoring
- Deterministic runtime
