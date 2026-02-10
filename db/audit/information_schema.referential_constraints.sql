SELECT
    tc.constraint_schema,
    tc.table_name,
    tc.constraint_name,
    rc.unique_constraint_schema,
    rc.unique_constraint_name,
    rc.match_option,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.referential_constraints rc
JOIN information_schema.table_constraints tc
    ON tc.constraint_catalog = rc.constraint_catalog
   AND tc.constraint_schema = rc.constraint_schema
   AND tc.constraint_name = rc.constraint_name
WHERE tc.constraint_schema = 'qe'
ORDER BY tc.constraint_schema, tc.table_name, tc.constraint_name;
