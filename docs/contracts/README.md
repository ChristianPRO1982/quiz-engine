# Runtime Contracts — Source of Truth

This directory contains the **authoritative runtime contracts** of the `quiz-engine` project.

These documents define **all data structures, lifecycles, and interactions**
used at runtime between:
- the engine core
- plugins
- WebSocket transports
- replay / persistence mechanisms

If something is not documented here, **it must not exist in code**.

---

## Golden Rule

> **Formats rule everything.**

No runtime behavior, data structure, or transport format may be introduced
without being explicitly documented in this folder.

---

## Contract Status

Each contract document MUST declare its status at the top:

- **DRAFT**  
  The contract may evolve and is not yet guaranteed stable.

- **STABLE**  
  The contract is frozen.
  Any modification is a **breaking change** and requires:
  - a new `schema_version`
  - updated documentation
  - updated fixtures
  - updated tests

Silent changes are strictly forbidden.

---

## Versioning Rules

- All runtime contracts are explicitly versioned using:
```
schema_version: vX

- `schema_version` applies to:
- runtime objects
- WebSocket payloads
- plugin manifests
- outcomes and traces

Engine and plugin **code versions** follow Semantic Versioning and are separate
from contract versions.

---

## Scope of These Contracts

The contracts in this folder define:

- Runtime data models (Stage, Context, Events, Frames, Outcomes)
- Engine ↔ Plugin interfaces
- WebSocket message structures
- Invariants and validation rules
- Serialization requirements (JSON-only, UTC timestamps)

They do **not** define:
- quiz business logic
- scoring rules
- UI rendering details
- database schemas

---

## Engine Responsibilities (Fixed)

The engine core:
- orchestrates stage lifecycles
- transports events and frames
- aggregates numeric score deltas
- stores traces and outcomes for replay
- enforces contract validation

The engine core MUST NEVER:
- interpret answers
- calculate scores
- apply quiz logic
- branch behavior based on plugin content

---

## Plugin Responsibilities (Fixed)

Plugins:
- own all intelligence (rules, scoring, grading, reveal)
- interpret their own payloads
- may emit live render frames
- must be deterministic when using randomness

Plugins interact with the engine **only via these contracts**.

---

## WebSocket Discipline

All WebSocket messages:
- follow a `{ type, payload }` envelope
- carry only JSON-serializable payloads
- use server-generated timestamps as the source of truth

No Python-only objects may cross system boundaries.

---

## Change Process

If a new requirement appears:

1. **STOP coding**
2. Propose a contract update (documentation only)
3. Decide whether it is:
 - backward-compatible → same `schema_version`
 - breaking → new `schema_version`
4. Update:
 - this documentation
 - related fixtures
 - related tests
5. Only then implement code

---

## Enforcement

- Tests and fixtures are part of the contract.
- CI must fail if:
- undocumented fields appear
- a STABLE contract is modified without version bump
- Codex and any AI assistant MUST follow these documents strictly.

---

## Final Reminder

> A strict engine with explicit contracts is easier to evolve
> than a clever engine with hidden assumptions.
```