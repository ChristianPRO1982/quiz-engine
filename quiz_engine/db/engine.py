"""Database engine helpers for quiz-engine."""

from __future__ import annotations

import os
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine.url import make_url


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set.")

    kwargs: dict[str, object] = {
        "echo": _env_bool("DB_ECHO"),
        "pool_pre_ping": True,
    }

    parsed_url = make_url(url)
    if parsed_url.get_backend_name().startswith("postgresql"):
        search_path = os.getenv("DB_SEARCH_PATH", "qe,public").strip()
        if search_path:
            kwargs["connect_args"] = {"options": f"-csearch_path={search_path}"}

    return create_engine(url, **kwargs)
