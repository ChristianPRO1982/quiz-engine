"""Sprint 2 auth and quiz builder tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.quiz import Quiz
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.user import User


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint2.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_dev_login_account_logout_flow(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    home = client.get("/")
    assert home.status_code == 200
    assert "Connect" in home.text

    account_anon = client.get("/account", follow_redirects=False)
    assert account_anon.status_code == 303
    assert account_anon.headers["location"] == "/login"

    login = client.post("/login", data={"user": "user1"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/account"

    account = client.get("/account")
    assert account.status_code == 200
    assert "user1" in account.text
    assert "Account" in account.text
    assert "Logout" in account.text

    logout = client.post("/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert logout.headers["location"] == "/"

    home_after_logout = client.get("/")
    assert "Connect" in home_after_logout.text


def test_quiz_create_list_detail_with_auth_gating(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    unauthorized_api = client.get("/api/quizzes")
    assert unauthorized_api.status_code == 401

    unauthorized_admin = client.get("/admin/quizzes", follow_redirects=False)
    assert unauthorized_admin.status_code == 303
    assert unauthorized_admin.headers["location"] == "/login"

    client.post("/login", data={"user": "user1"})

    create = client.post(
        "/api/quizzes",
        json={
            "schema_version": "v1",
            "title": "Sample Quiz",
            "description": "My first quiz",
            "questions": [
                {
                    "type": "qcm_single",
                    "text": "Question text",
                    "choices": ["A", "B", "C"],
                }
            ],
        },
    )
    assert create.status_code == 201
    created = create.json()
    quiz_id = created["id"]
    assert created["title"] == "Sample Quiz"

    listing = client.get("/api/quizzes")
    assert listing.status_code == 200
    listed = listing.json()
    assert len(listed) == 1
    assert listed[0]["id"] == quiz_id

    detail = client.get(f"/api/quizzes/{quiz_id}")
    assert detail.status_code == 200
    assert detail.json()["questions"][0]["type"] == "qcm_single"

    admin_list = client.get("/admin/quizzes")
    assert admin_list.status_code == 200
    assert "Sample Quiz" in admin_list.text
    assert f"/admin/quizzes/{quiz_id}/delete" in admin_list.text
    assert "Delete this quiz permanently?" in admin_list.text

    admin_detail = client.get(f"/admin/quizzes/{quiz_id}")
    assert admin_detail.status_code == 200
    assert "Question text" in admin_detail.text
    assert f"/admin/quizzes/{quiz_id}/delete" in admin_detail.text
    assert "Delete this quiz permanently?" in admin_detail.text


def test_quiz_delete_removes_quiz_and_sessions(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "user1"})

    create = client.post(
        "/api/quizzes",
        json={
            "schema_version": "v1",
            "title": "To delete",
            "description": "must disappear",
            "questions": [
                {
                    "type": "qcm_single",
                    "text": "Question text",
                    "choices": ["A", "B", "C"],
                }
            ],
        },
    )
    assert create.status_code == 201
    quiz_id = create.json()["id"]

    start_session = client.post(
        f"/host/quizzes/{quiz_id}/start",
        follow_redirects=False,
    )
    assert start_session.status_code == 303

    deleted = client.delete(f"/api/quizzes/{quiz_id}")
    assert deleted.status_code == 204

    deleted_detail = client.get(f"/api/quizzes/{quiz_id}")
    assert deleted_detail.status_code == 404

    listing = client.get("/api/quizzes")
    assert listing.status_code == 200
    assert listing.json() == []

    with get_session() as session:
        assert session.get(Quiz, quiz_id) is None
        linked_sessions = list(
            session.execute(
                select(SessionModel).where(SessionModel.quiz_id == quiz_id)
            ).scalars()
        )
        assert linked_sessions == []
