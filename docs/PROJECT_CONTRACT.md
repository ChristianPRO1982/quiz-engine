# Quiz-Engine — Project Contract

## 1. Purpose
This project aims to build a real-time quiz game engine designed for live sessions
(host + players via smartphones), prioritizing simplicity, robustness, and long-term
maintainability for a solo developer.

The goal is NOT to build features quickly, but to build a clean, extensible core
that can be safely evolved over time.

---

## 2. Product Philosophy
- Solo developer, “garage mode”
- Prefer clarity over cleverness
- Minimal viable architecture first
- Extensibility over premature optimization
- Breaking changes are acceptable (semantic versioning applies)

---

## 3. Roles (Fixed for V1)
- **Player**: joins a session and participates
- **Host**: creates and runs a session
- **Quiz Creator**: designs quizzes (future)
- **Admin**: manages global configuration (future)

No fine-grained permission system in V1.

---

## 4. Core Technical Principles
- Backend: **FastAPI**
- Real-time communication: **WebSocket**
- Server is the single source of truth
- Session state is:
  - **Stateful in memory during a session**
  - **Stateless between sessions**
- No quiz logic inside the engine core
- No plugin-specific logic inside the engine core

---

## 5. Architecture Rules
- One monorepo
- Clear separation between:
  - Engine core
  - Plugins
  - Contracts (schemas, events)
- Plugins live inside `/plugins/<plugin_name>/`
- Engine interacts with plugins only via a strict contract

---

## 6. Quiz & Plugin Model (Future-Oriented)
- A quiz is defined as a workflow of nodes (JSON)
- Plugins are written in Python
- JSON is used for configuration and data exchange only
- Each plugin:
  - Interprets its own JSON payload
  - Provides its own human-readable Markdown export
- The engine must never interpret quiz content

---

## 7. Versioning & Compatibility
- Semantic Versioning applies to the engine
- Quizzes declare the engine version they were created with
- Import rules:
  - Same MAJOR version → permissive import
  - Different MAJOR version → incompatible
- Breaking changes are allowed between MAJOR versions

---

## 8. Data & Privacy Principles
- Data minimization by default
- No persistent identity for players
- Session data:
  - Stored in memory during runtime
  - Checkpointed only at safe moments (end of question)
- No long-term storage without explicit consent
- Retention duration is configurable by admin

---

## 9. Session Design Principles
- Session lifecycle is explicit and finite
- Valid session states are limited and deterministic
- Recovery after crash is “soft”:
  - Resume from last completed step
  - Current step may be lost

---

## 10. Frontend Philosophy
- Frontend is intentionally minimal
- No frontend business logic
- Frontend reflects server state only
- UX must remain functional on smartphones

---

## 11. Testing & Quality
- Automated tests are mandatory
- Tests must cover:
  - Core state transitions
  - Event validation
  - WebSocket communication
- CI must be green before merging or releasing

---

## 12. Scope Discipline
- Each sprint has a clearly defined scope
- No feature creep inside a sprint
- Refactoring is allowed only when it reduces complexity
- One sprint = one clear technical objective

---

## 13. Definition of Done (Global)
A feature is considered done only if:
- It respects this contract
- It is tested
- It does not introduce coupling with future features
- It does not break the engine/plugin separation

---

## 14. Non-Goals
- No attempt to support every quiz type
- No attempt to build a full LMS
- No real-time analytics in V1
- No horizontal scaling in early versions

---

## 15. Guiding Rule
> If a future version of myself cannot understand or extend this system after
> several months away, the design has failed.
