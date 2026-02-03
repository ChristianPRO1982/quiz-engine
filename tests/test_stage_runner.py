"""Tests for stage runner orchestration."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PlayerIdentity,
    PluginFrame,
    StageContext,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.plugins.interfaces import IStageRuntime
from quiz_engine.runtime.stage_runner import StageRunner


class DummyRuntime(IStageRuntime):
    def __init__(self) -> None:
        self.opened = False
        self.last_event: PlayerEvent | None = None
        self.finish_after_events = 1

    def on_stage_open(self, context: StageContext) -> list[PluginFrame] | None:
        self.opened = True
        return [
            PluginFrame(
                session_id=context.session_id,
                stage_id=context.stage.stage_id,
                stage_index=context.stage.stage_index,
                plugin_id=context.stage.plugin_id,
                audience="ALL",
                frame_type="VIEW_MODEL",
                payload={"opened": True},
                sent_at=context.server_now,
            )
        ]

    def on_player_event(
        self, event: PlayerEvent, trace: StageTrace
    ) -> list[PluginFrame] | None:
        self.last_event = event
        return [
            PluginFrame(
                session_id=event.session_id,
                stage_id=event.stage_id,
                stage_index=event.stage_index,
                plugin_id="dummy.plugin",
                audience="ALL",
                frame_type="PATCH",
                payload={"count": len(trace.events)},
                sent_at=event.server_received_at,
            )
        ]

    def on_host_action(
        self, action: dict, trace: StageTrace
    ) -> list[PluginFrame] | None:
        return []

    def is_finished(self, trace: StageTrace) -> bool:
        return len(trace.events) >= self.finish_after_events

    def build_outcome(self, trace: StageTrace) -> StageOutcome:
        return StageOutcome(
            session_id=trace.session_id,
            stage_id=trace.stage_id,
            stage_index=trace.stage_index,
            plugin_id="dummy.plugin",
            completed_at=datetime.now(UTC),
        )


def _player() -> PlayerIdentity:
    return PlayerIdentity(
        player_id="player-1",
        display_name="Alice",
        is_authenticated=True,
        participation_mode="LOGGED",
        consents={"gameplay_identity": True, "email_results": True},
    )


def _context(stage: StageDefinition, now: datetime) -> StageContext:
    return StageContext(
        session_id="session-1",
        quiz_id="quiz-1",
        stage=stage,
        server_now=now,
        players=[_player()],
    )


def _stage_definition(time_limit_ms: int | None = None) -> StageDefinition:
    return StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id="dummy.plugin",
        stage_kind="question",
        engine_prompt={},
        plugin_spec={},
        time_limit_ms=time_limit_ms,
    )


def test_open_stage_initializes_trace_and_returns_frames() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(runtime)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    context = _context(_stage_definition(), now)

    frames = runner.open_stage(context)

    assert runtime.opened is True
    assert runner.trace is not None
    assert runner.trace.started_at == now
    assert len(frames) == 1


def test_handle_player_event_appends_trace_and_sets_server_time() -> None:
    runtime = DummyRuntime()
    recv_time = datetime(2024, 1, 1, 12, 0, 5, tzinfo=UTC)
    runner = StageRunner(runtime, clock=lambda: recv_time)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    frames = runner.handle_player_event(
        {
            "event_id": "event-1",
            "player_id": "player-1",
            "type": "SUBMIT",
            "payload": {"answer": "A"},
            "seq": 1,
        }
    )

    assert runner.trace is not None
    assert len(runner.trace.events) == 1
    assert runner.trace.events[0].server_received_at == recv_time
    assert len(frames) == 1


def test_handle_player_event_rejects_invalid_payload() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    with pytest.raises(ValueError):
        runner.handle_player_event(
            {
                "event_id": "event-1",
                "player_id": "player-1",
                "type": "SUBMIT",
                "payload": {"bad": object()},
            }
        )


def test_maybe_close_uses_plugin_finished() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(
        runtime,
        clock=lambda: datetime(2024, 1, 1, 12, 0, 5, tzinfo=UTC),
    )
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)
    runner.handle_player_event(
        {
            "event_id": "event-1",
            "player_id": "player-1",
            "type": "SUBMIT",
            "payload": {"answer": "A"},
        }
    )

    outcome = runner.maybe_close()

    assert outcome is not None
    assert runner.trace is not None
    assert runner.trace.ended_at is not None


def test_maybe_close_uses_time_limit() -> None:
    runtime = DummyRuntime()
    runtime.finish_after_events = 10
    start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    clock_time = start + timedelta(seconds=2)
    runner = StageRunner(runtime, clock=lambda: clock_time)
    context = _context(_stage_definition(time_limit_ms=1000), start)
    runner.open_stage(context)

    outcome = runner.maybe_close()

    assert outcome is not None


def test_open_stage_rejects_double_open() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(runtime)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    context = _context(_stage_definition(), now)

    runner.open_stage(context)

    with pytest.raises(ValueError):
        runner.open_stage(context)


def test_handle_player_event_requires_stage_open() -> None:
    runner = StageRunner(DummyRuntime())

    with pytest.raises(ValueError):
        runner.handle_player_event({"event_id": "event-1"})


def test_handle_player_event_rejects_non_dict_payload() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    with pytest.raises(ValueError):
        runner.handle_player_event(["bad payload"])


class NullHostRuntime(DummyRuntime):
    def on_host_action(
        self, action: dict, trace: StageTrace
    ) -> list[PluginFrame] | None:
        return None


class BadFrameRuntime(DummyRuntime):
    def on_host_action(
        self, action: dict, trace: StageTrace
    ) -> list[PluginFrame] | None:
        return ["invalid"]


def test_handle_host_action_requires_stage_open() -> None:
    runner = StageRunner(DummyRuntime())

    with pytest.raises(ValueError):
        runner.handle_host_action({})


def test_handle_host_action_rejects_invalid_action_payload() -> None:
    runtime = DummyRuntime()
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    with pytest.raises(ValueError):
        runner.handle_host_action(["bad action"])


def test_handle_host_action_allows_none_frames() -> None:
    runtime = NullHostRuntime()
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    frames = runner.handle_host_action({"type": "pause"})

    assert frames == []


def test_handle_host_action_rejects_invalid_frames() -> None:
    runtime = BadFrameRuntime()
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    with pytest.raises(ValueError):
        runner.handle_host_action({"type": "pause"})


def test_maybe_close_returns_existing_outcome() -> None:
    runtime = DummyRuntime()
    runtime.finish_after_events = 0
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    outcome = runner.maybe_close()
    assert outcome is not None

    second_outcome = runner.maybe_close()

    assert second_outcome is outcome


def test_maybe_close_returns_none_when_not_finished() -> None:
    runtime = DummyRuntime()
    runtime.finish_after_events = 10
    runner = StageRunner(runtime)
    context = _context(
        _stage_definition(),
        datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    runner.open_stage(context)

    outcome = runner.maybe_close()

    assert outcome is None


@pytest.mark.parametrize(
    ("outcome_kwargs", "error_message"),
    [
        ({"session_id": "other"}, "Outcome session_id does not match trace."),
        ({"stage_id": "other"}, "Outcome stage_id does not match trace."),
        ({"stage_index": 99}, "Outcome stage_index does not match trace."),
    ],
)
def test_validate_outcome_rejects_mismatch(outcome_kwargs, error_message) -> None:
    trace = StageTrace(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    outcome = StageOutcome(
        session_id=outcome_kwargs.get("session_id", "session-1"),
        stage_id=outcome_kwargs.get("stage_id", "stage-1"),
        stage_index=outcome_kwargs.get("stage_index", 0),
        plugin_id="dummy.plugin",
        completed_at=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
    )

    with pytest.raises(ValueError, match=error_message):
        StageRunner._validate_outcome(outcome, trace)


def test_parse_datetime_accepts_types() -> None:
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    from quiz_engine.runtime import stage_runner as module

    assert module._parse_datetime(None) is None
    assert module._parse_datetime(now) == now
    assert module._parse_datetime("2024-01-01T12:00:00+00:00") == now

    with pytest.raises(ValueError):
        module._parse_datetime(123)
