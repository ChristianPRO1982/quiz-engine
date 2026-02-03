"""Tests for database engine helpers."""

from __future__ import annotations

import pytest

from quiz_engine.db.engine import _env_bool, get_engine


def test_env_bool_parses_values(monkeypatch) -> None:
    monkeypatch.delenv("FLAG", raising=False)
    assert _env_bool("FLAG") is False

    monkeypatch.setenv("FLAG", "true")
    assert _env_bool("FLAG") is True

    monkeypatch.setenv("FLAG", "0")
    assert _env_bool("FLAG", default=True) is False


def test_get_engine_requires_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_engine.cache_clear()

    with pytest.raises(RuntimeError):
        get_engine()

    get_engine.cache_clear()


def test_get_engine_uses_env(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("DB_ECHO", "1")
    get_engine.cache_clear()

    engine = get_engine()

    assert str(engine.url) == "sqlite+pysqlite:///:memory:"
    assert engine.echo is True

    get_engine.cache_clear()
