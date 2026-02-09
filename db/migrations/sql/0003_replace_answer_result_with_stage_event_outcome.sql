-- 0003_replace_answer_result_with_stage_event_outcome.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

CREATE TABLE IF NOT EXISTS qe_stage_event (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    stage_id VARCHAR(64) NOT NULL,
    stage_index INTEGER NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_qe_stage_event_session_id ON qe_stage_event (session_id);

CREATE TABLE IF NOT EXISTS qe_stage_outcome (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    stage_id VARCHAR(64) NOT NULL,
    stage_index INTEGER NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_qe_stage_outcome_session_id ON qe_stage_outcome (session_id);

DROP INDEX IF EXISTS ix_qe_question_result_session_id;
DROP TABLE IF EXISTS qe_question_result;

DROP INDEX IF EXISTS ix_qe_answer_session_id;
DROP TABLE IF EXISTS qe_answer;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0003_replace_answer_result_with_stage_event_outcome',
    'Replace qe_answer/qe_question_result with qe_stage_event/qe_stage_outcome'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
