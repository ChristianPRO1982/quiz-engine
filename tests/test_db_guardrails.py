"""Guardrails for qe_* database isolation."""

from __future__ import annotations

import re
from pathlib import Path

import quiz_engine.models  # noqa: F401
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
    migrations_dir = Path(__file__).resolve().parents[1] / "db" / "migrations" / "sql"
    migrations = sorted(migrations_dir.glob("*.sql"))
    assert migrations, "No SQL migrations found."

    table_patterns: list[str] = [
        r"(?i)\bCREATE\s+TABLE(?:\s+IF\s+NOT\s+EXISTS)?\s+([a-zA-Z0-9_]+)",
        r"(?i)\bDROP\s+TABLE(?:\s+IF\s+EXISTS)?\s+([a-zA-Z0-9_]+)",
        r"(?i)\bALTER\s+TABLE(?:\s+ONLY)?\s+([a-zA-Z0-9_]+)",
        (
            r"(?i)\bCREATE\s+INDEX(?:\s+IF\s+NOT\s+EXISTS)?\s+"
            r"[a-zA-Z0-9_]+\s+ON\s+([a-zA-Z0-9_]+)"
        ),
    ]

    ref_pattern = re.compile(r"(?i)\bREFERENCES\s+([a-zA-Z0-9_]+)\s*\(")

    for path in migrations:
        text = path.read_text(encoding="utf-8")
        table_names: list[str] = []
        for pattern in table_patterns:
            table_names.extend(re.findall(pattern, text))

        allowed_non_qe = {"pg_type", "pg_namespace"}
        non_qe_tables = [
            name
            for name in table_names
            if not name.startswith("qe_") and name not in allowed_non_qe
        ]
        assert not non_qe_tables, (
            f"{path.name} references non qe_ tables: {non_qe_tables}"
        )

        fk_targets = ref_pattern.findall(text)
        non_qe_fk = [name for name in fk_targets if not name.startswith("qe_")]
        assert not non_qe_fk, f"{path.name} contains non qe_ foreign keys: {non_qe_fk}"
