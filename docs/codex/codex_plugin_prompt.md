# Codex Plugin Generation Prompt — v1
Template for generating new plugins

Status: CANONICAL
Scope: AI-assisted plugin development

Use this prompt when generating a new plugin.

---

You are implementing a new plugin for quiz-engine.

You MUST strictly follow the authoritative contracts:

- docs/contracts/runtime_schema_v1.md
- docs/contracts/scoreEntry_contract_v1.md
- docs/contracts/runtime_plugin_io_v1.md
- docs/contracts/engine_plugin_interfaces_v1.md
- docs/contracts/engine_responsibilities_v1.md
- docs/CODEX_RULES.md

The engine is intentionally dumb.
All business logic belongs to the plugin.
Host UI and Player UI behavior are 100% plugin-owned.

---

# Plugin Requirements

You must implement:

- A StageRuntime class
- Deterministic behavior
- Integer-only scoring
- Host UI behavior
- Player UI behavior
- A resolve() method returning StageOutcome

You must NOT:

- Use floats
- Use percentages
- Access engine storage
- Modify session state
- Redefine StageOutcome
- Redefine ScoreEntry

---

# Output Requirements

Your output must include:

1. Plugin manifest (if required)
2. StageRuntime implementation
3. Deterministic use of seed
4. Example StageOutcome output
5. Example score_entries

All scoring must use ScoreEntry
as defined in scoreEntry_contract_v1.md.

---

# Determinism Constraint

Given identical:

- config
- seed
- player inputs

resolve() must produce identical StageOutcome.

No time-based randomness.
No external I/O during resolution.

---

# WebSocket Compliance

All runtime events must follow:

{
  "type": "EVENT_NAME",
  "payload": { ... }
}

No alternative envelope allowed.

---

# StageOutcome Rules

resolve() must return a dictionary matching:

runtime_schema_v1.md

Specifically:

- stage_id
- plugin_key
- public_state
- private_state (optional)
- score_entries (optional)

score_entries must:

- Use integer values only
- Respect validation rules
- Be deterministic
- Not include floats

---

# Code Constraints

- Follow PEP8
- Use modular structure
- No business logic in engine
- No global state
- No cross-session state

---

# Architectural Guardrail

If uncertain:

- Do not invent new runtime structures
- Do not modify contracts
- Conform strictly to existing contracts
