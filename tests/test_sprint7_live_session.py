"""Sprint 7 tests for live host/player session flow."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.quiz import Quiz
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.stage_event import StageEvent
from quiz_engine.models.stage_outcome import StageOutcomeRecord
from quiz_engine.models.user import User
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.services.session_live_service import (
    LiveSessionState,
    SessionLiveService,
)
from quiz_engine.services.session_persist_service import SessionPersistService
from quiz_engine.services.stage_orchestrator_service import StageOrchestratorService


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint7.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def _drain_until(ws, expected_type: str, max_messages: int = 12):  # noqa: ANN001
    for _ in range(max_messages):
        message = ws.receive_json()
        if message.get("type") == expected_type:
            return message
    raise AssertionError(
        f"Did not receive {expected_type} within {max_messages} messages"
    )


def test_session_code_generation_format_and_uniqueness(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    persist = SessionPersistService()

    with get_session() as session:
        owner = session.execute(
            select(User).where(User.subject == "user1")
        ).scalar_one()
        quiz = Quiz(
            schema_version="v1",
            payload={"schema_version": "v1", "title": "Sprint 7", "questions": []},
            created_by_user_id=owner.id,
        )
        session.add(quiz)
        session.commit()
        session.refresh(quiz)

        codes = set()
        for _ in range(40):
            created = persist.create_session(
                session,
                quiz_id=quiz.id,
                host_user_id=owner.id,
            )
            assert re.fullmatch(r"[A-Z2-9]{6}", created.session_code)
            codes.add(created.session_code)

    assert len(codes) == 40


def test_live_state_transitions() -> None:
    async def _run() -> None:
        service = SessionLiveService()
        await service.create_or_replace_session(
            session_id=1,
            quiz_id=99,
            session_code="ABC123",
            lifecycle_state="LOBBY",
            stages=[],
        )

        running = await service.transition_state("ABC123", new_state="RUNNING")
        assert running.lifecycle_state == "RUNNING"

        ended = await service.transition_state("ABC123", new_state="ENDED")
        assert ended.lifecycle_state == "ENDED"

    asyncio.run(_run())


def test_stage_open_close_orchestration_persists_events_and_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    persist = SessionPersistService()
    orchestrator = StageOrchestratorService(persist)
    registry = build_default_registry()

    with get_session() as session:
        owner = session.execute(
            select(User).where(User.subject == "user1")
        ).scalar_one()
        quiz = Quiz(
            schema_version="v1",
            payload={
                "schema_version": "v1",
                "title": "Lifecycle",
                "questions": [
                    {
                        "question_id": "slide-1",
                        "type": "slide",
                        "title": "Intro",
                        "spec": {
                            "schema_version": "v0",
                            "type": "slide",
                            "content": {"title": "Intro", "body": "Hello"},
                        },
                    }
                ],
            },
            created_by_user_id=owner.id,
        )
        session.add(quiz)
        session.commit()
        session.refresh(quiz)

        created = persist.create_session(
            session,
            quiz_id=quiz.id,
            host_user_id=owner.id,
        )
        stages = orchestrator.build_stages_from_quiz_payload(quiz.payload)

        live = LiveSessionState(
            session_id=created.id,
            quiz_id=quiz.id,
            session_code=created.session_code,
            lifecycle_state="RUNNING",
            stages=stages,
        )

        opened = orchestrator.open_stage(
            session,
            live_session=live,
            stage_index=0,
            plugin_registry=registry,
        )
        assert opened is not None
        stage, frames = opened
        assert stage.stage_id == "slide-1"
        assert len(frames) == 1

        outcome = orchestrator.close_current_stage(session, live_session=live)
        assert outcome is not None
        assert outcome.stage_id == "slide-1"

        event_count = session.execute(select(func.count(StageEvent.id))).scalar_one()
        outcome_count = session.execute(
            select(func.count(StageOutcomeRecord.id))
        ).scalar_one()

    assert event_count == 2
    assert outcome_count == 1


def test_sprint7_live_session_flow_host_and_player_ws(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})
    create_quiz = client.post("/admin/quizzes", follow_redirects=False)
    assert create_quiz.status_code == 303
    quiz_id = int(create_quiz.headers["location"].rsplit("/", 1)[-1])

    save_quiz = client.put(
        f"/api/quizzes/{quiz_id}",
        json={
            "schema_version": "v1",
            "title": "Sprint 7 Live",
            "description": "ws",
            "questions": [
                {
                    "question_id": "slide-1",
                    "type": "slide",
                    "title": "Stage 1",
                    "spec": {
                        "schema_version": "v0",
                        "type": "slide",
                        "content": {
                            "title": "Stage 1",
                            "body": "# One\n\n- alpha",
                            "body_format": "markdown",
                        },
                    },
                },
                {
                    "question_id": "slide-2",
                    "type": "slide",
                    "title": "Stage 2",
                    "spec": {
                        "schema_version": "v0",
                        "type": "slide",
                        "content": {
                            "title": "Stage 2",
                            "body": "**Two**",
                            "body_format": "markdown",
                        },
                    },
                },
            ],
        },
    )
    assert save_quiz.status_code == 200

    start = client.post(f"/host/quizzes/{quiz_id}/start", follow_redirects=False)
    assert start.status_code == 303
    assert start.headers["location"].startswith("/host/s/")
    session_code = start.headers["location"].rsplit("/", 1)[-1]

    with client.websocket_connect(f"/ws/s/{session_code}?role=host") as host_ws:
        created_msg = host_ws.receive_json()
        assert created_msg["type"] == "SESSION_CREATED"
        assert created_msg["payload"]["session_code"] == session_code

        host_snapshot = host_ws.receive_json()
        assert host_snapshot["type"] == "LOBBY_SNAPSHOT"
        assert host_snapshot["payload"]["session_state"] == "LOBBY"

        with client.websocket_connect(f"/ws/s/{session_code}?role=player") as player_ws:
            player_snapshot = player_ws.receive_json()
            assert player_snapshot["type"] == "LOBBY_SNAPSHOT"

            player_ws.send_json(
                {
                    "type": "JOIN_SESSION",
                    "payload": {"nickname": "Alice"},
                }
            )
            player_joined = _drain_until(player_ws, "PLAYER_JOINED")
            assert player_joined["payload"]["nickname"] == "Alice"
            player_lobby_after_join = _drain_until(player_ws, "LOBBY_SNAPSHOT")
            assert len(player_lobby_after_join["payload"]["players"]) == 1

            host_joined = _drain_until(host_ws, "PLAYER_JOINED")
            assert host_joined["payload"]["nickname"] == "Alice"
            host_lobby_after_join = _drain_until(host_ws, "LOBBY_SNAPSHOT")
            assert len(host_lobby_after_join["payload"]["players"]) == 1

            host_ws.send_json({"type": "HOST_START", "payload": {}})
            running_host = _drain_until(host_ws, "SESSION_STATE_CHANGED")
            assert running_host["payload"]["session_state"] == "RUNNING"
            stage_0_host = _drain_until(host_ws, "STAGE_CHANGED")
            assert stage_0_host["payload"]["stage_index"] == 0
            frame_0_host = _drain_until(host_ws, "PLUGIN_FRAME")
            assert frame_0_host["payload"]["payload"]["title"] == "Stage 1"
            assert frame_0_host["payload"]["payload"]["body_format"] == "markdown"

            running_player = _drain_until(player_ws, "SESSION_STATE_CHANGED")
            assert running_player["payload"]["session_state"] == "RUNNING"
            stage_0_player = _drain_until(player_ws, "STAGE_CHANGED")
            assert stage_0_player["payload"]["stage_index"] == 0
            frame_0_player = _drain_until(player_ws, "PLUGIN_FRAME")
            assert frame_0_player["payload"]["payload"]["title"] == "Stage 1"
            assert frame_0_player["payload"]["payload"]["body_format"] == "markdown"

            host_ws.send_json({"type": "HOST_NEXT_STAGE", "payload": {}})
            stage_1_host = _drain_until(host_ws, "STAGE_CHANGED")
            assert stage_1_host["payload"]["stage_index"] == 1
            frame_1_host = _drain_until(host_ws, "PLUGIN_FRAME")
            assert frame_1_host["payload"]["payload"]["title"] == "Stage 2"
            assert frame_1_host["payload"]["payload"]["body_format"] == "markdown"

            stage_1_player = _drain_until(player_ws, "STAGE_CHANGED")
            assert stage_1_player["payload"]["stage_index"] == 1
            frame_1_player = _drain_until(player_ws, "PLUGIN_FRAME")
            assert frame_1_player["payload"]["payload"]["title"] == "Stage 2"
            assert frame_1_player["payload"]["payload"]["body_format"] == "markdown"

            host_ws.send_json({"type": "HOST_END", "payload": {}})

    with get_session() as session:
        db_session = session.execute(
            select(SessionModel).where(SessionModel.session_code == session_code)
        ).scalar_one()
        assert db_session.state == "ENDED"

        stage_event_count = session.execute(
            select(func.count(StageEvent.id)).where(
                StageEvent.session_id == db_session.id
            )
        ).scalar_one()
        stage_outcome_count = session.execute(
            select(func.count(StageOutcomeRecord.id)).where(
                StageOutcomeRecord.session_id == db_session.id
            )
        ).scalar_one()

    assert stage_event_count == 4
    assert stage_outcome_count == 2
