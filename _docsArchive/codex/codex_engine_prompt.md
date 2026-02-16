You are working **only on quiz-engine**, not on plugins.

Use the following Markdown documents as **authoritative specifications** (relative to the project root):

Contracts (runtime and interfaces):
- `./docs/contracts/runtime_schema_v0.md`
- `./docs/contracts/engine_plugin_interfaces_v0.md`
- `./docs/contracts/README.md`

Sprint scope (implementation constraints):
- `./docs/sprints/sprint_1_plan.md`
- `./docs/sprints/sprint_1_configuration.md`
- `./docs/sprints/sprint_1_db_schema.md`
- `./docs/sprints/sprint_1_migrations.md`
- `./docs/sprints/sprint_1_decisions.md`

Implementation workflow:
- `./docs/codex/codex_task_list.md`

Contracts define the **allowed formats and invariants**.
Sprint documents define **what must and must not be implemented in this sprint**.

Your goal is to:
- implement the runtime contracts V0
- refactor existing code when necessary so that **all runtime data structures, WS messages, and persistence respect these contracts**
- implement only what is included in Sprint 1 documents
- remove or adapt any existing structure that violates contracts or sprint scope

Constraints (non-negotiable):
- quiz-engine is intentionally **dumb**:
  - never interpret answers
  - never implement scoring rules
  - only aggregate `ScoreDelta.delta_score`
- Do NOT invent new fields or formats.
- All runtime objects crossing boundaries (WS, storage, replay) must be **JSON-serializable**.
- All timestamps must be handled in **UTC ISO 8601**.
- Enforce all invariants described in the contracts.
- Follow **PEP8**, modular code, and write tests for each invariant.

Scope:
- Engine-side Python code only.
- No plugin business logic.
- Use a **dummy plugin** only for tests.
- No UI or template work.

Workflow rules:
1. Read all documents listed above before writing any code.
2. Follow the phases in `codex_task_list.md` strictly and in order.
3. Respect Sprint 1 scope:
   - do not implement features not explicitly included
   - do not add hooks or placeholders for future sprints
4. When existing code conflicts with a contract or sprint rule:
   - refactor or remove it
   - update tests accordingly
5. Do not prepare for future features unless explicitly documented.

If a requirement seems ambiguous:
- STOP coding
- ask for clarification
- do NOT guess or invent behavior.
