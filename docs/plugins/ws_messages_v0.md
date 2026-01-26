# WS Messages V0 (plugin expectations)

## Envelope
All WS messages are JSON:
{ "type": "EVENT_NAME", "payload": { ... } }

Engine routes messages to the active plugin runtime of the current stage.

---

## Incoming (plugin receives via engine callbacks)
### PLAYER_EVENT
Represents a player action:
payload maps to PlayerEvent transport fields.
- type: "SUBMIT" | "CHANGE" | "CLEAR"
- payload: plugin-defined dict

### HOST_ACTION (optional)
Host interactions (plugin-defined):
payload is a dict you define, e.g.:
- { "action": "REVEAL" }
- { "action": "NEXT_PHASE" }
- { "action": "LOCK" }

### ENGINE_STAGE_OPENED / ENGINE_STAGE_CLOSED (optional)
Engine lifecycle signals.
Usually you do not need them if you implement on_stage_open/build_outcome.

---

## Outgoing (plugin emits frames; engine broadcasts)
### PLUGIN_FRAME
Engine broadcasts frames returned by plugin callbacks.

Recommended payload shape:
- audience: "HOST" | "PLAYERS" | "ALL"
- frame_type: "VIEW_MODEL" | "PATCH" | "REVEAL" | ...
- payload: JSON-like view model

---

## Recommended minimal frame patterns
### VIEW_MODEL
Full render state snapshot:
payload = { "view": "...", "data": {...} }

### PATCH
Small incremental updates:
payload = { "patch": {...} }

---

## Notes
- Keep frames small and frequent rather than huge dumps.
- Use server_received_at for all timing fairness.
