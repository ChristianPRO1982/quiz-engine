SELECT
    table_schema,
    table_name,
    constraint_name,
    column_name,
    ordinal_position,
    position_in_unique_constraint
FROM information_schema.key_column_usage
WHERE table_schema = 'qe'
ORDER BY table_schema, table_name, constraint_name, ordinal_position;
