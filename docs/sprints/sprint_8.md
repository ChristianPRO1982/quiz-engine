# Sprint 8 — Improve Plugin: SLIDE (Markdown Content Support)

## 1) Sprint Objective

Enhance the existing **SLIDE** plugin so that slide content can be authored as **Markdown** and rendered correctly for clients.

This sprint focuses only on:
- plugin spec updates
- plugin frame payload updates
- front rendering of markdown

No new gameplay logic, no scoring, no interactivity.

---

## 2) Scope — INCLUDED

### A) Plugin spec supports markdown
- The SLIDE plugin must accept a body field that contains **Markdown text**.
- The plugin must clearly declare whether the body is plain text or markdown.

### B) Deterministic behavior
- Rendering must be deterministic:
  - same input markdown produces same output HTML/structure
- No randomness.
- No external network calls for rendering.

### C) Rendering strategy (recommended)
Two acceptable strategies:

**Strategy 1 (recommended): client-side markdown rendering**
- Plugin sends raw markdown in frame payload
- Client renders markdown to HTML

**Strategy 2: server-side markdown rendering**
- Plugin converts markdown to HTML and sends HTML in frame payload
- Must ensure output is JSON-like and safe

Codex should implement **Strategy 1 by default** for simplicity and to keep plugin transport clean.

### D) Preview compatibility
- Sprint 6 preview mode must render markdown exactly like live session rendering.
- Same view component/code path must be reused for preview and live rendering.

### E) Editor compatibility (minimal)
- Quiz editor must allow editing slide body as markdown (plain textarea).
- Provide a small helper text: “Markdown supported”.

---

## 3) Scope — EXCLUDED

- WYSIWYG editor
- Advanced markdown extensions (tables, math, mermaid) unless already present
- Image uploads / attachments system
- Slides theming system
- Any interactive features

---

## 4) Data Contracts

### A) SLIDE plugin_spec (updated)
The SLIDE plugin_spec must accept a content format flag:

```json
{
  "schema_version": "v0",
  "type": "slide",
  "content": {
    "title": "string",
    "body": "string",
    "body_format": "markdown | text",
    "media": {
      "type": "image | none",
      "src": "string | null"
    }
  }
}
```

Rules:

* `body_format` defaults to `text` if missing (backward compatible).
* `body` is always a string.
* All fields remain JSON-serializable.

### B) PluginFrame payload (updated)

The plugin frame payload must include the same format field:

```json
{
  "title": "string",
  "body": "string",
  "body_format": "markdown | text",
  "media": {
    "type": "image | none",
    "src": "string | null"
  }
}
```

Clients must render:

* `text` as plain text
* `markdown` via markdown renderer

---

## 5) Rendering Requirements (Markdown)

### Minimal markdown features required

* headings (#, ##, ###)
* emphasis (*italic*, **bold**)
* lists (-, 1.)
* links ([text](url))
* line breaks / paragraphs

### Safety

If using client-side rendering:

* must sanitize output or configure renderer to avoid raw HTML injection
* raw HTML inside markdown must not be rendered by default

If using server-side rendering:

* must sanitize HTML output before sending to clients
* payload must remain JSON-like (no binary)

---

## 6) Files to Create / Modify

### Plugin

* Modify:

  * `plugins/slide/schemas.py` (accept body_format, backward compat)
  * `plugins/slide/runtime.py` (frame payload includes body_format)
  * `plugins/slide/README.md` (document markdown support)

### Editor

* Modify:

  * slide question editor panel (textarea + hint)
  * ensure the stored plugin_spec includes `body_format`

### Rendering (Preview + Live)

* Modify:

  * shared slide renderer component/template used by:

    * preview (Sprint 6)
    * live session (Sprint 7)
* Add a small markdown rendering utility (client-side) if not present.

---

## 7) Tests

### Plugin unit tests

* Legacy slide without `body_format` still works (defaults to text).
* Slide with `body_format="markdown"` emits correct frame payload.

### Rendering tests (lightweight)

* Preview renders markdown correctly for a sample slide
* Live rendering renders markdown correctly for the same sample

### Security check

* Verify `<script>` inside markdown is not executed/rendered.

---

## 8) Definition of Done (DoD)

* [ ] SLIDE plugin accepts markdown body via `body_format="markdown"`
* [ ] Frame payload contains `body_format`
* [ ] Preview renders markdown identically to live session
* [ ] Quiz editor can author slide markdown (textarea)
* [ ] Backward compatibility: old slides render as text
* [ ] Basic sanitization prevents HTML/script injection
* [ ] Tests and CI pass

---

## 9) Manual Validation Scenario

1. Create a quiz with a slide stage
2. Set slide body_format to markdown
3. Use markdown content:

   * headings, bold, list, link
4. Preview quiz: markdown renders correctly
5. Start a live session: markdown renders correctly on phones
6. Try unsafe markdown: `<script>alert(1)</script>`

   * must not execute
7. Confirm legacy slide (no body_format) still renders as text

---

## 10) Exit Rule

Sprint 8 ends when:

* markdown slides work end-to-end (editor → preview → live)
* compatibility with existing slides is preserved
* rendering is safe and deterministic
* CI is green
