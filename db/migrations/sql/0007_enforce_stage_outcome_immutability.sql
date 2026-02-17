-- 0007_enforce_stage_outcome_immutability.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;
LOCK TABLE qe_stage_outcome IN ACCESS EXCLUSIVE MODE;

DO $$
DECLARE
    v_deleted_count INTEGER := 0;
BEGIN
    CREATE TABLE IF NOT EXISTS qe_stage_outcome_dedup_backup (
        id INTEGER PRIMARY KEY,
        session_id INTEGER NOT NULL,
        stage_id VARCHAR(64) NOT NULL,
        stage_index INTEGER NOT NULL,
        payload JSON NOT NULL,
        created_at TIMESTAMPTZ NOT NULL,
        deduped_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    ALTER TABLE qe_stage_outcome_dedup_backup
        ADD COLUMN IF NOT EXISTS deduped_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

    CREATE TEMP TABLE tmp_qe_stage_outcome_dedup_ids (
        id INTEGER PRIMARY KEY
    ) ON COMMIT DROP;

    INSERT INTO tmp_qe_stage_outcome_dedup_ids (id)
    SELECT id
    FROM (
        SELECT
            id,
            ROW_NUMBER() OVER (
                PARTITION BY session_id, stage_id
                ORDER BY created_at ASC, id ASC
            ) AS rn_by_stage_id,
            ROW_NUMBER() OVER (
                PARTITION BY session_id, stage_index
                ORDER BY created_at ASC, id ASC
            ) AS rn_by_stage_index
        FROM qe_stage_outcome
    ) ranked
    WHERE rn_by_stage_id > 1
       OR rn_by_stage_index > 1;

    INSERT INTO qe_stage_outcome_dedup_backup (
        id,
        session_id,
        stage_id,
        stage_index,
        payload,
        created_at,
        deduped_at
    )
    SELECT
        o.id,
        o.session_id,
        o.stage_id,
        o.stage_index,
        o.payload,
        o.created_at,
        CURRENT_TIMESTAMP
    FROM qe_stage_outcome o
    JOIN tmp_qe_stage_outcome_dedup_ids d
      ON d.id = o.id
    ON CONFLICT (id) DO NOTHING;

    DELETE FROM qe_stage_outcome o
    USING tmp_qe_stage_outcome_dedup_ids d
    WHERE o.id = d.id;

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    IF v_deleted_count > 0 THEN
        RAISE NOTICE
            'Removed % duplicate qe_stage_outcome rows before immutability constraints.',
            v_deleted_count;
    END IF;

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
