# Plugin Manifest Contract — v2
Authoritative plugin declaration structure

Status: CANONICAL
Schema version: v2
Scope: Plugin registration, metadata, and catalog typing

This document defines how a plugin declares itself
to the engine and plugin catalog.

Runtime behavior is defined in:
- runtime_schema_v1.md
- engine_plugin_interfaces_v1.md

---

# 1. Purpose

The manifest describes:

- Plugin identity
- Version
- Runtime entrypoint
- General plugin type
- Capabilities
- Stage configuration schema
- Default stage configuration for authoring

The manifest does not contain runtime logic.

---

# 2. Manifest Schema

```json
{
  "schema_version": "v2",
  "plugin_key": "string",
  "name": "string",
  "version": "string",
  "entrypoint": "string",
  "description": "string | null",
  "plugin_type": "info | quiz | scoreboard | form",
  "capabilities": {
    "produces_scoring": "boolean",
    "produces_grading": "boolean",
    "uses_seed": "boolean",
    "supports_intermediate_updates": "boolean"
  },
  "stage_config_schema": "object",
  "default_stage_config": "object",
  "editor_hints": "object | null"
}
```

---

# 3. Authoring Semantics (Plugin-Smart)

`stage_config_schema` and `default_stage_config` define
how authoring creates and edits a stage.

Rules:

- Engine authoring flow MUST initialize a new stage config
  from `default_stage_config`.
- `default_stage_config` MUST be structurally valid
  against `stage_config_schema`.
- Engine and editor MUST treat stage config as plugin-owned data.
- Engine and editor MUST NOT hardcode plugin behavior branches
  (for example `if question.type == "slide"`).
- `editor_hints` is optional metadata for UX rendering only.
  It must not alter runtime semantics.

The persisted stage config remains an opaque plugin payload.

---

# 4. plugin_type Semantics

`plugin_type` is required and must be one of:

- `info`: informational content stage
- `quiz`: player-answer game stage
- `scoreboard`: score display / ranking presentation stage
- `form`: structured input / survey / form stage

This field is used by:

- Admin plugin catalog
- Authoring UI filtering
- Operational reporting

It does not define scoring behavior by itself.

---

# 5. Compatibility

Engine may load legacy manifests (`v0`/`v1`) for backward compatibility.

When scanning plugins for catalog synchronization:

- `plugin_type` must be resolvable
- Unknown or missing type must be treated as invalid plugin metadata
  for catalog publication

For legacy manifests missing `default_stage_config`:

- authoring may use an empty object `{}` as fallback
- editor should expose generic JSON editing
- plugin-specific hardcoded behavior in engine/editor remains forbidden

---

# 6. Stability Rules

Once published:

- `plugin_key` must remain stable
- Breaking changes require version bump
- `plugin_type` changes require explicit review

---

# 7. Non-Goals

Manifest is NOT:

- A runtime definition
- A scoring definition
- A UI layout definition
