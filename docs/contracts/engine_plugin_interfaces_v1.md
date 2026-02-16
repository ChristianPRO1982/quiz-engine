# Engine ↔ Plugin Interfaces — v1
Technical interface contract between engine and plugins

Status: CANONICAL (interface-level)
Schema version: v1
Scope: Runtime invocation contract

This document defines the minimal callable interface
a plugin must implement.

Data models:
- docs/contracts/runtime_schema_v1.md
- docs/contracts/scoreEntry_contract_v1.md

Behavioral rules:
- docs/contracts/engine_responsibilities_v1.md
- docs/contracts/runtime_plugin_io_v1.md

---

# 1. Plugin Resolution

The engine resolves a plugin using:

plugin_key → plugin instance

Plugin registration is outside scope of this document.

---

# 2. Required Plugin Interface

Each plugin must expose a runtime class
implementing the following interface:

```python
class StageRuntime:

    def initialize(
        self,
        config: dict,
        seed: int,
        players: list[str],
    ) -> None:
        """
        Called once when stage becomes ACTIVE.
        Must prepare deterministic internal state.
        """

    def handle_player_action(
        self,
        player_id: str,
        action: dict,
    ) -> None:
        """
        Called when a player sends an action.
        Must update internal state only.
        Must not emit StageOutcome.
        """

    def resolve(self) -> dict:
        """
        Called when stage resolution is triggered.
        Must return a StageOutcome structure
        as defined in runtime_schema_v1.md.
        Must be deterministic.
        """
```

---

# 3. Determinism Rules

Plugin must:

* Use provided seed
* Avoid non-deterministic randomness
* Avoid external I/O during resolve()
* Avoid time-based logic in scoring

Given identical:

* config
* seed
* player actions

resolve() must return identical StageOutcome.

---

# 4. Engine Invocation Order

For each stage:

1. Instantiate StageRuntime
2. Call initialize(...)
3. Route player actions via handle_player_action(...)
4. Call resolve()
5. Persist StageOutcome

Engine must never:

* Call resolve() twice
* Modify plugin state
* Patch returned outcome

---

# 5. Optional Capabilities

Plugins may internally:

* Maintain transient state
* Track action history
* Emit intermediate public updates
  (via engine callback mechanism, not defined here)

But must not:

* Persist external state
* Access engine storage directly
* Modify other stages

---

# 6. StageOutcome Contract

resolve() must return a dictionary matching:

runtime_schema_v1.md

Specifically:

* stage_id
* plugin_key
* public_state
* private_state
* score_entries

score_entries must conform to:

scoreEntry_contract_v1.md

Engine will validate structural integrity only.

---

# 7. Error Contract

If plugin cannot resolve:

* raise an exception
* engine handles STAGE_ERROR

Plugin must not fabricate partial outcomes.

---

# 8. Statelessness Across Stages

A plugin instance:

* Is scoped to a single stage
* Must not retain global cross-session state
* Must not depend on previous stages

Cross-stage logic must be encoded in stage config.

---

# 9. Strict Prohibitions

Plugins must not:

* Call engine persistence
* Compute global rankings
* Modify session state
* Override stage lifecycle
* Inject non-integer scoring

---

# 10. Extensibility

Future versions may add:

* pre_resolve hooks
* validation hooks
* structured action schemas

But must preserve:

* Deterministic resolve()
* Integer-only scoring
* Dumb engine boundary
