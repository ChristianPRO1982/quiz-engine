"""Tests for WebSocket message envelopes."""

from __future__ import annotations

import pytest

from quiz_engine.ws.messages import build_envelope


def test_build_envelope_returns_type_and_payload() -> None:
    envelope = build_envelope("PLAYER_EVENT", {"event_id": "e1"})
    assert envelope["type"] == "PLAYER_EVENT"
    assert envelope["payload"] == {"event_id": "e1"}


def test_build_envelope_rejects_empty_type() -> None:
    with pytest.raises(ValueError):
        build_envelope("", {})


def test_build_envelope_rejects_non_json_payload() -> None:
    with pytest.raises(ValueError):
        build_envelope("PLAYER_EVENT", {"bad": object()})
