-- 0009_enforce_stage_outcome_stage_fk_and_schema_version.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

LOCK TABLE qe_stage_outcome IN ACCESS EXCLUSIVE MODE;
LOCK TABLE qe_stage IN SHARE ROW EXCLUSIVE MODE;

DO $$
DECLARE
    v_backfilled_count INTEGER := 0;
BEGIN
    INSERT INTO qe_stage (
        session_id,
        stage_id,
        plugin_key,
        stage_index,
        config,
        seed,
        status,
        created_at,
        activated_at,
        resolved_at
    )
    SELECT
        so.session_id,
        so.stage_id,
        LEFT(
            COALESCE(
                NULLIF(BTRIM(so.payload::jsonb ->> 'plugin_key'), ''),
                'legacy_stage_outcome'
            ),
            64
        ) AS plugin_key,
        so.stage_index,
        '{}'::json AS config,
        0 AS seed,
        'RESOLVED' AS status,
        so.created_at,
        so.created_at,
        so.created_at
    FROM qe_stage_outcome so
    LEFT JOIN qe_stage st
      ON st.session_id = so.session_id
     AND st.stage_id = so.stage_id
     AND st.stage_index = so.stage_index
    WHERE st.id IS NULL
    ON CONFLICT DO NOTHING;

    GET DIAGNOSTICS v_backfilled_count = ROW_COUNT;

    IF v_backfilled_count > 0 THEN
        RAISE NOTICE
            'Backfilled % qe_stage rows from existing qe_stage_outcome records.',
            v_backfilled_count;
    END IF;
END$$;

DO $$
DECLARE
    v_schema_patched_count INTEGER := 0;
BEGIN
    UPDATE qe_stage_outcome so
    SET payload = jsonb_set(
        so.payload::jsonb,
        '{schema_version}',
        to_jsonb('v1'::text),
        true
    )::json
    WHERE jsonb_typeof(so.payload::jsonb) = 'object'
      AND NULLIF(BTRIM(so.payload::jsonb ->> 'schema_version'), '') IS NULL;

    GET DIAGNOSTICS v_schema_patched_count = ROW_COUNT;

    IF v_schema_patched_count > 0 THEN
        RAISE NOTICE
            'Normalized schema_version to v1 on % qe_stage_outcome payload rows.',
            v_schema_patched_count;
    END IF;
END$$;

DO $$
DECLARE
    v_invalid_stage_ref_count INTEGER;
    v_invalid_schema_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_invalid_stage_ref_count
    FROM qe_stage_outcome so
    LEFT JOIN qe_stage st
      ON st.session_id = so.session_id
     AND st.stage_id = so.stage_id
     AND st.stage_index = so.stage_index
    WHERE st.id IS NULL;

    IF v_invalid_stage_ref_count > 0 THEN
        RAISE EXCEPTION
            'Cannot enforce qe_stage_outcome stage FK: % rows do not match qe_stage(session_id, stage_id, stage_index).',
            v_invalid_stage_ref_count;
    END IF;

    SELECT COUNT(*)
    INTO v_invalid_schema_count
    FROM qe_stage_outcome so
    WHERE (so.payload::jsonb ->> 'schema_version') IS DISTINCT FROM 'v1';

    IF v_invalid_schema_count > 0 THEN
        RAISE EXCEPTION
            'Cannot enforce qe_stage_outcome payload schema_version=v1: % rows are invalid.',
            v_invalid_schema_count;
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
          AND t.relname = 'qe_stage_outcome'
          AND c.conname = 'qe_stage_outcome_stage_triplet_fkey'
    ) THEN
        ALTER TABLE qe_stage_outcome
            ADD CONSTRAINT qe_stage_outcome_stage_triplet_fkey
            FOREIGN KEY (session_id, stage_id, stage_index)
            REFERENCES qe_stage (session_id, stage_id, stage_index)
            ON UPDATE NO ACTION
            ON DELETE NO ACTION;
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
          AND c.conname = 'ck_qe_stage_outcome_payload_schema_version_v1'
    ) THEN
        ALTER TABLE qe_stage_outcome
            ADD CONSTRAINT ck_qe_stage_outcome_payload_schema_version_v1
            CHECK ((payload::jsonb ->> 'schema_version') = 'v1');
    END IF;
END$$;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0009_enforce_stage_outcome_stage_fk_and_schema_version',
    'Backfill missing qe_stage rows and normalize missing outcome schema_version, then enforce stage FK and payload schema_version=v1'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
