"""Additional Sprint 7 edge tests to raise per-module coverage."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.user import User
from quiz_engine.routers import ws as ws_router
from quiz_engine.services.session_persist_service import SessionPersistService


class _FakeWebSocketForHydrate:
    def __init__(self, app) -> None:  # noqa: ANN001
        self.app = app


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint7_edges.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def _drain_until(ws, expected_type: str, max_messages: int = 20):  # noqa: ANN001
    for _ in range(max_messages):
        message = ws.receive_json()
        if message.get("type") == expected_type:
            return message
    raise AssertionError(f"Did not receive {expected_type}")


def _login(client: TestClient, subject: str = "user1") -> None:
    response = client.post("/login", data={"user": subject}, follow_redirects=False)
    assert response.status_code == 303


def _create_quiz(client: TestClient, *, questions: list[dict]) -> int:
    created = client.post("/admin/quizzes", follow_redirects=False)
    assert created.status_code == 303
    quiz_id = int(created.headers["location"].rsplit("/", 1)[-1])

    saved = client.put(
        f"/api/quizzes/{quiz_id}",
        json={
            "schema_version": "v1",
            "title": "Edge quiz",
            "description": "edge",
            "questions": questions,
        },
    )
    assert saved.status_code == 200
    return quiz_id


def _slide_question(question_id: str, title: str) -> dict:
    return {
        "question_id": question_id,
        "type": "slide",
        "title": title,
        "spec": {
            "schema_version": "v0",
            "type": "slide",
            "content": {
                "title": title,
                "body": f"{title} body",
            },
        },
    }


def _start_session(client: TestClient, quiz_id: int) -> str:
    started = client.post(f"/host/quizzes/{quiz_id}/start", follow_redirects=False)
    assert started.status_code == 303
    return started.headers["location"].rsplit("/", 1)[-1]


def test_host_join_routes_auth_and_404_and_success(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    # Host routes require auth.
    unauth_start = client.post("/host/quizzes/1/start", follow_redirects=False)
    assert unauth_start.status_code == 303
    assert unauth_start.headers["location"] == "/login"

    unauth_host_page = client.get("/host/s/ABC123", follow_redirects=False)
    assert unauth_host_page.status_code == 303
    assert unauth_host_page.headers["location"] == "/login"

    _login(client, "user1")

    missing_host_page = client.get("/host/s/UNKNOWN")
    assert missing_host_page.status_code == 404

    quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])
    session_code = _start_session(client, quiz_id)

    host_page = client.get(f"/host/s/{session_code}")
    assert host_page.status_code == 200
    assert session_code in host_page.text
    assert "data:image/png;base64," in host_page.text

    # Wrong host user gets 404.
    client.post("/logout", follow_redirects=False)
    _login(client, "user2")
    forbidden_host_page = client.get(f"/host/s/{session_code}")
    assert forbidden_host_page.status_code == 404

    # Join/player pages.
    join_ok = client.get(f"/join/{session_code}")
    assert join_ok.status_code == 200

    join_missing = client.get("/join/NOPE")
    assert join_missing.status_code == 404

    nickname = "x" * 40
    player_ok = client.get(f"/player/s/{session_code}?nickname={nickname}")
    assert player_ok.status_code == 200
    assert ("x" * 32) in player_ok.text

    player_missing = client.get("/player/s/NOPE")
    assert player_missing.status_code == 404


def test_ws_rejects_invalid_role_and_missing_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    with client.websocket_connect("/ws/s/ANY?role=invalid") as ws:
        error = ws.receive_json()
        assert error["type"] == "ERROR"
        assert "Invalid role" in error["payload"]["message"]

    with client.websocket_connect("/ws/s/NOSESSION?role=host") as ws:
        error = ws.receive_json()
        assert error["type"] == "ERROR"
        assert "Session not found" in error["payload"]["message"]


def test_ws_invalid_envelope_connect_and_unsupported_event(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    _login(client, "user1")
    quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])
    session_code = _start_session(client, quiz_id)

    with client.websocket_connect(f"/ws/s/{session_code}?role=host") as ws:
        _drain_until(ws, "SESSION_CREATED")
        _drain_until(ws, "LOBBY_SNAPSHOT")

        ws.send_json([])
        invalid_1 = _drain_until(ws, "ERROR")
        assert "Invalid message envelope" in invalid_1["payload"]["message"]

        ws.send_json({"type": 123, "payload": {}})
        invalid_2 = _drain_until(ws, "ERROR")
        assert "Invalid message envelope" in invalid_2["payload"]["message"]

        ws.send_json({"type": "CONNECT", "payload": {}})
        connect = _drain_until(ws, "SESSION_STATE_CHANGED")
        assert connect["payload"]["session_state"] == "LOBBY"

        ws.send_json({"type": "WAT", "payload": {}})
        unsupported = _drain_until(ws, "ERROR")
        assert "Unsupported event" in unsupported["payload"]["message"]


def test_ws_join_leave_and_non_host_control_errors(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    _login(client, "user1")
    quiz_id = _create_quiz(
        client,
        questions=[_slide_question("s1", "Stage 1"), _slide_question("s2", "Stage 2")],
    )
    session_code = _start_session(client, quiz_id)

    with client.websocket_connect(f"/ws/s/{session_code}?role=host") as host_ws:
        _drain_until(host_ws, "SESSION_CREATED")
        _drain_until(host_ws, "LOBBY_SNAPSHOT")

        with client.websocket_connect(f"/ws/s/{session_code}?role=player") as player_ws:
            _drain_until(player_ws, "LOBBY_SNAPSHOT")

            host_ws.send_json({"type": "JOIN_SESSION", "payload": {"nickname": "X"}})

            player_ws.send_json({"type": "JOIN_SESSION", "payload": {"nickname": ""}})

            player_ws.send_json(
                {
                    "type": "JOIN_SESSION",
                    "payload": {"nickname": "Alice"},
                }
            )
            _drain_until(player_ws, "PLAYER_JOINED")
            _drain_until(player_ws, "LOBBY_SNAPSHOT")
            _drain_until(host_ws, "PLAYER_JOINED")
            _drain_until(host_ws, "LOBBY_SNAPSHOT")

            player_ws.send_json(
                {"type": "JOIN_SESSION", "payload": {"nickname": "Alice-again"}}
            )

            host_ws.send_json({"type": "LEAVE_SESSION", "payload": {}})

            player_ws.send_json({"type": "HOST_START", "payload": {}})

            player_ws.send_json({"type": "HOST_NEXT_STAGE", "payload": {}})

            player_ws.send_json({"type": "HOST_END", "payload": {}})

            player_ws.send_json({"type": "LEAVE_SESSION", "payload": {}})


def test_ws_host_start_next_end_edge_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    _login(client, "user1")

    # No stage -> HOST_START ends session.
    empty_quiz_id = _create_quiz(client, questions=[])
    empty_session_code = _start_session(client, empty_quiz_id)
    with client.websocket_connect(f"/ws/s/{empty_session_code}?role=host") as ws:
        _drain_until(ws, "SESSION_CREATED")
        _drain_until(ws, "LOBBY_SNAPSHOT")

        ws.send_json({"type": "HOST_START", "payload": {}})
        running = _drain_until(ws, "SESSION_STATE_CHANGED")
        assert running["payload"]["session_state"] == "RUNNING"
        ended = _drain_until(ws, "SESSION_STATE_CHANGED")
        assert ended["payload"]["session_state"] == "ENDED"

        ws.send_json({"type": "HOST_NEXT_STAGE", "payload": {}})
        not_running = _drain_until(ws, "ERROR")
        assert "not running" in not_running["payload"]["message"]

    # One stage -> HOST_START twice (second is ignored), HOST_NEXT_STAGE ends.
    one_quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])
    one_session_code = _start_session(client, one_quiz_id)

    with client.websocket_connect(f"/ws/s/{one_session_code}?role=host") as ws:
        _drain_until(ws, "SESSION_CREATED")
        _drain_until(ws, "LOBBY_SNAPSHOT")

        ws.send_json({"type": "HOST_START", "payload": {}})
        _drain_until(ws, "SESSION_STATE_CHANGED")
        _drain_until(ws, "STAGE_CHANGED")
        _drain_until(ws, "PLUGIN_FRAME")

        ws.send_json({"type": "HOST_START", "payload": {}})
        ws.send_json({"type": "HOST_NEXT_STAGE", "payload": {}})
        ended = _drain_until(ws, "SESSION_STATE_CHANGED")
        assert ended["payload"]["session_state"] == "ENDED"


def test_ws_errors_when_live_state_disappears_after_connect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    _login(client, "user1")

    quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])
    session_code = _start_session(client, quiz_id)

    with client.websocket_connect(f"/ws/s/{session_code}?role=host") as host_ws:
        _drain_until(host_ws, "SESSION_CREATED")
        _drain_until(host_ws, "LOBBY_SNAPSHOT")

        client.app.state.session_live_service._sessions.pop(session_code, None)  # noqa: SLF001

        host_ws.send_json({"type": "HOST_START", "payload": {}})
        start_error = _drain_until(host_ws, "ERROR")
        assert "Session not found" in start_error["payload"]["message"]

        host_ws.send_json({"type": "HOST_NEXT_STAGE", "payload": {}})
        next_error = _drain_until(host_ws, "ERROR")
        assert "Session not found" in next_error["payload"]["message"]

        host_ws.send_json({"type": "HOST_END", "payload": {}})
        end_error = _drain_until(host_ws, "ERROR")
        assert "Session not found" in end_error["payload"]["message"]

    session_code_2 = _start_session(client, quiz_id)
    with client.websocket_connect(f"/ws/s/{session_code_2}?role=player") as player_ws:
        _drain_until(player_ws, "LOBBY_SNAPSHOT")
        client.app.state.session_live_service._sessions.pop(session_code_2, None)  # noqa: SLF001
        player_ws.send_json({"type": "JOIN_SESSION", "payload": {"nickname": "A"}})
        join_error = _drain_until(player_ws, "ERROR")
        assert "Session not found" in join_error["payload"]["message"]


def test_ws_join_rejected_when_session_already_ended(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    _login(client, "user1")

    quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])
    session_code = _start_session(client, quiz_id)

    with client.websocket_connect(f"/ws/s/{session_code}?role=host") as host_ws:
        _drain_until(host_ws, "SESSION_CREATED")
        _drain_until(host_ws, "LOBBY_SNAPSHOT")
        host_ws.send_json({"type": "HOST_END", "payload": {}})
        _drain_until(host_ws, "SESSION_STATE_CHANGED")

    with client.websocket_connect(f"/ws/s/{session_code}?role=player") as player_ws:
        _drain_until(player_ws, "LOBBY_SNAPSHOT")
        player_ws.send_json({"type": "JOIN_SESSION", "payload": {"nickname": "Late"}})
        error = _drain_until(player_ws, "ERROR")
        assert "already ended" in error["payload"]["message"]


def test_ws_helper_hydrate_and_end_session_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    app = create_app()
    persist = SessionPersistService()

    client = TestClient(app)
    _login(client, "user1")
    quiz_id = _create_quiz(client, questions=[_slide_question("s1", "Stage 1")])

    with get_session() as session:
        owner = session.execute(
            select(User).where(User.subject == "user1")
        ).scalar_one()
        created = persist.create_session(
            session,
            quiz_id=quiz_id,
            host_user_id=owner.id,
        )
        player = persist.add_player(session, session_id=created.id, nickname="Hydrated")

    fake_ws = _FakeWebSocketForHydrate(app)
    live = asyncio.run(
        ws_router._hydrate_live_session(
            fake_ws,
            session_code=created.session_code,
        )
    )
    assert live is not None
    assert player.id in live.players

    # _end_session no-op branch when no live session exists.
    asyncio.run(ws_router._end_session("MISSING", app.state.session_live_service))

    with get_session() as session:
        db_session = session.execute(
            select(SessionModel).where(SessionModel.id == created.id)
        ).scalar_one()
    assert db_session.state == "LOBBY"
