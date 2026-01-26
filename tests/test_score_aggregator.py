"""Tests for score aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from quiz_engine.contracts.runtime_models import GradeDelta, ScoreDelta, StageOutcome
from quiz_engine.runtime.score_aggregator import ScoreAggregator


def _outcome(score_deltas=None, grade_deltas=None) -> StageOutcome:
    return StageOutcome(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        plugin_id="plugin.quiz",
        completed_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC),
        score_deltas=score_deltas,
        grade_deltas=grade_deltas,
    )


def test_score_aggregator_sums_deltas() -> None:
    aggregator = ScoreAggregator()
    outcome = _outcome(
        score_deltas=[
            ScoreDelta(player_id="player-1", delta_score=2.0),
            ScoreDelta(player_id="player-1", delta_score=3.5),
            ScoreDelta(player_id="player-2", delta_score=1.0),
        ]
    )
    aggregator.apply_outcome(outcome)

    assert aggregator.get_total("player-1") == 5.5
    assert aggregator.get_total("player-2") == 1.0


def test_score_aggregator_handles_missing_score_deltas() -> None:
    aggregator = ScoreAggregator()
    aggregator.apply_outcome(_outcome(score_deltas=None))

    assert aggregator.get_totals() == {}


def test_score_aggregator_stores_grade_deltas() -> None:
    aggregator = ScoreAggregator()
    outcome = _outcome(
        grade_deltas=[
            GradeDelta(player_id="player-1", value=3.0),
            GradeDelta(player_id="player-1", value=4.0),
        ]
    )
    aggregator.apply_outcome(outcome)

    stored = aggregator.get_grade_deltas("player-1")
    assert [delta.value for delta in stored] == [3.0, 4.0]
