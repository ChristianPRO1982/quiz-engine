"""Focused tests for auth dependency and service helper branches."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException

import quiz_engine.models  # noqa: F401
from auth.deps import SESSION_AUTH_USER_KEY, get_current_user, require_current_user
from auth.models import AuthUser
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User
from quiz_engine.services.auth_service import list_dev_user_subjects, user_has_role


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "auth_helpers.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
    monkeypatch.setenv("AUTH_MODE", "dev")
    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())


def test_get_current_user_casts_email_and_validates_required_fields(
    monkeypatch,
) -> None:
    request = SimpleNamespace()

    monkeypatch.setattr(
        "auth.deps.get_session_data",
        lambda _request: {
            SESSION_AUTH_USER_KEY: {
                "subject": "sub-1",
                "display_name": "Display",
                "auth_mode": "dev",
                "email": 123,
            }
        },
    )
    user = get_current_user(request)
    assert user == AuthUser(
        subject="sub-1",
        display_name="Display",
        email="123",
        auth_mode="dev",
    )

    monkeypatch.setattr(
        "auth.deps.get_session_data",
        lambda _request: {
            SESSION_AUTH_USER_KEY: {
                "subject": "",
                "display_name": "Display",
                "auth_mode": "dev",
            }
        },
    )
    assert get_current_user(request) is None


def test_require_current_user_raises_when_missing(monkeypatch) -> None:
    request = SimpleNamespace()
    monkeypatch.setattr(
        "auth.deps.get_session_data",
        lambda _request: {},
    )

    try:
        require_current_user(request)
        raise AssertionError("Expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 401


def test_auth_service_lists_subjects_and_handles_blank_role(
    tmp_path: Path, monkeypatch
) -> None:
    _setup_db(tmp_path, monkeypatch)

    with get_session() as session:
        session.add_all([User(subject="zeta"), User(subject="alpha")])
        session.commit()

    with get_session() as session:
        subjects = list_dev_user_subjects(session)
        assert subjects == ["alpha", "zeta"]
        assert user_has_role(session, user_id=1, role="") is False
