# SLIDE Plugin (v0/v1 compatible)

SLIDE is the first built-in plugin for quiz-engine.

## Purpose
- Render one static informational slide.
- No player interaction.
- No scoring and no grading.
- Stage closure is controlled by the engine flow.

## Minimal `plugin_spec`
```json
{
  "schema_version": "v1",
  "title": "Welcome",
  "body": "Rules of the round",
  "body_format": "markdown",
  "media": {
    "type": "image",
    "src": "https://example.org/slide.png"
  }
}
```

`body_format` supports `"markdown"` and `"text"` and defaults to `"text"` when omitted.
`media` is optional. If `media.type` is `"none"`, `src` must be `null`.

## Compatibility
- v0 payloads are still accepted with `content` wrapper and `type: "slide"`.
- If `quiz_engine.plugins.slide` is unavailable, engine registry falls back to a sandbox slide runtime (`quiz_engine.plugins.sandbox_slide`) so sessions keep running.
