SELECT
    n.nspname AS type_schema,
    t.typname AS type_name,
    e.enumsortorder AS enum_sort_order,
    e.enumlabel AS enum_label
FROM pg_catalog.pg_type t
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
JOIN pg_catalog.pg_enum e ON e.enumtypid = t.oid
WHERE n.nspname = 'qe'
ORDER BY type_schema, type_name, enum_sort_order;
