"""Unit and integration tests for the built-in SLIDE plugin."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quiz_engine.contracts.runtime_models import (
    PlayerIdentity,
    StageContext,
    StageDefinition,
    StageTrace,
)
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.plugins.slide import SlidePlugin, SlideStageRuntime
from quiz_engine.runtime.stage_runner import StageRunner
from quiz_engine.ws.messages import PLUGIN_FRAME, build_envelope


def _player() -> PlayerIdentity:
    return PlayerIdentity(
        player_id="player-1",
        display_name="Alice",
        is_authenticated=True,
        participation_mode="LOGGED",
        consents={"gameplay_identity": True, "email_results": True},
    )


def _slide_stage(stage_id: str = "stage-1", stage_index: int = 0) -> StageDefinition:
    return StageDefinition(
        stage_id=stage_id,
        stage_index=stage_index,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={
            "schema_version": "v1",
            "title": "Welcome",
            "body": "Round starts now.",
            "body_format": "markdown",
            "media": {
                "type": "image",
                "src": "https://cdn.example.org/welcome.png",
            },
        },
    )


def _context(stage: StageDefinition, now: datetime) -> StageContext:
    return StageContext(
        session_id="session-1",
        quiz_id="quiz-1",
        stage=stage,
        server_now=now,
        players=[_player()],
    )


def test_slide_plugin_creates_runtime_with_valid_spec() -> None:
    plugin = SlidePlugin()

    runtime = plugin.create_runtime("session-1", _slide_stage())

    assert isinstance(runtime, SlideStageRuntime)


def test_slide_plugin_rejects_invalid_spec() -> None:
    plugin = SlidePlugin()
    bad_stage = StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={
            "schema_version": "v1",
        },
    )

    with pytest.raises(ValueError):
        plugin.create_runtime("session-1", bad_stage)


def test_slide_runtime_on_stage_open_emits_single_view_model_frame() -> None:
    plugin = SlidePlugin()
    stage = _slide_stage()
    runtime = plugin.create_runtime("session-1", stage)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    frames = runtime.on_stage_open(_context(stage, now))

    assert frames is not None
    assert len(frames) == 1
    frame = frames[0]
    assert frame.audience == "ALL"
    assert frame.frame_type == "VIEW_MODEL"
    assert frame.payload["title"] == "Welcome"
    assert frame.payload["body"] == "Round starts now."
    assert frame.payload["body_format"] == "markdown"
    assert frame.payload["media"]["type"] == "image"
    assert frame.sent_at == now


def test_slide_runtime_defaults_body_format_to_text_for_legacy_spec() -> None:
    plugin = SlidePlugin()
    stage = StageDefinition(
        stage_id="stage-legacy",
        stage_index=0,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={
            "schema_version": "v0",
            "type": "slide",
            "content": {"title": "Legacy", "body": "Plain"},
        },
    )
    runtime = plugin.create_runtime("session-1", stage)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    frames = runtime.on_stage_open(_context(stage, now))

    assert frames is not None
    assert frames[0].payload["body_format"] == "text"


def test_slide_runtime_accepts_v1_content_wrapper_shape() -> None:
    plugin = SlidePlugin()
    stage = StageDefinition(
        stage_id="stage-v1-wrapper",
        stage_index=0,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={
            "schema_version": "v1",
            "type": "slide",
            "content": {"title": "Wrapped", "body": "Body"},
        },
    )
    runtime = plugin.create_runtime("session-1", stage)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    frames = runtime.on_stage_open(_context(stage, now))

    assert frames is not None
    assert frames[0].payload["title"] == "Wrapped"


def test_slide_runtime_prefers_stage_metadata_title() -> None:
    plugin = SlidePlugin()
    stage = StageDefinition(
        stage_id="stage-meta-title",
        stage_index=0,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={
            "schema_version": "v1",
            "content": {"title": "Spec title", "body": "Body"},
        },
        metadata={"title": "Question title"},
    )
    runtime = plugin.create_runtime("session-1", stage)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    frames = runtime.on_stage_open(_context(stage, now))

    assert frames is not None
    assert frames[0].payload["title"] == "Question title"


def test_slide_runtime_build_outcome_returns_no_score() -> None:
    plugin = SlidePlugin()
    stage = _slide_stage()
    runtime = plugin.create_runtime("session-1", stage)
    ended_at = datetime(2024, 1, 1, 12, 1, 0, tzinfo=UTC)
    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        ended_at=ended_at,
    )

    outcome = runtime.build_outcome(trace)

    assert outcome.score_deltas is None
    assert outcome.grade_deltas is None
    assert outcome.render_summary is None
    assert outcome.plugin_state_out is None
    assert outcome.completed_at == ended_at


def test_slide_stage_opens_broadcasts_and_closes_with_engine_flow() -> None:
    registry = build_default_registry()
    plugin = registry.get("slide")
    assert plugin is not None
    stage = _slide_stage()
    open_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    close_at = datetime(2024, 1, 1, 12, 0, 8, tzinfo=UTC)
    runtime = plugin.create_runtime("session-1", stage)
    runner = StageRunner(runtime=runtime, clock=lambda: close_at)

    frames = runner.open_stage(_context(stage, open_at))
    envelope = build_envelope(PLUGIN_FRAME, frames[0].to_transport_dict())

    assert len(frames) == 1
    assert envelope["type"] == PLUGIN_FRAME
    assert envelope["payload"]["audience"] == "ALL"
    assert runner.maybe_close() is None

    outcome = runner.close_stage()

    assert outcome is not None
    assert outcome.stage_id == stage.stage_id
    assert outcome.score_deltas is None
    assert outcome.grade_deltas is None


def test_slide_session_can_continue_to_next_stage() -> None:
    registry = build_default_registry()
    plugin = registry.get("slide")
    assert plugin is not None

    stage_1 = _slide_stage(stage_id="stage-1", stage_index=0)
    stage_2 = _slide_stage(stage_id="stage-2", stage_index=1)

    runner_1 = StageRunner(
        runtime=plugin.create_runtime("session-1", stage_1),
        clock=lambda: datetime(2024, 1, 1, 12, 0, 5, tzinfo=UTC),
    )
    runner_1.open_stage(_context(stage_1, datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)))
    outcome_1 = runner_1.close_stage()

    runner_2 = StageRunner(
        runtime=plugin.create_runtime("session-1", stage_2),
        clock=lambda: datetime(2024, 1, 1, 12, 0, 10, tzinfo=UTC),
    )
    runner_2.open_stage(_context(stage_2, datetime(2024, 1, 1, 12, 0, 6, tzinfo=UTC)))
    outcome_2 = runner_2.close_stage()

    assert outcome_1.stage_index == 0
    assert outcome_2.stage_index == 1
