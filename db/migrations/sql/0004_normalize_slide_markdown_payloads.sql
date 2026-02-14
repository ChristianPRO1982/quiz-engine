-- 0004_normalize_slide_markdown_payloads.sql
-- Manual migration for PostgreSQL (run by DB admin).

BEGIN;

SET LOCAL search_path TO qe, public;

DO $$
DECLARE
    quiz_row RECORD;
    payload_obj JSONB;
    source_key TEXT;
    normalized_array JSONB;
    item JSONB;
    spec_obj JSONB;
    content_obj JSONB;
    media_obj JSONB;
    media_type TEXT;
    media_src TEXT;
    body_format TEXT;
    fallback_title TEXT;
BEGIN
    FOR quiz_row IN
        SELECT id, payload::jsonb AS payload_jsonb
        FROM qe_quiz
    LOOP
        payload_obj := quiz_row.payload_jsonb;

        FOREACH source_key IN ARRAY ARRAY['questions', 'stages']
        LOOP
            IF jsonb_typeof(payload_obj -> source_key) <> 'array' THEN
                CONTINUE;
            END IF;

            normalized_array := '[]'::jsonb;

            FOR item IN
                SELECT value
                FROM jsonb_array_elements(payload_obj -> source_key)
            LOOP
                IF jsonb_typeof(item) = 'object'
                   AND COALESCE(
                       NULLIF(BTRIM(item ->> 'type'), ''),
                       NULLIF(BTRIM(item ->> 'plugin_id'), '')
                   ) = 'slide'
                THEN
                    fallback_title := COALESCE(NULLIF(BTRIM(item ->> 'title'), ''), 'Slide');

                    IF jsonb_typeof(item -> 'spec') = 'object' THEN
                        spec_obj := item -> 'spec';
                    ELSIF jsonb_typeof(item -> 'plugin_spec') = 'object' THEN
                        spec_obj := item -> 'plugin_spec';
                    ELSE
                        spec_obj := '{}'::jsonb;
                    END IF;

                    IF jsonb_typeof(spec_obj -> 'content') = 'object' THEN
                        content_obj := spec_obj -> 'content';
                    ELSE
                        content_obj := '{}'::jsonb;
                    END IF;

                    content_obj := jsonb_set(
                        content_obj,
                        '{title}',
                        to_jsonb(COALESCE(NULLIF(BTRIM(content_obj ->> 'title'), ''), fallback_title)::text),
                        true
                    );
                    content_obj := jsonb_set(
                        content_obj,
                        '{body}',
                        to_jsonb(COALESCE(content_obj ->> 'body', item ->> 'text', '')::text),
                        true
                    );

                    body_format := LOWER(BTRIM(COALESCE(content_obj ->> 'body_format', '')));
                    IF body_format NOT IN ('markdown', 'text') THEN
                        body_format := 'text';
                    END IF;
                    content_obj := jsonb_set(
                        content_obj,
                        '{body_format}',
                        to_jsonb(body_format::text),
                        true
                    );

                    IF jsonb_typeof(content_obj -> 'media') = 'object' THEN
                        media_obj := content_obj -> 'media';
                        media_src := NULLIF(BTRIM(media_obj ->> 'src'), '');
                        media_type := LOWER(BTRIM(COALESCE(media_obj ->> 'type', 'none')));
                        IF media_type = 'image' AND media_src IS NOT NULL THEN
                            media_obj := jsonb_build_object(
                                'type', 'image',
                                'src', media_src
                            );
                        ELSE
                            media_obj := jsonb_build_object(
                                'type', 'none',
                                'src', to_jsonb(NULL::text)
                            );
                        END IF;
                    ELSE
                        media_obj := jsonb_build_object(
                            'type', 'none',
                            'src', to_jsonb(NULL::text)
                        );
                    END IF;
                    content_obj := jsonb_set(content_obj, '{media}', media_obj, true);

                    spec_obj := jsonb_set(spec_obj, '{schema_version}', to_jsonb('v0'::text), true);
                    spec_obj := jsonb_set(spec_obj, '{type}', to_jsonb('slide'::text), true);
                    spec_obj := jsonb_set(spec_obj, '{content}', content_obj, true);

                    item := jsonb_set(item, '{spec}', spec_obj, true);
                    IF item ? 'plugin_spec' THEN
                        item := jsonb_set(item, '{plugin_spec}', spec_obj, true);
                    END IF;
                END IF;

                normalized_array := normalized_array || jsonb_build_array(item);
            END LOOP;

            payload_obj := jsonb_set(payload_obj, ARRAY[source_key], normalized_array, true);
        END LOOP;

        UPDATE qe_quiz
        SET payload = payload_obj::json
        WHERE id = quiz_row.id
          AND payload::jsonb IS DISTINCT FROM payload_obj;
    END LOOP;
END$$;

INSERT INTO qe_schema_migration (version, description)
VALUES (
    '0004_normalize_slide_markdown_payloads',
    'Normalize SLIDE plugin specs with content.body and content.body_format'
)
ON CONFLICT (version) DO NOTHING;

COMMIT;
