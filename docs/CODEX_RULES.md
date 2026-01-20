# CODEX_RULES.md
## Purpose

This document defines **non-negotiable working rules** for any AI-assisted code generation
(Codex, ChatGPT, or similar) on the `quiz-engine` project.

Its goal is to:
* preserve architectural integrity
* enforce contracts and formats
* prevent hidden coupling and premature intelligence in the engine

If a rule here conflicts with convenience or speed, **this document wins**.

## Golden Rule

> **The engine orchestrates.**

> **Plugins think.**

> **Formats rule everything.**

## 1. Scope of Codex Intervention

Codex is allowed to:
* implement features explicitly described in sprint documents
* refactor code only when it reduces complexity
* add tests required by the Definition of Done
* enforce contracts defined in docs/contracts/

Codex is NOT allowed to:
* invent new features
* interpret quiz or scoring logic inside the engine
* bypass or weaken existing contracts
* introduce ad-hoc formats or undocumented structures

## 2. Contract-First Development (MANDATORY)

Before writing or modifying any code, Codex MUST:

1. Read docs/contracts/CONTRACTS.md
2. Identify which contracts are:
    * `STABLE`
    * `DRAFT`
3. Ensure all data structures and exchanges strictly conform to them

## Forbidden

* Introducing a new field not documented in a contract
* Modifying a `STABLE` contract without explicit instruction
* Creating “temporary” or “internal” formats

If a format is needed and does not exist:
* STOP
* Propose a contract update first (documentation only)

## 3. Engine Purity Rules (Critical)

The engine core MUST NEVER:
* calculate scores
* interpret answers
* know what a “correct” response is
* know how many points a question gives
* branch logic based on quiz content

The engine MAY:
* store opaque results
* aggregate numeric deltas without interpretation
* broadcast events
* enforce session lifecycle rules

## 4. Plugin Boundary Rules

Codex MUST assume that:
* Plugins are the only place where intelligence lives
* Plugins own:
  * scoring rules
  * reveal / interlude logic
  * answer interpretation
* The engine interacts with plugins **only via contracts**

The engine must treat all plugin outputs as **opaque data**,
except for explicitly allowed generic fields (e.g. numeric score deltas).

## 5. Formats and Serialization Rules

All exchanged data MUST be:
* explicitly versioned
* serializable to JSON
* validated against a documented contract
* testable via fixtures

This applies to:
* WebSocket events
* REST payloads
* quiz definitions
* plugin manifests
* runtime answers
* question results

No Python-only objects may cross system boundaries without a JSON representation.

## 6. Versioning Rules

* Engine versioning follows Semantic Versioning
* All formats include a `schema_version`
* Breaking changes are allowed only with:
  * a version bump
  * updated documentation
  * updated fixtures
  * updated tests

Silent breaking changes are strictly forbidden.

## 7. Tests Are Part of the Contract

Codex MUST assume that:
* Tests are not optional
* A feature without tests is incomplete
* Fixtures in `tests/fixtures/contracts/` are canonical references

Any change to a format requires:
* updating the related fixtures
* updating or adding validation tests

Green CI is mandatory.

## 8. Sprint Discipline

Codex MUST strictly respect sprint scope:
* Only what is included in the current sprint may be implemented
* Anything listed as EXCLUDED must not appear, even partially
* “Preparing for the future” by adding hooks or logic is forbidden unless documented

## 9. Explicit Failure Over Silent Behavior

When something goes wrong:
* return explicit error events
* fail loudly
* prefer rejecting invalid input over guessing intent

The engine must never “try to be smart”.

## 10. If in Doubt

When Codex is unsure:
* STOP coding
* Ask for clarification
* Propose alternatives at the design level (not code)

Silence or assumptions are worse than asking.

## Final Reminder

> A clean engine with strict contracts scales better than a clever engine with hidden logic.