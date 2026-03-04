"""Additional Sprint 2 coverage tests for auth and quiz admin edges."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from auth.models import AuthUser
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User
from quiz_engine.services.auth_service import ensure_user_record


def _setup_db(
    tmp_path: Path,
    monkeypatch,
    *,
    auth_mode: str = "dev",
    db_name: str = "sprint2_edges.sqlite",
) -> None:
    db_path = tmp_path / db_name
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", auth_mode)
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())

    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_login_page_redirects_when_already_authenticated(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})
    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/account"


def test_login_page_in_oidc_mode_hides_dev_users(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch, auth_mode="oidc")
    client = TestClient(create_app())

    response = client.get("/login")

    assert response.status_code == 200
    assert "Hub auth mode placeholder" in response.text
    assert "user1" not in response.text


def test_login_submit_rejects_non_dev_mode_and_unknown_user(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch, auth_mode="oidc", db_name="oidc.sqlite")
    client = TestClient(create_app())

    non_dev = client.post("/login", data={"user": "user1"}, follow_redirects=False)
    assert non_dev.status_code == 303
    assert non_dev.headers["location"] == "/login"

    _setup_db(tmp_path, monkeypatch, auth_mode="dev", db_name="dev.sqlite")
    client = TestClient(create_app())
    unknown = client.post(
        "/login", data={"user": "unknown-user"}, follow_redirects=False
    )
    assert unknown.status_code == 303
    assert unknown.headers["location"] == "/login"


def test_admin_new_page_and_invalid_submit(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})

    page = client.get("/admin/quizzes/new", follow_redirects=False)
    assert page.status_code == 303
    assert page.headers["location"] == "/admin/quizzes"

    invalid = client.post(
        "/admin/quizzes/new",
        data={
            "title": "Quiz invalide",
            "description": "",
            "question": "Question ?",
            "choice1": "A",
            "choice2": "",
            "choice3": "",
        },
    )
    assert invalid.status_code == 400
    assert "cannot" in invalid.text.lower() or "at least" in invalid.text.lower()


def test_admin_new_submit_requires_authentication(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    response = client.post(
        "/admin/quizzes/new",
        data={
            "title": "Quiz",
            "description": "desc",
            "question": "Q",
            "choice1": "A",
            "choice2": "B",
            "choice3": "C",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_admin_quiz_detail_404_when_not_found(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})
    response = client.get("/admin/quizzes/9999")

    assert response.status_code == 404
    assert "Quiz not found" in response.text


def test_ensure_user_record_creates_missing_user(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)

    auth_user = AuthUser(
        subject="new-subject",
        display_name="New Subject",
        email=None,
        auth_mode="dev",
    )

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        assert db_user.subject == "new-subject"

        same = ensure_user_record(session, auth_user)
        assert same.id == db_user.id
