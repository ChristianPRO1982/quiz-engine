WITH non_fk_constraints AS (
    SELECT
        ns.nspname AS table_schema,
        tbl.relname AS table_name,
        con.conname AS constraint_name,
        att.attname AS column_name
    FROM pg_catalog.pg_constraint con
    JOIN pg_catalog.pg_class tbl
        ON tbl.oid = con.conrelid
    JOIN pg_catalog.pg_namespace ns
        ON ns.oid = tbl.relnamespace
    JOIN LATERAL unnest(con.conkey) AS key(attnum)
        ON TRUE
    JOIN pg_catalog.pg_attribute att
        ON att.attrelid = tbl.oid
       AND att.attnum = key.attnum
    WHERE ns.nspname = 'qe'
      AND con.contype IN ('p', 'u', 'c', 'x')
),
fk_target_columns AS (
    SELECT
        tgt_ns.nspname AS table_schema,
        tgt_tbl.relname AS table_name,
        con.conname AS constraint_name,
        tgt_att.attname AS column_name
    FROM pg_catalog.pg_constraint con
    JOIN pg_catalog.pg_class src_tbl
        ON src_tbl.oid = con.conrelid
    JOIN pg_catalog.pg_namespace src_ns
        ON src_ns.oid = src_tbl.relnamespace
    JOIN pg_catalog.pg_class tgt_tbl
        ON tgt_tbl.oid = con.confrelid
    JOIN pg_catalog.pg_namespace tgt_ns
        ON tgt_ns.oid = tgt_tbl.relnamespace
    JOIN LATERAL unnest(con.confkey) AS key(attnum)
        ON TRUE
    JOIN pg_catalog.pg_attribute tgt_att
        ON tgt_att.attrelid = tgt_tbl.oid
       AND tgt_att.attnum = key.attnum
    WHERE con.contype = 'f'
      AND src_ns.nspname = 'qe'
)
SELECT
    table_schema,
    table_name,
    constraint_name,
    column_name
FROM (
    SELECT * FROM non_fk_constraints
    UNION ALL
    SELECT * FROM fk_target_columns
) q
ORDER BY table_schema, table_name, constraint_name, column_name;
