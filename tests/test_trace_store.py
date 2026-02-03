"""Tests for the in-memory trace store."""

from __future__ import annotations

from datetime import UTC, datetime

from quiz_engine.contracts.runtime_models import StageOutcome, StageTrace
from quiz_engine.runtime.trace_store import TraceStore


def test_trace_store_round_trip() -> None:
    store = TraceStore()
    trace = StageTrace(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    outcome = StageOutcome(
        session_id="session-1",
        stage_id="stage-1",
        stage_index=0,
        plugin_id="dummy.plugin",
        completed_at=datetime(2024, 1, 1, 0, 1, tzinfo=UTC),
    )

    store.store_trace(trace)
    store.store_outcome(outcome)

    assert store.get_trace("session-1", "stage-1") is trace
    assert store.get_outcome("session-1", "stage-1") is outcome
