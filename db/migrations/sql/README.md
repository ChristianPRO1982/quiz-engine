# SQL Migrations (manual)

These migrations are designed to be run manually by a PostgreSQL administrator.

## Files order

1. `0001_create_qe_core_tables.sql`
2. `0002_seed_service_settings.sql`
3. `0003_replace_answer_result_with_stage_event_outcome.sql`
4. `0004_normalize_slide_markdown_payloads.sql`
5. `0005_rename_session_state_ended_to_finished.sql`
6. `0006_add_runtime_session_stage_and_score_entry.sql`
7. `0007_enforce_stage_outcome_immutability.sql`

## Tracking table

Each migration inserts one row in `qe.qe_schema_migration` (or `qe_schema_migration` with `search_path=qe,public`) so you can audit:

- which migration was applied,
- when,
- by which DB user.

Notes:

- `db/audit/*.md` are DB snapshot exports and may lag behind files listed above.
- Re-run the audit queries after applying pending migrations to refresh `db/audit/qe_schema_migration.rows.md`.
- Current repository snapshot has been refreshed on 2026-02-17 and includes migrations up to `0007_enforce_stage_outcome_immutability`.

## Status query

```sql
SET search_path TO qe, public;
SELECT version, applied_at, applied_by
FROM qe_schema_migration
ORDER BY applied_at, id;
```
