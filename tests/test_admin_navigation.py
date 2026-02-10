"""Sprint 3 tests for admin navigation and landing page."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "sprint3_nav.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")

    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        session.add_all([User(subject="user1"), User(subject="user2")])
        session.commit()


def test_admin_routes_require_authentication(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    response = client.get("/admin", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    quizzes = client.get("/admin/quizzes", follow_redirects=False)
    assert quizzes.status_code == 303
    assert quizzes.headers["location"] == "/login"


def test_authenticated_user_sees_admin_nav_everywhere(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})

    for path in ["/", "/account", "/admin", "/admin/quizzes", "/admin/quizzes/new"]:
        page = client.get(path)
        assert page.status_code == 200
        assert "Admin navigation" in page.text
        assert "Quizzes" in page.text
        assert "New quiz" in page.text


def test_admin_landing_links_are_present(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "user1"})

    page = client.get("/admin")
    assert page.status_code == 200
    assert "My quizzes" in page.text
    assert "Create a new quiz" in page.text
