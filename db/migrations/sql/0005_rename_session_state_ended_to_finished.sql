-- 0005_rename_session_state_ended_to_finished.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

DO $$
DECLARE
    has_ended BOOLEAN;
    has_finished BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_enum e ON e.enumtypid = t.oid
        WHERE n.nspname = 'qe'
          AND t.typname = 'qe_session_state'
          AND e.enumlabel = 'ENDED'
    )
    INTO has_ended;

    SELECT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_enum e ON e.enumtypid = t.oid
        WHERE n.nspname = 'qe'
          AND t.typname = 'qe_session_state'
          AND e.enumlabel = 'FINISHED'
    )
    INTO has_finished;

    IF has_ended AND NOT has_finished THEN
        ALTER TYPE qe_session_state RENAME VALUE 'ENDED' TO 'FINISHED';
    END IF;
END$$;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0005_rename_session_state_ended_to_finished',
    'Rename qe_session_state enum value ENDED to FINISHED for contract alignment'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
