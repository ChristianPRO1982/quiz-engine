"""Unit tests for the built-in MCQ plugin."""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PlayerIdentity,
    StageContext,
    StageDefinition,
    StageTrace,
)
from quiz_engine.plugins.mcq import (
    MCQPlugin,
    MCQStageRuntime,
    _derive_runtime_seed,
    _draw_bot_choice,
    _extract_prestart_countdown_s,
    _extract_single_choice_id,
    _resolve_multianswer_selection,
)
from quiz_engine.plugins.mcq.config import MCQConfig
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


def test_mcq_create_runtime_rejects_wrong_plugin_id() -> None:
    plugin = MCQPlugin()
    bad_stage = StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id="slide",
        stage_kind="slide",
        engine_prompt={},
        plugin_spec={"schema_version": "v1", "plugin": "mcq", "mode": "oneclick"},
    )
    with pytest.raises(ValueError, match="cannot create runtime"):
        plugin.create_runtime("session-1", bad_stage)


def test_mcq_runtime_ignores_unknown_player_event_types() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    runtime = plugin.create_runtime("session-1", stage)
    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
    )
    event = PlayerEvent(
        event_id="e-ignored",
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        player_id="p1",
        type="IGNORED",
        server_received_at=datetime(2024, 1, 1, 12, 0, 1, tzinfo=UTC),
        payload={},
    )
    assert runtime.on_player_event(event, trace) is None


def test_mcq_runtime_internal_state_machine_branches() -> None:
    plugin = MCQPlugin()
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    runtime = plugin.create_runtime("session-1", stage)

    started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    events = [
        PlayerEvent(
            event_id="e0",
            session_id="session-1",
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            player_id="p1",
            type="OTHER",
            server_received_at=started,
            payload={},
        ),
        PlayerEvent(
            event_id="e1",
            session_id="session-1",
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            player_id="p1",
            type="MCQ_PLAYER_SUBMIT",
            server_received_at=started,
            payload={},
        ),
        PlayerEvent(
            event_id="e2",
            session_id="session-1",
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            player_id="p1",
            type="MCQ_PLAYER_SELECT",
            server_received_at=started,
            payload={"choice_id": "unknown"},
        ),
        PlayerEvent(
            event_id="e3",
            session_id="session-1",
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            player_id="p1",
            type="MCQ_PLAYER_SELECT",
            server_received_at=started,
            payload={"choice_id": "b"},
        ),
        PlayerEvent(
            event_id="e4",
            session_id="session-1",
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            player_id="p1",
            type="MCQ_PLAYER_SELECT",
            server_received_at=started,
            payload={"choice_id": "a"},
        ),
    ]
    trace = StageTrace(
        session_id="session-1",
        stage_id=stage.stage_id,
        stage_index=stage.stage_index,
        started_at=started,
        events=events,
    )

    states = runtime._compute_player_states(trace)  # noqa: SLF001
    assert states["p1"].submitted_choice_ids == {"b"}


def test_mcq_compute_final_score_edge_paths() -> None:
    runtime = MCQStageRuntime(
        session_id="session-1",
        stage=_mcq_stage(plugin_spec=_oneclick_spec()),
        plugin_spec=_oneclick_spec(),
        config=MCQPlugin()._config,  # noqa: SLF001
    )
    started_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)

    assert (
        runtime._compute_final_score(  # noqa: SLF001
            points=10,
            mode_value=1,
            submitted_at=started_at,
            started_at=started_at,
            time_limit_s=0,
        )
        == 10
    )
    assert (
        runtime._compute_final_score(  # noqa: SLF001
            points=10,
            mode_value=1,
            submitted_at=None,
            started_at=started_at,
            time_limit_s=30,
        )
        == 0
    )


