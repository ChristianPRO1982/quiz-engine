# Contracts Index — quiz-engine

## Purpose

This document is the **single source of truth** for all technical contracts
used by the `quiz-engine` project.

A contract defines:
- a data format
- an exchange protocol
- or a lifecycle rule

All engine and plugin code MUST comply with these contracts.

If a behavior or format is not documented here, **it does not exist**.

---

## Contract Status Definitions

Each contract has a status:

- **STABLE**
  - Must not change without a strong justification
  - Any change requires:
    - version bump
    - updated documentation
    - updated fixtures
    - updated tests

- **DRAFT**
  - May evolve
  - Still mandatory if referenced
  - Changes must remain explicit and documented

---

## Contract List

### 1. WebSocket Protocol

- **File**: `ws_protocol_v1.md`
- **Status**: STABLE
- **Scope**:
  - WebSocket envelope
  - Event structure
  - Error format
  - Client ↔ Server communication rules

This contract is the backbone of all real-time interactions.

- **File**: `ws_protocol_v2.md`
- **Status**: DRAFT
- **Scope**:
  - WebSocket envelope
  - Event structure
  - Join approval flow during RUNNING
  - Error format

---

### 2. Session Lifecycle

- **File**: `session_lifecycle_v1.md`
- **Status**: STABLE
- **Scope**:
  - Session states
  - Valid transitions
  - Allowed events per state
  - Invalid transitions behavior

The engine must strictly enforce this lifecycle.

- **File**: `session_lifecycle_v2.md`
- **Status**: DRAFT
- **Scope**:
  - Session states
  - Valid transitions
  - Join approval during RUNNING
  - Host kick rules

---

### 3. Quiz JSON Format

- **File**: `quiz_json_v1.md`
- **Status**: DRAFT
- **Scope**:
  - Quiz structure
  - Metadata
  - Nodes / workflow definition
  - Versioning rules

The engine must not interpret quiz content, only load and pass it to plugins.

---

### 4. Plugin Contract

- **File**: `plugin_contract_v1.md`
- **Status**: DRAFT
- **Scope**:
  - Plugin responsibilities
  - Plugin manifest structure
  - Plugin lifecycle expectations
  - Engine ↔ Plugin interaction boundaries

All plugins must comply with this contract.

---

### 5. Result Contract

- **File**: `result_contract_v1.md`
- **Status**: DRAFT
- **Scope**:
  - QuestionResult structure
  - PlayerResult structure
  - Score delta handling
  - Opaque plugin-owned payloads

The engine stores results but must not interpret them.

---

### 6. HTTP API Contract

- **File**: `http_api_v1.md`
- **Status**: DRAFT
- **Scope**:
  - REST session creation
  - Host and Player pages
  - QR code endpoint
  - WebSocket endpoint transport details

---

## Versioning Rules

- All contracts are versioned
- Contract version changes must be explicit
- Breaking changes are allowed only with:
  - a contract version bump
  - updated examples
  - updated tests

Silent breaking changes are forbidden.

---

## Fixtures and Tests

Canonical examples for contracts are stored in: `tests/fixtures/contracts/`.

These fixtures are:
- normative references
- used for validation tests
- required to be updated when a contract changes

---

## Enforcement Rule

Any code that:
- bypasses a contract
- introduces undocumented formats
- weakens a STABLE contract

**must be rejected**.

Contracts take precedence over convenience.

---

## Final Note

> The long-term health of quiz-engine depends on strict contracts,

> not on clever implementations.

> Every file in docs/contracts/ MUST be listed here

> If a contract is added, this index MUST be updated in the same PR
