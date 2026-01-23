"""Alembic environment for qe_* only migrations."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

config = context.config


def _target_metadata():
    import quiz_engine.models  # noqa: F401
    from quiz_engine.db.base import Base

    return Base.metadata


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set for Alembic.")
    return url


def _include_object(object_, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    if type_ == "table":
        return name.startswith("qe_")
    table = getattr(object_, "table", None)
    if table is not None:
        return table.name.startswith("qe_")
    return True


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=_target_metadata(),
        literal_binds=True,
        compare_type=True,
        include_object=_include_object,
        version_table="qe_alembic_version",
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        {"sqlalchemy.url": _database_url()},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=_target_metadata(),
            compare_type=True,
            include_object=_include_object,
            version_table="qe_alembic_version",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
