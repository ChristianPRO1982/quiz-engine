SELECT
    table_schema,
    table_name,
    constraint_name,
    column_name
FROM information_schema.constraint_column_usage
WHERE table_schema = 'qe'
ORDER BY table_schema, table_name, constraint_name, column_name;
