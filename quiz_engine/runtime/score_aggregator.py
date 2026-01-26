"""Score aggregation for stage outcomes."""

from __future__ import annotations

from quiz_engine.contracts.runtime_models import GradeDelta, ScoreDelta, StageOutcome


class ScoreAggregator:
    def __init__(self) -> None:
        self._totals: dict[str, float] = {}
        self._grade_deltas: dict[str, list[GradeDelta]] = {}

    def apply_outcome(self, outcome: StageOutcome) -> None:
        if outcome.score_deltas:
            for delta in outcome.score_deltas:
                self._apply_score_delta(delta)
        if outcome.grade_deltas:
            for delta in outcome.grade_deltas:
                self._grade_deltas.setdefault(delta.player_id, []).append(delta)

    def _apply_score_delta(self, delta: ScoreDelta) -> None:
        current = self._totals.get(delta.player_id, 0.0)
        self._totals[delta.player_id] = current + delta.delta_score

    def get_total(self, player_id: str) -> float:
        return self._totals.get(player_id, 0.0)

    def get_totals(self) -> dict[str, float]:
        return dict(self._totals)

    def get_grade_deltas(self, player_id: str) -> list[GradeDelta]:
        return list(self._grade_deltas.get(player_id, []))
