"""Unit tests for the built-in MCQ plugin."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quiz_engine.contracts.runtime_models import (
    PlayerIdentity,
    StageContext,
    StageDefinition,
    StageTrace,
)
from quiz_engine.plugins.mcq import MCQPlugin, MCQStageRuntime
from quiz_engine.runtime.stage_runner import StageRunner


class _Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def _player(player_id: str) -> PlayerIdentity:
    return PlayerIdentity(
        player_id=player_id,
        display_name=player_id,
        is_authenticated=True,
        participation_mode="LOGGED",
        consents={"gameplay_identity": True, "email_results": False},
    )


def _mcq_stage(
    *,
    plugin_spec: dict,
    stage_id: str = "mcq-1",
    stage_index: int = 0,
    random_seed: int | None = None,
) -> StageDefinition:
    return StageDefinition(
        stage_id=stage_id,
        stage_index=stage_index,
        plugin_id="mcq",
        stage_kind="mcq",
        engine_prompt={},
        plugin_spec=plugin_spec,
        random_seed=random_seed,
    )


def _context(
    stage: StageDefinition,
    *,
    now: datetime,
    player_ids: list[str],
) -> StageContext:
    return StageContext(
        session_id="session-1",
        quiz_id="quiz-1",
        stage=stage,
        server_now=now,
        players=[_player(player_id) for player_id in player_ids],
    )


def _oneclick_spec() -> dict:
    return {
        "schema_version": "v1",
        "type": "quiz",
        "plugin": "mcq",
        "title": "Math",
        "prompt": "2 + 2 = ?",
        "mode": "oneclick",
        "time_limit_s": 30,
        "points": 1000,
        "examination": False,
        "choices": [
            {"id": "a", "label": "3", "is_correct": False},
            {"id": "b", "label": "4", "is_correct": True},
        ],
    }


def _multianswer_spec() -> dict:
    return {
        "schema_version": "v1",
        "type": "quiz",
        "plugin": "mcq",
        "title": "Signals",
        "prompt": "Pick weighted answers",
        "mode": "multianswer",
        "time_limit_s": 30,
        "points": 1000,
        "examination": False,
        "choices": [
            {"id": "a", "label": "+2", "weight": 2},
            {"id": "b", "label": "-1", "weight": -1},
            {"id": "c", "label": "0", "weight": 0},
        ],
    }


def _player_event(
    *,
    event_id: str,
    player_id: str,
    event_type: str,
    payload: dict,
) -> dict:
    return {
        "event_id": event_id,
        "player_id": player_id,
        "type": event_type,
        "payload": payload,
    }


def test_mcq_plugin_creates_runtime_and_emits_view_model() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    runtime = plugin.create_runtime("session-1", stage)
    assert isinstance(runtime, MCQStageRuntime)

    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    frames = runtime.on_stage_open(_context(stage, now=now, player_ids=["p1", "p2"]))

    assert frames is not None
    assert len(frames) == 1
    frame = frames[0]
    assert frame.frame_type == "VIEW_MODEL"
    assert frame.payload["plugin"] == "mcq"
    assert frame.payload["mode"] == "oneclick"
    assert frame.payload["player_count"] == 2
    assert frame.sent_at == now


def test_mcq_runtime_uses_stage_metadata_title_when_spec_title_missing() -> None:
    plugin = MCQPlugin()
    spec = _oneclick_spec()
    spec.pop("title")
    spec["content"] = {"body": "Body only"}
    stage = _mcq_stage(plugin_spec=spec)
    stage.metadata = {"title": "Question title"}
    runtime = plugin.create_runtime("session-1", stage)

    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    frames = runtime.on_stage_open(_context(stage, now=now, player_ids=["p1"]))

    assert frames is not None
    assert frames[0].payload["title"] == "Question title"


def test_mcq_runtime_scores_oneclick_with_time_factor() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    open_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(open_at)
    runtime = plugin.create_runtime("session-1", stage)
    runner = StageRunner(runtime=runtime, clock=clock)
    runner.open_stage(_context(stage, now=open_at, player_ids=["player-1", "player-2"]))

    clock.now = open_at + timedelta(seconds=3)
    runner.handle_player_event(
        _player_event(
            event_id="e1",
            player_id="player-1",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_id": "b"},
        )
    )
    clock.now = open_at + timedelta(seconds=10)
    runner.handle_player_event(
        _player_event(
            event_id="e2",
            player_id="player-2",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_id": "a"},
        )
    )

    clock.now = open_at + timedelta(seconds=30)
    outcome = runner.close_stage()
    by_player = {
        delta.player_id: delta.delta_score for delta in outcome.score_deltas or []
    }

    assert by_player["player-1"] == 900.0
    assert by_player["player-2"] == 0.0
    assert outcome.render_summary is not None
    assert outcome.render_summary["distribution"] == {"a": 1, "b": 1}


def test_mcq_runtime_scores_multianswer_with_negative_delta() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_multianswer_spec())
    open_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(open_at)
    runtime = plugin.create_runtime("session-1", stage)
    runner = StageRunner(runtime=runtime, clock=clock)
    runner.open_stage(_context(stage, now=open_at, player_ids=["player-1", "player-2"]))

    clock.now = open_at + timedelta(seconds=15)
    runner.handle_player_event(
        _player_event(
            event_id="e1",
            player_id="player-1",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_ids": ["a", "b"]},
        )
    )
    clock.now = open_at + timedelta(seconds=15)
    runner.handle_player_event(
        _player_event(
            event_id="e2",
            player_id="player-1",
            event_type="MCQ_PLAYER_SUBMIT",
            payload={},
        )
    )

    clock.now = open_at + timedelta(seconds=6)
    runner.handle_player_event(
        _player_event(
            event_id="e3",
            player_id="player-2",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_ids": ["b"]},
        )
    )
    clock.now = open_at + timedelta(seconds=6)
    runner.handle_player_event(
        _player_event(
            event_id="e4",
            player_id="player-2",
            event_type="MCQ_PLAYER_SUBMIT",
            payload={},
        )
    )

    clock.now = open_at + timedelta(seconds=30)
    outcome = runner.close_stage()
    by_player = {
        delta.player_id: delta.delta_score for delta in outcome.score_deltas or []
    }

    assert by_player["player-1"] == 500.0
    assert by_player["player-2"] == -800.0


def test_mcq_runtime_influence_uses_latest_selection() -> None:
    spec = _oneclick_spec()
    spec["mode"] = "influence"

    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=spec)
    open_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    clock = _Clock(open_at)
    runtime = plugin.create_runtime("session-1", stage)
    runner = StageRunner(runtime=runtime, clock=clock)
    runner.open_stage(_context(stage, now=open_at, player_ids=["player-1"]))

    clock.now = open_at + timedelta(seconds=2)
    runner.handle_player_event(
        _player_event(
            event_id="e1",
            player_id="player-1",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_id": "a"},
        )
    )
    clock.now = open_at + timedelta(seconds=8)
    runner.handle_player_event(
        _player_event(
            event_id="e2",
            player_id="player-1",
            event_type="MCQ_PLAYER_SELECT",
            payload={"choice_id": "b"},
        )
    )

    clock.now = open_at + timedelta(seconds=30)
    outcome = runner.close_stage()
    by_player = {
        delta.player_id: delta.delta_score for delta in outcome.score_deltas or []
    }

    assert by_player["player-1"] == 733.0


def test_mcq_runtime_bots_distribution_is_deterministic() -> None:
    spec = _oneclick_spec()
    spec["mode"] = "influence_bots_nice"
    stage = _mcq_stage(plugin_spec=spec, random_seed=1234)
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    plugin = MCQPlugin()
    runtime_a = plugin.create_runtime("session-1", stage)
    runtime_b = plugin.create_runtime("session-1", stage)

    context = _context(stage, now=now, player_ids=["p1", "p2"])
    runtime_a.on_stage_open(context)
    runtime_b.on_stage_open(context)

    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=now,
        ended_at=now + timedelta(seconds=20),
    )
    outcome_a = runtime_a.build_outcome(trace)
    outcome_b = runtime_b.build_outcome(trace)

    assert outcome_a.render_summary is not None
    assert outcome_b.render_summary is not None
    assert outcome_a.render_summary["bot_count"] == 10
    assert (
        outcome_a.render_summary["bot_distribution"]
        == outcome_b.render_summary["bot_distribution"]
    )


def test_mcq_runtime_host_end_marks_runtime_finished() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    runtime = plugin.create_runtime("session-1", stage)
    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )

    assert runtime.is_finished(trace) is False
    runtime.on_host_action({"type": "MCQ_HOST_END"}, trace)
    assert runtime.is_finished(trace) is True