def test_mcq_helper_functions_cover_remaining_branches() -> None:
    assert _extract_prestart_countdown_s(None) is None
    assert _extract_prestart_countdown_s({"prestart_countdown_s": "x"}) is None
    assert _extract_prestart_countdown_s({"prestart_countdown_s": -1}) is None
    assert _extract_prestart_countdown_s({"prestart_countdown_s": 3}) == 3

    assert _extract_single_choice_id({}, choice_ids={"a"}) is None
    assert _extract_single_choice_id({"choice_id": "x"}, choice_ids={"a"}) is None
    assert _extract_single_choice_id({"choice_id": " a "}, choice_ids={"a"}) == "a"

    current = {"a"}
    assert (
        _resolve_multianswer_selection(
            payload={"choice_id": 1},
            current_selection=current,
            valid_choice_ids={"a", "b"},
        )
        is None
    )
    assert (
        _resolve_multianswer_selection(
            payload={"choice_id": "x"},
            current_selection=current,
            valid_choice_ids={"a", "b"},
        )
        is None
    )
    assert _resolve_multianswer_selection(
        payload={"choice_id": "b", "selected": True},
        current_selection=current,
        valid_choice_ids={"a", "b"},
    ) == {"a", "b"}
    assert _resolve_multianswer_selection(
        payload={"choice_id": "a", "selected": False},
        current_selection={"a", "b"},
        valid_choice_ids={"a", "b"},
    ) == {"b"}
    assert (
        _resolve_multianswer_selection(
            payload={"choice_id": "a"},
            current_selection={"a"},
            valid_choice_ids={"a", "b"},
        )
        == set()
    )
    assert _resolve_multianswer_selection(
        payload={"choice_ids": ["a", " ", "z", "b"]},
        current_selection=set(),
        valid_choice_ids={"a", "b"},
    ) == {"a", "b"}


def test_mcq_seed_and_bot_draw_helpers() -> None:
    stage = _mcq_stage(plugin_spec=_oneclick_spec())
    stage.random_seed = None
    derived = _derive_runtime_seed(stage, "session-1")
    assert isinstance(derived, int)
    assert derived > 0

    rng = random.Random(0)
    config = MCQConfig(
        default_time_limit_s=30,
        allowed_time_limits_s=(0, 30),
        default_points=1000,
        min_points=10,
        max_points=10000,
        default_choices_count=4,
        min_choices=1,
        max_choices=20,
        choice_columns_smartphone=2,
        choice_columns_tablet=4,
        choice_columns_desktop=6,
        default_player_choice_view="compact",
        allow_player_toggle_choice_view=True,
        enabled_modes=(
            "oneclick",
            "influence_bots",
            "influence_bots_nice",
            "influence_bots_evil",
        ),
        min_bots=0,
        bots_vote_early_ratio=0.8,
        early_time_window_ratio=0.2,
        bots_good_answer_ratio_nice=1.0,
        bots_good_answer_ratio_evil=0.0,
    )
    assert _draw_bot_choice(
        rng=rng,
        mode="influence_bots",
        choice_ids=["a", "b"],
        correct_ids=["b"],
        incorrect_ids=["a"],
        config=config,
    ) in {"a", "b"}
    assert (
        _draw_bot_choice(
            rng=rng,
            mode="influence_bots_evil",
            choice_ids=["only"],
            correct_ids=[],
            incorrect_ids=[],
            config=config,
        )
        == "only"
    )


def test_mcq_simulate_bot_votes_returns_zero_when_no_players_and_no_min_bots() -> None:
    config = MCQConfig(
        default_time_limit_s=30,
        allowed_time_limits_s=(30,),
        default_points=1000,
        min_points=10,
        max_points=10000,
        default_choices_count=4,
        min_choices=1,
        max_choices=20,
        choice_columns_smartphone=2,
        choice_columns_tablet=4,
        choice_columns_desktop=6,
        default_player_choice_view="compact",
        allow_player_toggle_choice_view=True,
        enabled_modes=("influence_bots",),
        min_bots=0,
        bots_vote_early_ratio=0.8,
        early_time_window_ratio=0.2,
        bots_good_answer_ratio_nice=0.8,
        bots_good_answer_ratio_evil=0.2,
    )
    spec = _oneclick_spec()
    spec["mode"] = "influence_bots"
    runtime = MCQStageRuntime(
        session_id="session-1",
        stage=_mcq_stage(plugin_spec=spec),
        plugin_spec=spec,
        config=config,
    )
    result = runtime._simulate_bot_votes(player_count=0)  # noqa: SLF001
    assert result == {"bot_count": 0, "distribution": {"a": 0, "b": 0}}
