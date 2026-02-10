SELECT
    trigger_schema,
    event_object_table,
    trigger_name,
    action_timing,
    event_manipulation,
    action_orientation,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'qe'
ORDER BY trigger_schema, event_object_table, trigger_name;
