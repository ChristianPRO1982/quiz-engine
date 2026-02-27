-- 0010_add_plugin_catalog_table.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

CREATE TABLE IF NOT EXISTS qe_plugin_catalog (
    id SERIAL PRIMARY KEY,
    plugin_id VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    plugin_version VARCHAR(64) NOT NULL,
    plugin_type VARCHAR(32) NOT NULL,
    manifest_payload JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_qe_plugin_catalog_plugin_type
ON qe_plugin_catalog (plugin_type);

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0010_add_plugin_catalog_table',
    'Add persisted plugin catalog for discovery/synchronization'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
