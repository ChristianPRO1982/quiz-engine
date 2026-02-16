# Contracts — quiz-engine
Authoritative runtime contracts

Status: CANONICAL INDEX
Scope: Engine ↔ Plugin runtime

This directory contains the authoritative runtime contracts
for quiz-engine.

If a structure exists at runtime, it must be defined here.

If it is not defined here, it must not exist in code.

---

# Purpose of This Folder

These documents define:

- Runtime data models
- Engine ↔ Plugin interface
- WebSocket interaction model
- HTTP runtime surface
- Plugin manifest structure
- Scoring contract

They do NOT define:

- Business logic
- UI rendering
- Database schema
- Infrastructure configuration

---

# Contract Hierarchy

The authoritative order is:

1. runtime_schema_v1.md
2. scoreEntry_contract_v1.md
3. runtime_plugin_io_v1.md
4. engine_responsibilities_v1.md
5. engine_plugin_interfaces_v1.md
6. plugin_manifest_contract_v1.md
7. http_endpoints_v1.md

If a contradiction appears, higher documents prevail.

---

# Schema Versioning

All runtime structures must include:

schema_version: "v1"

If a breaking change occurs:

- A new schema_version must be created
- Old schemas must remain archived
- Documentation must be updated before code

Silent structural changes are forbidden.

---

# Golden Rule

> Code implements contracts.
> Contracts define structure.
> Structure defines architecture.

Never modify runtime code without updating contracts first.

---

# Stability

These contracts are stable under v1.

Any structural change requires:

1. Contract update
2. Explicit version bump
3. Updated tests and fixtures
4. Then implementation

Contract-driven development is mandatory.

# Freeze Policy

The v1 contracts are frozen.

Any breaking change requires:
- new *_v2.md files
- updated references in docs/CODEX_RULES.md and docs/PROJECT_CONTRACT.md
- implementation changes only after documentation is updated

Do not edit v1 files to introduce structural changes.