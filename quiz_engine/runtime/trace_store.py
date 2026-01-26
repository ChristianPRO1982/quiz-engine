"""In-memory trace storage."""

from __future__ import annotations

from quiz_engine.contracts.runtime_models import StageOutcome, StageTrace


class TraceStore:
    def __init__(self) -> None:
        self._traces: dict[tuple[str, str], StageTrace] = {}
        self._outcomes: dict[tuple[str, str], StageOutcome] = {}

    def store_trace(self, trace: StageTrace) -> None:
        key = (trace.session_id, trace.stage_id)
        self._traces[key] = trace

    def get_trace(self, session_id: str, stage_id: str) -> StageTrace | None:
        return self._traces.get((session_id, stage_id))

    def store_outcome(self, outcome: StageOutcome) -> None:
        key = (outcome.session_id, outcome.stage_id)
        self._outcomes[key] = outcome

    def get_outcome(self, session_id: str, stage_id: str) -> StageOutcome | None:
        return self._outcomes.get((session_id, stage_id))
