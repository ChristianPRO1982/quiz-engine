"""Tests for runtime contract models."""

from __future__ import annotations

from datetime import UTC, datetime
from math import inf, nan

import pytest

from quiz_engine.contracts.runtime_models import (
    GradeDelta,
    PlayerEvent,
    PlayerIdentity,
    PluginFrame,
    PluginManifest,
    ScoreDelta,
    StageContext,
    StageDefinition,
    StageOutcome,
    StageTrace,
)


def _utc_now() -> datetime:
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


def _stage_definition() -> StageDefinition:
    return StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id="plugin.quiz",
        stage_kind="question",
        engine_prompt={"title": "Hello"},
        plugin_spec={"question": "What?"},
        time_limit_ms=30000,
        random_seed=42,
        metadata={"difficulty": "easy"},
    )


def _player_identity() -> PlayerIdentity:
    return PlayerIdentity(
        player_id="player-1",
        display_name="Alice",
        is_authenticated=True,
        participation_mode="LOGGED",
        consents={"gameplay_identity": True, "email_results": True},
        metadata={"team": "blue"},
    )


def _player_event() -> PlayerEvent:
    return PlayerEvent(
        event_id="event-1",
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        player_id="player-1",
        type="SUBMIT",
        server_received_at=_utc_now(),
        payload={"answer": "A"},
        client_sent_at=_utc_now(),
        seq=1,
        correlation_id="corr-1",
    )


def _stage_trace() -> StageTrace:
    return StageTrace(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        started_at=_utc_now(),
        events=[_player_event()],
        ended_at=_utc_now(),
        engine_events=[{"kind": "engine", "detail": "opened"}],
    )


def _plugin_frame() -> PluginFrame:
    return PluginFrame(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        plugin_id="plugin.quiz",
        audience="ALL",
        frame_type="VIEW_MODEL",
        payload={"text": "Hello"},
        sent_at=_utc_now(),
        seq=2,
    )


def _score_delta() -> ScoreDelta:
    return ScoreDelta(
        player_id="player-1",
        delta_score=10.5,
        meta={"source": "test"},
        reason="correct",
    )


def _grade_delta() -> GradeDelta:
    return GradeDelta(
        player_id="player-1",
        value=3.0,
        max_value=5.0,
        scale="points",
        meta={"note": "ok"},
    )


def _stage_outcome() -> StageOutcome:
    return StageOutcome(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        plugin_id="plugin.quiz",
        completed_at=_utc_now(),
        score_deltas=[_score_delta()],
        grade_deltas=[_grade_delta()],
        plugin_state_out={"state": "done"},
        render_summary={"summary": "ok"},
        attachments={"file": "none"},
        next_hint={"next": "stage-2"},
    )


def _stage_context() -> StageContext:
    return StageContext(
        session_id="session-1",
        quiz_id="quiz-1",
        stage=_stage_definition(),
        server_now=_utc_now(),
        players=[_player_identity()],
        scoreboard_snapshot={"player-1": 10.0},
        plugin_state_in={"state": "start"},
        transport_hints={"reliable": True},
        session_flags={"flag": "demo"},
    )


@pytest.mark.parametrize("invalid_index", [-1])
def test_stage_definition_rejects_negative_index(invalid_index: int) -> None:
    with pytest.raises(ValueError):
        StageDefinition(
            stage_id="stage-1",
            stage_index=invalid_index,
            plugin_id="plugin.quiz",
            stage_kind="question",
            engine_prompt={},
            plugin_spec={},
        )


def test_stage_definition_rejects_non_json_prompt() -> None:
    with pytest.raises(ValueError):
        StageDefinition(
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            stage_kind="question",
            engine_prompt={"bad": object()},
            plugin_spec={},
        )


def test_player_identity_requires_gameplay_consent() -> None:
    with pytest.raises(ValueError):
        PlayerIdentity(
            player_id="player-1",
            display_name="Alice",
            consents={"email_results": False},
        )


def test_player_identity_rejects_logged_mode_when_unauthenticated() -> None:
    with pytest.raises(ValueError):
        PlayerIdentity(
            player_id="player-1",
            display_name="Alice",
            is_authenticated=False,
            participation_mode="LOGGED",
            consents={"gameplay_identity": True, "email_results": False},
        )


def test_player_identity_rejects_email_results_for_guest_mode() -> None:
    with pytest.raises(ValueError):
        PlayerIdentity(
            player_id="player-1",
            display_name="Alice",
            is_authenticated=True,
            participation_mode="GUEST",
            consents={"gameplay_identity": True, "email_results": True},
        )


@pytest.mark.parametrize("value", [nan, inf, -inf])
def test_score_delta_rejects_non_finite(value: float) -> None:
    with pytest.raises(ValueError):
        ScoreDelta(player_id="player-1", delta_score=value)


@pytest.mark.parametrize("value", [0, -1.0])
def test_grade_delta_requires_positive_max(value: float) -> None:
    with pytest.raises(ValueError):
        GradeDelta(player_id="player-1", value=1.0, max_value=value)


def test_stage_trace_requires_matching_event_ids() -> None:
    event = _player_event()
    event.stage_id = "stage-2"
    with pytest.raises(ValueError):
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            events=[event],
        )


