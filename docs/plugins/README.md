# Plugins — Implementation Guides

Status: REFERENCE
Scope: Plugin authors

This directory contains guidance and examples
for implementing plugins.

It does NOT define runtime contracts.

Authoritative contracts are located in:
- docs/contracts/

---

# Purpose of This Folder

This folder provides:

- Determinism guidelines
- Seed usage rules
- Example StageOutcome payloads
- Example WebSocket messages
- Practical implementation advice

These documents help plugin authors
implement correct, deterministic plugins.

---

# What This Folder Does NOT Define

This folder does NOT define:

- Runtime schemas
- StageOutcome structure
- ScoreEntry structure
- WebSocket envelope
- Engine responsibilities

All runtime structures are defined in:

docs/contracts/

If a contradiction appears,
contracts prevail.

---

# Engine–Plugin Philosophy

The engine orchestrates.
Plugins implement intelligence.

Plugins must:

- Follow StageRuntime interface
- Be deterministic
- Use provided seed
- Produce integer-only ScoreEntry
- Return valid StageOutcome

Plugins must not:

- Modify session lifecycle
- Access engine storage
- Introduce floats in scoring
- Implement ranking inside engine

---

# Built-in Plugins

The following plugins are bundled with the project:

- `slide` — Informational stage, no interaction, no scoring.
  Reference:
  quiz_engine/plugins/slide/README.md

---

# Stability

Documents in this folder are guidance only.

They may evolve without requiring a schema version bump.

Contracts in docs/contracts/ remain authoritative.