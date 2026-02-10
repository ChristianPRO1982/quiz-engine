SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_catalog.pg_indexes
WHERE schemaname = 'qe'
ORDER BY schemaname, tablename, indexname;