def test_player_event_rejects_non_json_payload() -> None:
    with pytest.raises(ValueError):
        PlayerEvent(
            event_id="event-1",
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            player_id="player-1",
            type="SUBMIT",
            server_received_at=_utc_now(),
            payload={"bad": object()},
        )


def test_plugin_frame_rejects_non_json_payload() -> None:
    with pytest.raises(ValueError):
        PluginFrame(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            audience="ALL",
            frame_type="VIEW_MODEL",
            payload={"bad": object()},
            sent_at=_utc_now(),
        )


@pytest.mark.parametrize(
    "builder",
    [
        lambda: PluginManifest(
            plugin_id="plugin.quiz",
            plugin_version="1.0.0",
            display_name="Quiz",
            schema_version="v0",
            description="demo",
            capabilities={"frames": True},
        ),
        _stage_definition,
        _player_identity,
        _stage_context,
        _player_event,
        _stage_trace,
        _plugin_frame,
        _score_delta,
        _grade_delta,
        _stage_outcome,
    ],
)
def test_transport_roundtrip(builder) -> None:
    model = builder()
    data = model.to_transport_dict()
    restored = model.__class__.from_transport_dict(data)
    assert restored == model


def test_plugin_manifest_rejects_invalid_optional_fields() -> None:
    with pytest.raises(ValueError, match="must be a non-empty string"):
        PluginManifest(
            plugin_id="",
            plugin_version="1.0.0",
            display_name="Quiz",
            schema_version="v0",
        )
    with pytest.raises(ValueError, match="schema_version must be 'v0'"):
        PluginManifest(
            plugin_id="p",
            plugin_version="1.0.0",
            display_name="Quiz",
            schema_version="v1",
        )
    with pytest.raises(ValueError, match="description must be a string"):
        PluginManifest(
            plugin_id="p",
            plugin_version="1.0.0",
            display_name="Quiz",
            schema_version="v0",
            description=123,  # type: ignore[arg-type]
        )


def test_stage_context_rejects_invalid_stage_and_players() -> None:
    with pytest.raises(ValueError, match="stage must be a StageDefinition"):
        StageContext(
            session_id="session-1",
            quiz_id="quiz-1",
            stage="bad",  # type: ignore[arg-type]
            server_now=_utc_now(),
            players=[],
        )

    with pytest.raises(ValueError, match="players must be a list"):
        StageContext(
            session_id="session-1",
            quiz_id="quiz-1",
            stage=_stage_definition(),
            server_now=_utc_now(),
            players="bad",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="players must contain PlayerIdentity"):
        StageContext(
            session_id="session-1",
            quiz_id="quiz-1",
            stage=_stage_definition(),
            server_now=_utc_now(),
            players=[object()],  # type: ignore[list-item]
        )


def test_stage_trace_rejects_invalid_events_and_engine_events() -> None:
    with pytest.raises(ValueError, match="events must be a list"):
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            events="bad",  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="events must contain PlayerEvent"):
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            events=[object()],  # type: ignore[list-item]
        )

    with pytest.raises(ValueError, match="event stage_index mismatch"):
        event = _player_event()
        event.stage_index = 1
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            events=[event],
        )

    with pytest.raises(ValueError, match="engine_events must be a list"):
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            engine_events={"bad": True},  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="engine_events entry must be a dict"):
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=_utc_now(),
            engine_events=[1],  # type: ignore[list-item]
        )


def test_score_delta_and_grade_delta_reject_invalid_types() -> None:
    with pytest.raises(ValueError, match="delta_score must be a number"):
        ScoreDelta(player_id="p1", delta_score=True)
    with pytest.raises(ValueError, match="reason must be a string"):
        ScoreDelta(player_id="p1", delta_score=1.0, reason=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="value must be a number"):
        GradeDelta(player_id="p1", value=True)
    with pytest.raises(ValueError, match="max_value must be a number"):
        GradeDelta(player_id="p1", value=1.0, max_value="x")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="scale must be a string"):
        GradeDelta(player_id="p1", value=1.0, scale=1)  # type: ignore[arg-type]


def test_stage_outcome_rejects_invalid_delta_collections() -> None:
    with pytest.raises(ValueError, match="score_deltas must be a list"):
        StageOutcome(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            completed_at=_utc_now(),
            score_deltas="bad",  # type: ignore[arg-type]
        )
    with pytest.raises(
        ValueError,
        match="score_deltas must contain ScoreDelta objects",
    ):
        StageOutcome(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            completed_at=_utc_now(),
            score_deltas=[object()],  # type: ignore[list-item]
        )
    with pytest.raises(ValueError, match="grade_deltas must be a list"):
        StageOutcome(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            completed_at=_utc_now(),
            grade_deltas="bad",  # type: ignore[arg-type]
        )
    with pytest.raises(
        ValueError,
        match="grade_deltas must contain GradeDelta objects",
    ):
        StageOutcome(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            plugin_id="plugin.quiz",
            completed_at=_utc_now(),
            grade_deltas=[object()],  # type: ignore[list-item]
        )
