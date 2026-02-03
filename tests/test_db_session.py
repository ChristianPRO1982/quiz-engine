"""Tests for database session helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session


def test_get_session_yields_and_closes(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    closed = {"value": False}
    original_close = Session.close

    def _close_with_flag(self) -> None:
        closed["value"] = True
        original_close(self)

    monkeypatch.setattr(Session, "close", _close_with_flag)

    with get_session() as session:
        assert isinstance(session, Session)
        assert session.bind is not None

    assert closed["value"] is True
