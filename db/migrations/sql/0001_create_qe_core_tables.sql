-- 0001_create_qe_core_tables.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

CREATE SCHEMA IF NOT EXISTS qe;
SET LOCAL search_path TO qe, public;

CREATE TABLE IF NOT EXISTS qe_schema_migration (
    id BIGSERIAL PRIMARY KEY,
    version VARCHAR(128) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    applied_by TEXT NOT NULL DEFAULT CURRENT_USER
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'qe_session_state'
          AND n.nspname = 'qe'
    ) THEN
        CREATE TYPE qe_session_state AS ENUM ('LOBBY', 'RUNNING', 'ENDED');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'qe_user_role_enum'
          AND n.nspname = 'qe'
    ) THEN
        CREATE TYPE qe_user_role_enum AS ENUM ('admin', 'moderator');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'qe_consent_scope'
          AND n.nspname = 'qe'
    ) THEN
        CREATE TYPE qe_consent_scope AS ENUM ('pseudo', 'history', 'email');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'qe_consent_status'
          AND n.nspname = 'qe'
    ) THEN
        CREATE TYPE qe_consent_status AS ENUM ('granted', 'revoked');
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'qe_consent_action'
          AND n.nspname = 'qe'
    ) THEN
        CREATE TYPE qe_consent_action AS ENUM ('granted', 'revoked', 'expired', 'revalidated');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS qe_user (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qe_service_setting (
    key VARCHAR(64) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qe_quiz (
    id SERIAL PRIMARY KEY,
    schema_version VARCHAR(16) NOT NULL,
    payload JSON NOT NULL,
    created_by_user_id INTEGER REFERENCES qe_user (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qe_session (
    id SERIAL PRIMARY KEY,
    session_code VARCHAR(12) NOT NULL UNIQUE,
    quiz_id INTEGER REFERENCES qe_quiz (id),
    host_user_id INTEGER REFERENCES qe_user (id),
    state qe_session_state NOT NULL DEFAULT 'LOBBY',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS qe_user_role (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES qe_user (id) ON DELETE CASCADE,
    role qe_user_role_enum NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_qe_user_role_user_id UNIQUE (user_id, role)
);

CREATE TABLE IF NOT EXISTS qe_consent (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES qe_user (id) ON DELETE CASCADE,
    scope qe_consent_scope NOT NULL,
    status qe_consent_status NOT NULL,
    policy_version VARCHAR(32) NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_qe_consent_user_id UNIQUE (user_id, scope)
);

CREATE TABLE IF NOT EXISTS qe_consent_audit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES qe_user (id) ON DELETE CASCADE,
    scope qe_consent_scope NOT NULL,
    action qe_consent_action NOT NULL,
    policy_version VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS qe_player (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES qe_user (id),
    player_code VARCHAR(64) NOT NULL UNIQUE,
    nickname VARCHAR(64) NOT NULL,
    is_guest BOOLEAN NOT NULL DEFAULT TRUE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_qe_player_session_id ON qe_player (session_id);

CREATE TABLE IF NOT EXISTS qe_answer (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES qe_player (id) ON DELETE CASCADE,
    question_id VARCHAR(64) NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_qe_answer_session_id ON qe_answer (session_id);

CREATE TABLE IF NOT EXISTS qe_question_result (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES qe_session (id) ON DELETE CASCADE,
    question_id VARCHAR(64) NOT NULL,
    payload JSON NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_qe_question_result_session_id ON qe_question_result (session_id);

INSERT INTO qe_schema_migration (version, description)
VALUES ('0001_create_qe_core_tables', 'Create initial qe_* tables and enum types')
ON CONFLICT (version) DO NOTHING;

COMMIT;
