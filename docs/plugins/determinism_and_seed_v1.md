# Determinism & Seed — v1
Deterministic execution model for plugins

Status: REFERENCE
Scope: Plugin implementation guide

Authoritative runtime definitions:
- docs/contracts/runtime_schema_v1.md
- docs/contracts/engine_plugin_interfaces_v1.md
- docs/contracts/scoreEntry_contract_v1.md

This document explains how to implement deterministic plugins.

---

# 1. Why Determinism Matters

Determinism guarantees:

- Reproducible results
- Replay capability
- Debug reliability
- Auditability
- Consistent scoring

Given identical:

- stage config
- seed
- player actions

resolve() must produce identical StageOutcome.

---

# 2. The Seed Contract

Each stage receives:

seed: integer

The engine guarantees:

- Same seed on replay
- Seed stability across resolution
- Seed uniqueness per stage (recommended)

The plugin must use this seed
for all pseudo-random behavior.

---

# 3. Allowed Randomness

Plugins may use pseudo-random generation
only if:

- Initialized with provided seed
- Fully deterministic
- No external entropy

Example (Python):

```python
import random

rng = random.Random(seed)
value = rng.randint(0, 10)
````

Never use:

* random without seed
* time-based randomness
* uuid-based randomness
* OS entropy

```

---

# 4. Forbidden Non-Determinism

Plugins must not:

- Call datetime.now() inside resolve()
- Fetch external API data during resolve()
- Query database during resolve()
- Depend on system clock
- Depend on thread scheduling

All resolution inputs must be explicit.

---

# 5. Player Action Order

Player actions must be treated deterministically.

If action order matters:

- Sort by timestamp (stored by engine)
- Or sort by player_id

Order must be stable.

---

# 6. Deterministic Scoring

ScoreEntry generation must depend only on:

- config
- seed
- player actions

Scoring must be:

- Integer-only
- Reproducible
- Stable across runs

No floating-point accumulation.

---

# 7. Intermediate Updates

If plugin emits STAGE_UPDATE:

- It must derive from deterministic state
- It must not leak unstable values

Intermediate state must not affect final determinism.

---

# 8. Replay Model (Future-Proofing)

A replay system may:

- Re-run initialize()
- Re-feed player actions
- Call resolve()

The plugin must produce identical:

- public_state
- private_state
- score_entries

---

# 9. Testing Determinism

Recommended plugin test:

1. Run stage with seed X
2. Capture StageOutcome
3. Re-run with same inputs
4. Assert equality

---

# 10. Determinism Summary

Plugins must be:

- Pure relative to input + seed
- Free of external side effects
- Free of hidden randomness

The engine does not enforce determinism.
Plugins are responsible.
