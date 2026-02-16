# Plugin Manifest Contract — v0 (with Assets)

## Purpose

Define the exact structure of a plugin manifest used by quiz-engine to:
- identify plugins
- declare capabilities
- declare assets (JS/CSS) to load on the client
- keep plugins self-contained

The engine loads plugins by explicit registration initially.
Later discovery mechanisms (entrypoints, scanning) may be added without changing this manifest schema.

---

# 1. Manifest Schema

A plugin must expose a **PluginManifest** JSON object.

## 1.1 Required fields

```json
{
  "schema_version": "v0",
  "plugin_id": "string",
  "plugin_version": "string",
  "display_name": "string"
}
```

### Rules

* `schema_version` MUST be `"v0"`
* `plugin_id` MUST be stable, unique, lowercase (snake or kebab)

  * examples: `slide`, `mcq`, `wordcloud`, `slider`
* `plugin_version` MUST follow semantic versioning (recommended)
* `display_name` is user-facing label (UI)

---

## 1.2 Optional fields

### 1.2.1 Capabilities

Capabilities are declarative hints for the engine UI and orchestration.

```json
{
  "capabilities": {
    "live_frames": true,
    "supports_host_actions": false,
    "multi_phase": false,
    "uses_random_seed": false,
    "supports_scoring": false,
    "supports_grading": false,
    "supports_no_score": true
  }
}
```

#### Meaning (recommended semantics)

* `live_frames`: plugin emits frames during stage (not only at open)
* `supports_host_actions`: plugin accepts `HostAction`
* `multi_phase`: plugin can run multiple phases within a single stage
* `uses_random_seed`: plugin requires `random_seed` for deterministic randomness
* `supports_scoring`: plugin may output `delta_score`
* `supports_grading`: plugin may output `grade_value/grade_max`
* `supports_no_score`: plugin supports returning no score (null score_entries)

Capabilities are hints only; plugins remain the source of truth at runtime.

---

### 1.2.2 Assets

Plugins may declare client assets to be loaded when a stage uses this plugin.

```json
{
  "assets": {
    "js": [
      "/plugins/slide/slide.js"
    ],
    "css": [
      "/plugins/slide/slide.css"
    ]
  }
}
```

#### Rules

* `assets.js` and `assets.css` are lists of URLs (strings)
* URLs must be served by quiz-engine (static files) or by a trusted internal origin
* Engine must avoid duplicate loading (same URL loaded once per page/session)
* Assets must be optional: a plugin may have no assets at all

**Security note (recommended):**

* Do not load arbitrary third-party URLs in production
* Prefer hosting assets under `/plugins/{plugin_id}/...`

---

### 1.2.3 Stage Kinds (optional hint)

If the plugin supports multiple stage kinds (variants), it may declare them:

```json
{
  "stage_kinds": ["slide", "slide_markdown"]
}
```

This is optional and informational.

---

### 1.2.4 Authors / metadata (optional)

```json
{
  "metadata": {
    "author": "string",
    "homepage": "string",
    "license": "string"
  }
}
```

---

# 2. Full Manifest Example

```json
{
  "schema_version": "v0",
  "plugin_id": "slide",
  "plugin_version": "1.0.0",
  "display_name": "Slide",
  "capabilities": {
    "live_frames": false,
    "supports_host_actions": false,
    "multi_phase": false,
    "uses_random_seed": false,
    "supports_scoring": false,
    "supports_grading": false,
    "supports_no_score": true
  },
  "assets": {
    "js": ["/plugins/slide/slide.js"],
    "css": ["/plugins/slide/slide.css"]
  },
  "metadata": {
    "author": "quiz-engine",
    "license": "proprietary"
  }
}
```

---

# 3. Engine Loading Expectations (v0)

## 3.1 Manifest access

A plugin must expose a function or property that returns the manifest.

The engine must be able to retrieve:

* plugin_id
* capabilities
* assets

## 3.2 When assets are loaded

Recommended behavior:

* When the active stage uses plugin_id `X`, engine ensures assets for `X` are loaded
* Assets should be loaded once per page and cached by the browser

## 3.3 Asset loading policy

Engine must:

* load CSS via `<link rel="stylesheet">`
* load JS via `<script defer>` (recommended)
* ensure stable ordering:

  * CSS first
  * JS last
* avoid duplicates

---

# 4. Compatibility and Versioning

* Manifest schema is versioned by `schema_version`.
* Breaking changes require incrementing schema_version.
* Plugins and engine must refuse mismatched schema_version by default.

---

# 5. Design Philosophy

* Manifests are declarative and minimal.
* Plugins remain self-contained.
* Engine remains dumb and stable.
* Capabilities and assets are hints for orchestration, not logic.
