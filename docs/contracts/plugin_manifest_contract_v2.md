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
  "stage_config_schema": "object"
}
```

---

# 3. plugin_type Semantics

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

# 4. Compatibility

Engine may load legacy manifests (`v0`/`v1`) for backward compatibility.

When scanning plugins for catalog synchronization:

- `plugin_type` must be resolvable
- Unknown or missing type must be treated as invalid plugin metadata
  for catalog publication

---

# 5. Stability Rules

Once published:

- `plugin_key` must remain stable
- Breaking changes require version bump
- `plugin_type` changes require explicit review

---

# 6. Non-Goals

Manifest is NOT:

- A runtime definition
- A scoring definition
- A UI layout definition

