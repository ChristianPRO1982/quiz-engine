-- 0008_enforce_score_entry_immutability_and_stage_fk.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

LOCK TABLE qe_score_entry IN ACCESS EXCLUSIVE MODE;
LOCK TABLE qe_stage IN SHARE ROW EXCLUSIVE MODE;

DO $$
DECLARE
    v_invalid_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_invalid_count
    FROM qe_score_entry se
    LEFT JOIN qe_stage st
      ON st.session_id = se.session_id
     AND st.stage_id = se.stage_id
     AND st.stage_index = se.stage_index
    WHERE st.id IS NULL;

    IF v_invalid_count > 0 THEN
        RAISE EXCEPTION
            'Cannot enforce qe_score_entry stage FK: % rows do not match qe_stage(session_id, stage_id, stage_index).',
            v_invalid_count;
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
          AND t.relname = 'qe_stage'
          AND c.conname = 'uq_qe_stage_session_stage_id_stage_index'
    ) THEN
        ALTER TABLE qe_stage
            ADD CONSTRAINT uq_qe_stage_session_stage_id_stage_index
            UNIQUE (session_id, stage_id, stage_index);
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
          AND t.relname = 'qe_score_entry'
          AND c.conname = 'qe_score_entry_stage_triplet_fkey'
    ) THEN
        ALTER TABLE qe_score_entry
            ADD CONSTRAINT qe_score_entry_stage_triplet_fkey
            FOREIGN KEY (session_id, stage_id, stage_index)
            REFERENCES qe_stage (session_id, stage_id, stage_index)
            ON UPDATE NO ACTION
            ON DELETE NO ACTION;
    END IF;
END$$;

CREATE OR REPLACE FUNCTION qe_forbid_score_entry_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'qe_score_entry is immutable: % is not allowed.',
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
          AND t.relname = 'qe_score_entry'
          AND tr.tgname = 'trg_qe_score_entry_no_update'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_score_entry_no_update
        BEFORE UPDATE ON qe_score_entry
        FOR EACH ROW
        EXECUTE FUNCTION qe_forbid_score_entry_mutation();
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
          AND t.relname = 'qe_score_entry'
          AND tr.tgname = 'trg_qe_score_entry_no_delete'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_score_entry_no_delete
        BEFORE DELETE ON qe_score_entry
        FOR EACH ROW
        EXECUTE FUNCTION qe_forbid_score_entry_mutation();
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
          AND t.relname = 'qe_score_entry'
          AND tr.tgname = 'trg_qe_score_entry_no_truncate'
          AND NOT tr.tgisinternal
    ) THEN
        CREATE TRIGGER trg_qe_score_entry_no_truncate
        BEFORE TRUNCATE ON qe_score_entry
        FOR EACH STATEMENT
        EXECUTE FUNCTION qe_forbid_score_entry_mutation();
    END IF;
END$$;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0008_enforce_score_entry_immutability_and_stage_fk',
    'Enforce qe_score_entry immutability and strong stage referential integrity'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
