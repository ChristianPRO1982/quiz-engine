"""Admin plugin scan authorization and UI tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

import quiz_engine.models  # noqa: F401
from quiz_engine.app import create_app
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.user import User, UserRole
from quiz_engine.services.plugin_catalog_service import PluginCatalogScanResult


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "admin_plugin_scan.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("AUTH_MODE", "dev")
    monkeypatch.setenv("SESSION_SECRET_KEY", "test-secret")
    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())
    with get_session() as session:
        user = User(subject="mod-user")
        non_mod = User(subject="plain-user")
        session.add_all([user, non_mod])
        session.commit()
        session.refresh(user)
        session.add(UserRole(user_id=user.id, role="moderator"))
        session.commit()


def test_admin_page_shows_scan_button_only_for_moderator(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "plain-user"})
    plain_page = client.get("/admin")
    assert plain_page.status_code == 200
    assert "Scan plugins" not in plain_page.text

    client.post("/logout")
    client.post("/login", data={"user": "mod-user"})
    mod_page = client.get("/admin")
    assert mod_page.status_code == 200
    assert "Scan plugins" in mod_page.text


def test_admin_plugin_scan_requires_moderator(tmp_path: Path, monkeypatch) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())

    client.post("/login", data={"user": "plain-user"})
    response = client.post("/admin/plugins/scan")

    assert response.status_code == 403


def test_admin_plugin_scan_redirects_with_summary_for_moderator(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    client = TestClient(create_app())
    client.post("/login", data={"user": "mod-user"})

    monkeypatch.setattr(
        "quiz_engine.routers.admin.plugin_catalog_service.scan_and_sync",
        lambda session: PluginCatalogScanResult(
            scanned_at=datetime.now(UTC),
            discovered_count=3,
            added=["a", "b"],
            updated=["c"],
            removed=["d"],
            errors=["x"],
        ),
    )
    monkeypatch.setattr(
        "quiz_engine.routers.admin.build_default_registry",
        lambda: object(),
    )

    response = client.post("/admin/plugins/scan", follow_redirects=False)

    assert response.status_code == 303
    location = response.headers["location"]
    assert location.startswith("/admin?")
    assert "scan_status=partial" in location
    assert "scan_added=2" in location
    assert "scan_updated=1" in location
    assert "scan_removed=1" in location
    assert "scan_errors=1" in location
