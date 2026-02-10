SELECT
    table_schema,
    table_name,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints
WHERE table_schema = 'qe'
ORDER BY table_schema, table_name, constraint_type, constraint_name;
