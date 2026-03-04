"""Focused tests for stage orchestrator branch coverage."""

from __future__ import annotations

from quiz_engine.plugins.registry import PluginRegistry, build_default_registry
from quiz_engine.services.session_live_service import LivePlayerState, LiveSessionState
from quiz_engine.services.stage_orchestrator_service import StageOrchestratorService


class _FakePersist:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.outcomes: list[object] = []

    def record_stage_event(self, _session, **kwargs) -> None:  # noqa: ANN003
        self.events.append(kwargs)

    def record_stage_outcome(self, _session, **kwargs) -> None:  # noqa: ANN003
        self.outcomes.append(kwargs["outcome"])


def test_build_stages_from_quiz_payload_handles_fallback_shapes() -> None:
    orchestrator = StageOrchestratorService(_FakePersist())
    assert (
        orchestrator.build_stages_from_quiz_payload(
            {"questions": "bad", "stages": "bad"}
        )
        == []
    )

    stages = orchestrator.build_stages_from_quiz_payload(
        {
            "stages": [
                "skip-me",
                {
                    "question_id": "q1",
                    "type": "slide",
                    "plugin_spec": {"schema_version": "v1", "content": {"body": "Hi"}},
                    "title": " Intro ",
                },
            ]
        }
    )
    assert len(stages) == 1
    assert stages[0].stage_id == "q1"
    assert stages[0].plugin_spec == {"schema_version": "v1", "content": {"body": "Hi"}}
    assert stages[0].metadata == {"title": "Intro"}


def test_open_stage_raises_when_plugin_missing() -> None:
    orchestrator = StageOrchestratorService(_FakePersist())
    stages = orchestrator.build_stages_from_quiz_payload(
        {"questions": [{"question_id": "q1", "type": "missing", "spec": {}}]}
    )
    live = LiveSessionState(
        session_id=1,
        quiz_id=2,
        session_code="ABC123",
        lifecycle_state="RUNNING",
        stages=stages,
    )

    try:
        orchestrator.open_stage(
            None,  # type: ignore[arg-type]
            live_session=live,
            stage_index=0,
            plugin_registry=PluginRegistry(),
        )
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "Plugin not registered: missing" in str(exc)


def test_open_stage_sorts_players_and_persists_open_event() -> None:
    persist = _FakePersist()
    orchestrator = StageOrchestratorService(persist)
    stages = orchestrator.build_stages_from_quiz_payload(
        {
            "questions": [
                {
                    "question_id": "slide-1",
                    "type": "slide",
                    "spec": {"schema_version": "v1", "content": {"body": "Body"}},
                }
            ]
        }
    )
    live = LiveSessionState(
        session_id=1,
        quiz_id=2,
        session_code="ABC123",
        lifecycle_state="RUNNING",
        stages=stages,
        players={
            2: LivePlayerState(player_id=2, nickname="bob"),
            1: LivePlayerState(player_id=1, nickname="Alice"),
        },
    )

    opened = orchestrator.open_stage(
        None,  # type: ignore[arg-type]
        live_session=live,
        stage_index=0,
        plugin_registry=build_default_registry(),
    )
    assert opened is not None
    stage, frames = opened
    assert stage.stage_id == "slide-1"
    assert len(frames) == 1
    assert persist.events and persist.events[0]["stage_id"] == "slide-1"
