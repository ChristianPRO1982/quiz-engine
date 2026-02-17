-- 0006_add_runtime_session_stage_and_score_entry.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

ALTER TABLE qe_session
    ADD COLUMN IF NOT EXISTS current_stage_index INTEGER,
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS qe_stage (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    stage_id VARCHAR(64) NOT NULL,
    plugin_key VARCHAR(64) NOT NULL,
    stage_index INTEGER NOT NULL,
    config JSON NOT NULL DEFAULT '{}'::json,
    seed INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    failed_at TIMESTAMPTZ,
    CONSTRAINT uq_qe_stage_session_stage_id UNIQUE (session_id, stage_id),
    CONSTRAINT uq_qe_stage_session_stage_index UNIQUE (session_id, stage_index),
    CONSTRAINT ck_qe_stage_status
        CHECK (status IN ('PENDING', 'ACTIVE', 'RESOLVED', 'FAILED'))
);

CREATE INDEX IF NOT EXISTS ix_qe_stage_session_id
    ON qe_stage (session_id);

CREATE TABLE IF NOT EXISTS qe_score_entry (
    id BIGSERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    stage_id VARCHAR(64) NOT NULL,
    stage_index INTEGER NOT NULL,
    player_id VARCHAR(64) NOT NULL,
    schema_version VARCHAR(16) NOT NULL DEFAULT 'v1',
    delta_score INTEGER,
    grade_value INTEGER,
    grade_max INTEGER,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_qe_score_entry_schema_version
        CHECK (schema_version = 'v1'),
    CONSTRAINT ck_qe_score_entry_presence
        CHECK (delta_score IS NOT NULL OR grade_value IS NOT NULL),
    CONSTRAINT ck_qe_score_entry_grade_pair
        CHECK (
            (grade_value IS NULL AND grade_max IS NULL)
            OR (grade_value IS NOT NULL AND grade_max IS NOT NULL)
        ),
    CONSTRAINT ck_qe_score_entry_grade_bounds
        CHECK (
            grade_value IS NULL
            OR (grade_value >= 0 AND grade_max >= 0 AND grade_value <= grade_max)
        )
);

CREATE INDEX IF NOT EXISTS ix_qe_score_entry_session_id
    ON qe_score_entry (session_id);

CREATE INDEX IF NOT EXISTS ix_qe_score_entry_session_stage_index
    ON qe_score_entry (session_id, stage_index);

CREATE INDEX IF NOT EXISTS ix_qe_score_entry_player_id
    ON qe_score_entry (player_id);

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0006_add_runtime_session_stage_and_score_entry',
    'Add session started_at/current_stage_index and explicit qe_stage/qe_score_entry persistence'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
