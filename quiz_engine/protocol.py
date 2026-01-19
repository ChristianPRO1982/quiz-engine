"""WebSocket protocol helpers and validation."""

from dataclasses import dataclass
from typing import Any, Optional

PROTOCOL_VERSION = "1"

CLIENT_EVENTS = {
    "create_session",
    "join_session",
    "leave_session",
    "host_start",
    "host_end",
}

ROLE_HOST = "host"
ROLE_PLAYER = "player"


@dataclass
class EventEnvelope:
    v: str
    type: str
    session_code: str
    payload: dict[str, Any]


class ProtocolError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        session_code: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.session_code = session_code
        self.details = details or {}


def build_event(session_code: str, event_type: str, payload: dict[str, Any]) -> dict:
    return {
        "v": PROTOCOL_VERSION,
        "type": event_type,
        "session_code": session_code,
        "payload": payload,
    }


def parse_event(data: Any) -> EventEnvelope:
    if not isinstance(data, dict):
        raise ProtocolError("invalid_envelope", "Envelope must be an object.")

    for field in ("v", "type", "session_code", "payload"):
        if field not in data:
            raise ProtocolError(
                "invalid_envelope",
                f"Missing field '{field}'.",
                session_code=_safe_session_code(data),
            )

    if data.get("v") != PROTOCOL_VERSION:
        raise ProtocolError(
            "invalid_version",
            "Unsupported protocol version.",
            session_code=_safe_session_code(data),
            details={"expected": PROTOCOL_VERSION},
        )

    event_type = data.get("type")
    if event_type not in CLIENT_EVENTS:
        raise ProtocolError(
            "unknown_event",
            "Unknown event type.",
            session_code=_safe_session_code(data),
            details={"type": event_type},
        )

    session_code = data.get("session_code")
    if not isinstance(session_code, str):
        raise ProtocolError(
            "invalid_envelope",
            "session_code must be a string.",
            session_code=_safe_session_code(data),
        )

    payload = data.get("payload")
    if not isinstance(payload, dict):
        raise ProtocolError(
            "invalid_envelope",
            "payload must be an object.",
            session_code=session_code,
        )

    _validate_payload(event_type, payload, session_code)

    return EventEnvelope(
        v=data["v"],
        type=event_type,
        session_code=session_code,
        payload=payload,
    )


def _validate_payload(event_type: str, payload: dict[str, Any], session_code: str) -> None:
    if event_type == "join_session":
        nickname = payload.get("nickname")
        if not isinstance(nickname, str):
            raise ProtocolError(
                "invalid_payload",
                "nickname must be a string.",
                session_code=session_code,
            )
        if nickname.strip() == "":
            raise ProtocolError(
                "invalid_payload",
                "nickname must not be empty.",
                session_code=session_code,
            )
        return

    if payload:
        raise ProtocolError(
            "invalid_payload",
            "payload must be an empty object for this event.",
            session_code=session_code,
        )


def _safe_session_code(data: dict[str, Any]) -> str:
    session_code = data.get("session_code")
    return session_code if isinstance(session_code, str) else ""
