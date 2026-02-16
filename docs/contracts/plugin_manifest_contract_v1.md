# Plugin Manifest Contract — v1
Authoritative plugin declaration structure

Status: CANONICAL
Schema version: v1
Scope: Plugin registration and metadata

This document defines how a plugin declares itself
to the engine.

Runtime behavior is defined in:
- runtime_schema_v1.md
- engine_plugin_interfaces_v1.md

Scoring is defined in:
- scoreEntry_contract_v1.md

---

# 1. Purpose

The manifest describes:

- Plugin identity
- Version
- Runtime entrypoint
- Capabilities
- Stage configuration schema

The manifest does not contain runtime logic.

---

# 2. Manifest Schema

```json
{
  "schema_version": "v1",
  "plugin_key": "string",
  "name": "string",
  "version": "string",
  "entrypoint": "string",
  "description": "string | null",
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

# 3. Field Semantics

### schema_version

Must be "v1".

---

### plugin_key (required)

Unique identifier.

* Lowercase
* Snake_case
* Stable
* Used in Stage.plugin_key

Must not change once published.

---

### name (required)

Human-readable name.

Used for UI display only.

---

### version (required)

Semantic version string.

Example:

* "1.0.0"

Engine does not interpret version.

---

### entrypoint (required)

Python import path.

Example:
"plugins.qcm.runtime:StageRuntime"

Engine resolves this dynamically.

---

### description (optional)

Human-readable explanation.

No runtime effect.

---

### capabilities (required)

Describes plugin behavior.

#### produces_scoring

True if plugin emits ScoreEntry with delta_score.

#### produces_grading

True if plugin emits grade_value / grade_max.

#### uses_seed

True if plugin relies on deterministic seed.

Should be true for most plugins.

#### supports_intermediate_updates

True if plugin emits STAGE_UPDATE before resolve().

---

### stage_config_schema (required)

JSON-schema-like object describing expected stage config.

Engine does not validate business logic,
only structural integrity.

Example:

```json
{
  "type": "object",
  "required": ["question", "choices", "correct_index"],
  "properties": {
    "question": { "type": "string" },
    "choices": {
      "type": "array",
      "items": { "type": "string" }
    },
    "correct_index": { "type": "integer" }
  }
}
```

---

# 4. Engine Responsibilities

The engine must:

* Load manifest
* Register plugin_key
* Validate presence of entrypoint
* Validate manifest schema_version

The engine must not:

* Interpret stage_config_schema semantics
* Enforce scoring logic
* Enforce grading logic

---

# 5. Plugin Stability Rules

Once published:

* plugin_key must remain stable
* Backward-incompatible changes require version bump
* StageRuntime interface must remain compliant

---

# 6. Non-Goals

Manifest is NOT:

* A runtime definition
* A scoring definition
* A UI definition
* A ranking definition

---

# 7. Future Extensions

Future versions may include:

* UI hints
* Category tags
* Difficulty metadata
* Compatibility flags

But must not alter:

* Engine dumb philosophy
* Integer-only scoring
