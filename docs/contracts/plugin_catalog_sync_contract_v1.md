# Plugin Catalog Sync Contract — v1
Admin-triggered plugin discovery and database synchronization

Status: CANONICAL (operations + persistence)
Schema version: v1
Scope: Plugin discovery, catalog persistence, admin scan workflow

This contract defines how engine-quiz keeps a persisted catalog
of installed plugins aligned with filesystem reality.

---

# 1. Discovery Source

Plugins are discovered from the runtime plugin package namespace:

- `quiz_engine.plugins.*`

Internal modules that are not distributable plugins
may be excluded by engine policy.

---

# 2. Scan Authorization

Plugin scan can be triggered from Admin UI only by users
with admin capability.

Operational source of truth:

- `qe_user_role` contains role `admin`

---

# 3. Catalog Persistence Model

The engine persists discovered plugins in `qe_plugin_catalog`.

Minimum persisted fields:

- `plugin_key`
- `name`
- `version`
- `plugin_type`
- `manifest_payload`
- timestamps (`created_at`, `updated_at`, `last_scanned_at`)

`plugin_type` must use this enum-like value set:

- `info`
- `quiz`
- `scoreboard`
- `form`

---

# 4. Synchronization Rules

On each scan:

1. Discover currently available plugins.
2. Upsert each discovered plugin by `plugin_key`.
3. Delete catalog rows for plugins no longer discoverable.
4. Refresh in-memory runtime registry from current discovery.

Result: catalog exactly matches currently available plugins.

---

# 5. Failure Policy

If one plugin fails import/instantiation:

- scan continues for other plugins
- failed plugin is excluded from synced catalog
- failure must be reported in admin scan result

---

# 6. Non-Goals

This contract does NOT define:

- stage runtime payload schemas
- websocket envelope
- score aggregation logic
