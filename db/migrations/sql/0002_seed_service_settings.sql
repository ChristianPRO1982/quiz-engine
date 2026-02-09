-- 0002_seed_service_settings.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

INSERT INTO qe_service_setting (key, value)
VALUES ('CONSENT_REVIEW_MONTHS', '6')
ON CONFLICT (key) DO NOTHING;

INSERT INTO qe_schema_migration (version, description)
VALUES ('0002_seed_service_settings', 'Seed default service settings')
ON CONFLICT (version) DO NOTHING;

COMMIT;
