"""Tests for sandbox fallback slide plugin."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PlayerIdentity,
    StageContext,
    StageDefinition,
    StageTrace,
)
from quiz_engine.plugins.sandbox_slide import (
    SandboxSlidePlugin,
    _build_sandbox_payload,
    _coerce_body_format,
    _coerce_text,
    _fallback_title,
)


def _stage(
    *,
    plugin_id: str = "slide",
    plugin_spec: dict | None = None,
) -> StageDefinition:
    return StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id=plugin_id,
        stage_kind="slide",
        engine_prompt={},
        plugin_spec=plugin_spec or {},
    )


def _context(stage: StageDefinition) -> StageContext:
    return StageContext(
        session_id="session-1",
        quiz_id="quiz-1",
        stage=stage,
        server_now=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        players=[
            PlayerIdentity(
                player_id="p1",
                display_name="Alice",
                is_authenticated=False,
                participation_mode="GUEST",
                consents={"gameplay_identity": True, "email_results": False},
            )
        ],
    )


def test_sandbox_slide_plugin_rejects_wrong_plugin_id() -> None:
    plugin = SandboxSlidePlugin()
    with pytest.raises(ValueError, match="cannot create runtime"):
        plugin.create_runtime("session-1", _stage(plugin_id="mcq"))


def test_sandbox_slide_runtime_open_and_outcome() -> None:
    plugin = SandboxSlidePlugin()
    stage = _stage(
        plugin_spec={
            "content": {
                "title": "  Intro  ",
                "body": "  Body  ",
                "body_format": "markdown",
                "media": {"type": "image", "src": "https://cdn/x.png"},
            }
        }
    )
    runtime = plugin.create_runtime("session-1", stage)
    frames = runtime.on_stage_open(_context(stage))
    assert frames is not None
    assert frames[0].payload["title"] == "Intro"
    assert frames[0].payload["body"] == "Body"
    assert frames[0].payload["body_format"] == "markdown"
    assert frames[0].payload["media"]["src"] == "https://cdn/x.png"

    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    event = PlayerEvent(
        event_id="e1",
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        player_id="p1",
        type="CLICK",
        server_received_at=datetime(2024, 1, 1, 12, 0, 1, tzinfo=UTC),
        payload={},
    )
    assert runtime.on_player_event(event=event, trace=trace) is None
    assert runtime.on_host_action(action={}, trace=trace) is None
    assert runtime.is_finished(trace) is False

    outcome = runtime.build_outcome(trace)
    assert outcome.plugin_state_out == {"sandbox_mode": True}


def test_build_payload_supports_none_media_and_defaults() -> None:
    stage = _stage(
        plugin_spec={
            "title": "",
            "body": "",
            "media": {"type": "none", "src": "x"},
        }
    )
    payload = _build_sandbox_payload(stage)
    assert payload["title"] == "Stage 1"
    assert payload["body"] == "Slide content rendered by sandbox fallback plugin."
    assert payload["body_format"] == "text"
    assert payload["media"] == {"type": "none", "src": None}


def test_build_payload_ignores_invalid_media_and_uses_metadata_title() -> None:
    stage = _stage(
        plugin_spec={"content": {"body": "B", "media": {"type": "video", "src": "x"}}}
    )
    stage.metadata = {"title": "  Stage title  "}
    payload = _build_sandbox_payload(stage)
    assert payload["title"] == "Stage title"
    assert "media" not in payload


def test_sandbox_coercion_helpers_cover_all_branches() -> None:
    assert _fallback_title(_stage()) == "Stage 1"
    stage = _stage()
    stage.metadata = {"title": "  Nice  "}
    assert _fallback_title(stage) == "Nice"

    assert _coerce_body_format(" markdown ") == "markdown"
    assert _coerce_body_format("html") == "text"
    assert _coerce_text("  x  ", "d") == "x"
    assert _coerce_text(None, "d") == "d"
