SELECT
    table_schema,
    table_name,
    check_option,
    is_updatable
FROM information_schema.views
WHERE table_schema = 'qe'
ORDER BY table_schema, table_name;
