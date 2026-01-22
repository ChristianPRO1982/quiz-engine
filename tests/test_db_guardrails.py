"""Guardrails for qe_* database isolation."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from alembic.config import Config

import quiz_engine.models  # noqa: F401
from alembic import command
from quiz_engine.db.base import Base


def test_metadata_tables_are_qe_only():
    tables = list(Base.metadata.tables)
    assert tables, "No tables registered in SQLAlchemy metadata."
    non_qe = [name for name in tables if not name.startswith("qe_")]
    assert not non_qe, f"Non qe_ tables in metadata: {non_qe}"


def test_metadata_fks_are_qe_only():
    violations = []
    for table in Base.metadata.tables.values():
        for fk in table.foreign_keys:
            target = fk.column.table.name
            if not target.startswith("qe_"):
                violations.append((table.name, target))
    assert not violations, f"Non qe_ foreign keys found: {violations}"


def test_migrations_are_qe_only():
    migrations_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    migrations = sorted(migrations_dir.glob("*.py"))
    assert migrations, "No Alembic migrations found."

    table_patterns = [
        r'op\.create_table\("([^"]+)"',
        r'op\.drop_table\("([^"]+)"',
        r'op\.rename_table\("([^"]+)"',
        r'op\.create_index\("[^"]+",\s*"([^"]+)"',
        r'op\.drop_index\("[^"]+",\s*table_name="([^"]+)"',
    ]

    fk_table_pattern = re.compile(r'"([a-zA-Z0-9_]+)\.[^"]+"')
    fk_direct_pattern = re.compile(r'ForeignKey\("([a-zA-Z0-9_]+)\.[^"]+"\)')

    for path in migrations:
        text = path.read_text(encoding="utf-8")
        table_names: list[str] = []
        for pattern in table_patterns:
            table_names.extend(re.findall(pattern, text))

        non_qe_tables = [name for name in table_names if not name.startswith("qe_")]
        assert not non_qe_tables, (
            f"{path.name} references non qe_ tables: {non_qe_tables}"
        )

        fk_blocks = re.findall(r"ForeignKeyConstraint\((.*?)\)", text, flags=re.DOTALL)
        fk_targets = []
        for block in fk_blocks:
            fk_targets.extend(fk_table_pattern.findall(block))
        fk_targets.extend(fk_direct_pattern.findall(text))
        non_qe_fk = [name for name in fk_targets if not name.startswith("qe_")]
        assert not non_qe_fk, f"{path.name} contains non qe_ foreign keys: {non_qe_fk}"


@pytest.mark.skipif(
    "DATABASE_URL_TEST" not in os.environ,
    reason="DATABASE_URL_TEST is not configured.",
)
def test_alembic_upgrade_downgrade(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["DATABASE_URL_TEST"])
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
