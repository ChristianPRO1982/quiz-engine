# SQL Migrations (manual)

These migrations are designed to be run manually by a PostgreSQL administrator.

## Files order

1. `0001_create_qe_core_tables.sql`
2. `0002_seed_service_settings.sql`
3. `0003_replace_answer_result_with_stage_event_outcome.sql`
4. `0004_normalize_slide_markdown_payloads.sql`

## Tracking table

Each migration inserts one row in `qe.qe_schema_migration` (or `qe_schema_migration` with `search_path=qe,public`) so you can audit:

- which migration was applied,
- when,
- by which DB user.

## Status query

```sql
SET search_path TO qe, public;
SELECT version, applied_at, applied_by
FROM qe_schema_migration
ORDER BY applied_at, id;
```
