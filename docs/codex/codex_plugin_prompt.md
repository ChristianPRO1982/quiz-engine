You are developing a **stand-alone quiz-engine plugin**, not the engine itself.

Use the following Markdown documents as **authoritative specifications**:
* `docs/plugins/plugin_contracts_v0.md`
* `docs/plugins/plugin_lifecycle_v0.md`
* `docs/plugins/ws_messages_v0.md`
* `docs/plugins/plugin_examples_payloads.md`
* `docs/plugins/determinism_and_seed.md`
* `docs/plugins/plugin_packaging_and_manifest.md`

Your goal is to implement one plugin that fully respects the V0 runtime contracts.

Constraints:
* The plugin owns all business logic:
  * answer interpretation
  * scoring rules (speed, inverse ranking, group effects, etc.)
  * grading (0/1, /20, custom scales)
  * reveal logic and visuals (PluginFrame)
* The plugin must treat quiz-engine as dumb:
  * engine only transports events and frames
  * engine only aggregates `ScoreDelta.delta_score`
* All payloads must be JSON-serializable (JSON-like only).
* All time-based logic must rely on server_received_at.
* If randomness or bots are used, the plugin must require and use `random_seed`.

Scope:
* Implement only the plugin package.
* No direct access to quiz-engine internals.
* No database usage.
* No UI framework assumptions (frames are pure view-models).

Required structure:
* A class implementing `IPlugin`
* A stage runtime class implementing `IStageRuntime`
* A valid `PluginManifest`
* Clear separation between:
  * stage configuration (`plugin_spec`)
  * runtime state (internal)
  * replayable state (`plugin_state_out`)

Workflow:
1. Read the Markdown specs carefully.
2. Implement the plugin respecting lifecycle and determinism rules.
3. Include minimal unit tests for:
  * deterministic behavior
  * correct handling of PlayerEvent
  * valid StageOutcome output
4. Do not invent new contracts or fields.

If something seems ambiguous, follow the Markdown strictly and prefer the most conservative interpretation.