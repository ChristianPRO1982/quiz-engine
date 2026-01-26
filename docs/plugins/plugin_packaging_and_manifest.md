# Plugin Packaging & Manifest

## Goal
Plugins are standalone Python packages/modules that quiz-engine can load.

## Required manifest fields
PluginManifest:
- plugin_id (stable unique)
- plugin_version
- display_name
- contract_version == "v0"

Optional:
- capabilities: dict
  Suggested keys:
  - live_frames: bool
  - multi_phase: bool
  - supports_host_actions: bool
  - uses_random_seed: bool
  - supports_no_score: bool

## Conventions
- plugin_id: lowercase, snake-like or kebab-like, e.g. "mcq", "slider", "wordcloud"
- contract_version: "v0" must match engine contracts

## Loading expectations (engine-side)
Engine may load plugins by:
- explicit registration in code (initially)
- later: entrypoints / module discovery

Your plugin must expose:
- a class implementing IPlugin
- returning PluginManifest and stage runtime instances

## Standalone guarantee
A plugin should not require:
- access to engine DB
- access to engine internal services
- any secret keys by default

If a plugin needs assets, it should reference them by IDs/URLs via attachments or frames.
