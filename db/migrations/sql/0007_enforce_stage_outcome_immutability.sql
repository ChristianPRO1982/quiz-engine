-- 0007_enforce_stage_outcome_immutability.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM qe_stage_outcome
        GROUP BY session_id, stage_id
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Cannot enforce immutability: duplicate qe_stage_outcome rows for (session_id, stage_id).';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM qe_stage_outcome
        GROUP BY session_id, stage_index
        HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Cannot enforce immutability: duplicate qe_stage_outcome rows for (session_id, stage_index).';
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'qe'
          AND t.relname = 'qe_stage_outcome'
          AND c.conname = 'uq_qe_stage_outcome_session_stage_id'
    ) THEN
        ALTER TABLE qe_stage_outcome
            ADD CONSTRAINT uq_qe_stage_outcome_session_stage_id
            UNIQUE (session_id, stage_id);
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'qe'
          AND t.relname = 'qe_stage_outcome'
          AND c.conname = 'uq_qe_stage_outcome_session_stage_index'
    ) THEN
        ALTER TABLE qe_stage_outcome
            ADD CONSTRAINT uq_qe_stage_outcome_session_stage_index
            UNIQUE (session_id, stage_index);
    END IF;
END$$;

CREATE OR REPLACE FUNCTION qe_forbid_stage_outcome_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'qe_stage_outcome is immutable: % is not allowed.',
        TG_OP
        USING ERRCODE = '55000';
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger tr
        JOIN pg_class t ON t.oid = tr.tgrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'qe'
          AND t.relname = 'qe_stage_outcome'
          AND tr.tgname = 'trg_qe_stage_outcome_no_update'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_stage_outcome_no_update
        BEFORE UPDATE ON qe_stage_outcome
        FOR EACH ROW
        EXECUTE FUNCTION qe_forbid_stage_outcome_mutation();
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger tr
        JOIN pg_class t ON t.oid = tr.tgrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'qe'
          AND t.relname = 'qe_stage_outcome'
          AND tr.tgname = 'trg_qe_stage_outcome_no_delete'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_stage_outcome_no_delete
        BEFORE DELETE ON qe_stage_outcome
        FOR EACH ROW
        EXECUTE FUNCTION qe_forbid_stage_outcome_mutation();
    END IF;
END$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_trigger tr
        JOIN pg_class t ON t.oid = tr.tgrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'qe'
          AND t.relname = 'qe_stage_outcome'
          AND tr.tgname = 'trg_qe_stage_outcome_no_truncate'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_stage_outcome_no_truncate
        BEFORE TRUNCATE ON qe_stage_outcome
        FOR EACH STATEMENT
        EXECUTE FUNCTION qe_forbid_stage_outcome_mutation();
    END IF;
END$$;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0007_enforce_stage_outcome_immutability',
    'Enforce qe_stage_outcome immutability with unique business keys and mutation-blocking triggers'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
