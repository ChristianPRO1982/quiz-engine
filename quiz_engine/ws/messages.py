"""WebSocket message envelopes for quiz-engine."""

from __future__ import annotations

from typing import Any

from quiz_engine.contracts.serialization import ensure_json_like

CONNECT = "CONNECT"
JOIN_SESSION = "JOIN_SESSION"
LEAVE_SESSION = "LEAVE_SESSION"
HOST_START = "HOST_START"
HOST_NEXT_STAGE = "HOST_NEXT_STAGE"
HOST_END = "HOST_END"

SESSION_CREATED = "SESSION_CREATED"
LOBBY_SNAPSHOT = "LOBBY_SNAPSHOT"
PLAYER_JOINED = "PLAYER_JOINED"
PLAYER_LEFT = "PLAYER_LEFT"
SESSION_STATE_CHANGED = "SESSION_STATE_CHANGED"
STAGE_CHANGED = "STAGE_CHANGED"
ERROR = "ERROR"

PLAYER_EVENT = "PLAYER_EVENT"
PLUGIN_FRAME = "PLUGIN_FRAME"
ENGINE_STAGE_OPENED = "ENGINE_STAGE_OPENED"
ENGINE_STAGE_CLOSED = "ENGINE_STAGE_CLOSED"
ENGINE_SCORE_UPDATE = "ENGINE_SCORE_UPDATE"


def build_envelope(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(event_type, str) or event_type.strip() == "":
        raise ValueError("event_type must be a non-empty string.")
    if not isinstance(payload, dict):
        raise ValueError("payload must be a dict.")
    ensure_json_like(payload, "payload")
    return {"type": event_type, "payload": payload}
