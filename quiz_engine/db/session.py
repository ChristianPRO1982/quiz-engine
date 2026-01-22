"""Session factory for quiz-engine."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from .engine import get_engine


@lru_cache
def _sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    session = _sessionmaker()()
    try:
        yield session
    finally:
        session.close()
