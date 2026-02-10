SELECT
    id,
    version,
    description,
    applied_at,
    applied_by
FROM qe.qe_schema_migration
ORDER BY id;
