SELECT
    src_ns.nspname AS constraint_schema,
    src_tbl.relname AS table_name,
    src_att.attname AS source_column,
    con.conname AS constraint_name,
    tgt_ns.nspname AS target_schema,
    tgt_tbl.relname AS target_table,
    tgt_att.attname AS target_column,
    CASE con.confupdtype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
    END AS update_rule,
    CASE con.confdeltype
        WHEN 'a' THEN 'NO ACTION'
        WHEN 'r' THEN 'RESTRICT'
        WHEN 'c' THEN 'CASCADE'
        WHEN 'n' THEN 'SET NULL'
        WHEN 'd' THEN 'SET DEFAULT'
    END AS delete_rule
FROM pg_catalog.pg_constraint con
JOIN pg_catalog.pg_class src_tbl
    ON src_tbl.oid = con.conrelid
JOIN pg_catalog.pg_namespace src_ns
    ON src_ns.oid = src_tbl.relnamespace
JOIN pg_catalog.pg_class tgt_tbl
    ON tgt_tbl.oid = con.confrelid
JOIN pg_catalog.pg_namespace tgt_ns
    ON tgt_ns.oid = tgt_tbl.relnamespace
JOIN LATERAL unnest(con.conkey) WITH ORDINALITY AS src_key(attnum, ord)
    ON TRUE
JOIN LATERAL unnest(con.confkey) WITH ORDINALITY AS tgt_key(attnum, ord)
    ON tgt_key.ord = src_key.ord
JOIN pg_catalog.pg_attribute src_att
    ON src_att.attrelid = src_tbl.oid
   AND src_att.attnum = src_key.attnum
JOIN pg_catalog.pg_attribute tgt_att
    ON tgt_att.attrelid = tgt_tbl.oid
   AND tgt_att.attnum = tgt_key.attnum
WHERE con.contype = 'f'
  AND src_ns.nspname = 'qe'
ORDER BY
    src_ns.nspname,
    src_tbl.relname,
    con.conname,
    src_key.ord;
