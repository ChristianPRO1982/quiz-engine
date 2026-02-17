WITH trigger_base AS (
    SELECT
        t.oid AS trigger_oid,
        n.nspname AS trigger_schema,
        c.relname AS event_object_table,
        t.tgname AS trigger_name,
        t.tgtype
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'qe'
      AND NOT t.tgisinternal
)
SELECT
    tb.trigger_schema,
    tb.event_object_table,
    tb.trigger_name,
    CASE
        WHEN (tb.tgtype & 64) = 64 THEN 'INSTEAD OF'
        WHEN (tb.tgtype & 2) = 2 THEN 'BEFORE'
        ELSE 'AFTER'
    END AS action_timing,
    ev.event_manipulation,
    CASE
        WHEN (tb.tgtype & 1) = 1 THEN 'ROW'
        ELSE 'STATEMENT'
    END AS action_orientation,
    REGEXP_REPLACE(pg_get_triggerdef(tb.trigger_oid), '^.*EXECUTE FUNCTION ', 'EXECUTE FUNCTION ') AS action_statement
FROM trigger_base tb
CROSS JOIN LATERAL (
    VALUES
        ('INSERT', (tb.tgtype & 4) = 4),
        ('DELETE', (tb.tgtype & 8) = 8),
        ('UPDATE', (tb.tgtype & 16) = 16),
        ('TRUNCATE', (tb.tgtype & 32) = 32)
) AS ev(event_manipulation, enabled)
WHERE ev.enabled
ORDER BY tb.trigger_schema, tb.event_object_table, tb.trigger_name, ev.event_manipulation;
