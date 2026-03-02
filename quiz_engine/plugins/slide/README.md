# SLIDE Plugin

Built-in informational plugin (`plugin_id=slide`, general type `info`).

## Purpose

Render a simple non-interactive slide:

- title
- body text (supports markdown via `body_format=markdown`)
- optional image URL

No scoring and no grading are produced.

## plugin_spec (accepted)

Minimal v1 shape:

```json
{
  "schema_version": "v1",
  "title": "Welcome",
  "body": "# Intro",
  "body_format": "markdown",
  "image_url": "https://cdn.example.org/welcome.png"
}
```

Legacy wrapper shape is also accepted:

```json
{
  "schema_version": "v0",
  "type": "slide",
  "content": {
    "title": "Welcome",
    "body": "Hello",
    "body_format": "text",
    "media": {"type": "none", "src": null}
  }
}
```

## Emitted frame payload

`VIEW_MODEL` payload:

```json
{
  "title": "Welcome",
  "body": "# Intro",
  "body_format": "markdown",
  "media": {"type": "image", "src": "https://cdn.example.org/welcome.png"}
}
```
