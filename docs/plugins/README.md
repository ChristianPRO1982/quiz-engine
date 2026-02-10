# Runtime schemas — Source of Truth

Any data structure used at runtime, storage, or transport MUST be documented in this folder before being implemented.

All schemas are explicitly versioned using `schema_version`.
Modifying a STABLE schema is a breaking change.

The engine orchestrates.
Plugins think.
Formats rule everything.

## Built-in plugins

- `slide` (v0): static informational stage, no interaction and no score. Reference: `quiz_engine/plugins/slide/README.md`
