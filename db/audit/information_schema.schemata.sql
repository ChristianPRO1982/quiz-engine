SELECT
    schema_name,
    schema_owner
FROM information_schema.schemata
WHERE schema_name = 'qe'
ORDER BY schema_name;
