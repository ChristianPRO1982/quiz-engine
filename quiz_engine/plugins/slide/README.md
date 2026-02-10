# SLIDE Plugin (v0)

SLIDE is the first built-in plugin for quiz-engine.

## Purpose
- Render one static informational slide.
- No player interaction.
- No scoring and no grading.
- Stage closure is controlled by the engine flow.

## Minimal `plugin_spec`
```json
{
  "schema_version": "v0",
  "type": "slide",
  "content": {
    "title": "Welcome",
    "body": "Rules of the round",
    "media": {
      "type": "image",
      "src": "https://example.org/slide.png"
    }
  }
}
```

`media` is optional. If `media.type` is `"none"`, `src` must be `null`.
