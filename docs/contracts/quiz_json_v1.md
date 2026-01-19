# Quiz JSON Contract — v1

## Status

**DRAFT**

This contract defines the structure of a quiz definition consumed by the
quiz-engine.

The quiz JSON describes **what should happen**, never **how it is executed**.

The engine loads the quiz, validates it, and orchestrates execution without
interpreting quiz logic.

---

## Purpose

A quiz is defined as a **workflow of nodes**, similar to N8N workflows.

Each node:
- references a plugin
- contains plugin-specific configuration
- produces a result at runtime

The engine:
- controls sequencing
- manages session state
- delegates execution to plugins

---

## Core Principles

- Quiz JSON is configuration, not code
- Quiz JSON must be JSON-serializable
- Quiz JSON must be portable and copy/paste friendly
- The engine must never interpret plugin configuration

---

## Top-Level Structure

A quiz JSON document MUST contain:

- `schema_version`
- `engine_version`
- `quiz_id`
- `metadata`
- `nodes`
- `edges`

---

## Versioning

- `schema_version` identifies the quiz JSON schema version
- `engine_version` declares the engine version used to create the quiz

Compatibility rules:
- Same MAJOR engine version → compatible
- Different MAJOR engine version → incompatible

---

## Metadata

`metadata` is informational only and must not affect execution.

Recommended fields:
- `title`
- `description`
- `author`
- `tags`
- `created_at`

---

## Nodes

Each quiz consists of a list of nodes.

Each node MUST define:

- `node_id`
- `plugin_id`
- `plugin_version`
- `config`

Rules:
- `node_id` must be unique within the quiz
- `config` is plugin-owned and opaque to the engine
- The engine must pass `config` unchanged to the plugin

---

## Edges

`edges` define the execution order of nodes.

Each edge MUST define:
- `from`
- `to`

Rules:
- Execution is linear by default
- Branching is allowed but optional in v1
- The engine must not interpret edge semantics beyond sequencing

For v1:
- A simple linear chain is sufficient
- Multiple outgoing edges may be ignored or rejected

---

## Execution Model

At runtime:
1. The engine selects the first node
2. The engine instantiates the referenced plugin
3. The plugin executes and produces a `QuestionResult`
4. The engine stores the result
5. The engine moves to the next node according to `edges`

The engine must not:
- skip nodes
- reorder nodes
- inject logic between nodes

---

## Plugin Responsibility

Plugins are responsible for:
- interpreting `config`
- validating their configuration
- handling player answers
- producing results

The engine is responsible for:
- lifecycle control
- state transitions
- result storage

---

## Error Handling

If a quiz JSON is invalid:
- the engine must reject it explicitly
- no partial execution is allowed

If a plugin fails during execution:
- the error must be propagated
- the session must move to a safe state

---

## Minimal Valid Quiz (Conceptual)

A minimal quiz:
- contains at least one node
- has a valid linear edge
- references compatible plugins

Plugins may define additional validation rules.

---

## Non-Goals (v1)

- Dynamic branching based on answers
- Conditional logic
- Loops
- Variables shared between nodes

These may be introduced in later schema versions.

---

## Final Rule

> The quiz defines the path.
> Plugins define the meaning.
> The engine defines the time.

