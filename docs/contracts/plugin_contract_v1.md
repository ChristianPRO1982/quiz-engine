# Plugin Contract — v1

## Status

**DRAFT**

This contract defines how plugins interact with the quiz-engine.
It is expected to evolve, but all changes must remain explicit and documented.

---

## Purpose

A plugin represents **one autonomous unit of quiz intelligence**.

The engine:
- orchestrates execution
- manages sessions and state
- stores plugin outputs

The plugin:
- interprets quiz content
- processes player answers
- computes results
- defines reveal / interlude behavior

The engine must never interpret plugin logic.

---

## Core Principles

- Plugins are the **only place where quiz intelligence lives**
- Plugins must be **stateless between sessions**
- Plugins must be **purely deterministic** given the same inputs
- Plugins must expose **explicit inputs and outputs**
- Plugins must never access global engine state directly

---

## Plugin Identity

Each plugin MUST define:

- `plugin_id`
- `plugin_version`
- `engine_version_compatibility`

The engine must refuse to load plugins with incompatible engine versions.

---

## Plugin Manifest

Each plugin MUST provide a **manifest** describing its capabilities.

The manifest:
- is static
- is JSON-serializable
- is independent from quiz configuration

The manifest defines:
- plugin identity
- supported question type
- supported scoring modes
- supported reveal styles
- required runtime capabilities (timer, anonymity, etc.)

The engine uses the manifest only for validation and compatibility checks.

---

## Plugin Configuration (Quiz Node)

Plugin configuration is provided via the **Quiz JSON**.

This configuration:
- is plugin-specific
- is opaque to the engine
- must be fully interpretable by the plugin

The engine must:
- load the configuration
- pass it unchanged to the plugin
- never inspect or modify it

---

## Plugin Lifecycle (Conceptual)

For each question node, a plugin is expected to support the following phases:

1. **Initialization**
   - Receives configuration and context
   - Prepares internal structures

2. **Answer Collection**
   - Receives normalized player answers
   - May accept or reject answers based on rules

3. **Finalization**
   - Locks answers
   - Computes results
   - Produces a QuestionResult

4. **Reveal / Interlude**
   - Provides data required for result visualization
   - Defines optional animations or transitions

The engine controls *when* these phases occur.
The plugin controls *how* they behave.

---

## Player Answer Input

Plugins receive player answers via a **normalized input object**.

This object:
- is defined by a shared runtime contract
- contains timing and attempt metadata
- contains an opaque `answer` payload

Plugins must not expect engine-specific fields beyond this contract.

---

## Result Output (Mandatory)

Each plugin MUST produce a `QuestionResult` object at the end of execution.

This object:
- is JSON-serializable
- conforms to `result_contract_v1.md`
- includes per-player score deltas
- may include opaque plugin-owned data

The engine:
- stores the result
- aggregates numeric score deltas
- never interprets plugin-specific payloads

---

## Scoring Rules

Plugins own all scoring logic.

Scoring MUST:
- be explicit
- be deterministic
- produce numeric deltas (positive, zero, or negative)

The engine must never:
- know scoring rules
- branch logic based on scoring mode
- modify score values

---

## Reveal and Visualization

Plugins may define how results are revealed between questions.

Reveal behavior:
- is plugin-owned
- may vary between plugins
- may include animation instructions or layout hints

The engine:
- triggers reveal phases
- transports reveal payloads
- does not render or interpret visual logic

---

## Forbidden Behaviors

A plugin MUST NOT:

- access engine internal state
- persist data outside allowed session scope
- rely on side effects
- assume a specific frontend implementation
- modify other plugins’ data

---

## Error Handling

Plugins must fail explicitly.

When an error occurs:
- the plugin must return a structured error
- the engine must propagate the error as an event
- silent failures are forbidden

---

## Determinism Rule

Given:
- the same configuration
- the same player answers
- the same timing data

A plugin MUST produce the same `QuestionResult`.

Randomness must be:
- explicit
- seeded
- reproducible

---

## Final Rule

> A plugin is a black box with a contract.
> The engine trusts the box, but never opens it.

