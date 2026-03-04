"""Tests for plugin catalog scanning and synchronization."""

from __future__ import annotations

from pathlib import Path

import pytest

import quiz_engine.models  # noqa: F401
from quiz_engine.contracts.runtime_models import PluginManifest
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime
from quiz_engine.plugins.registry import PluginDiscoveryResult
from quiz_engine.services.plugin_catalog_service import (
    PluginCatalogService,
    _resolve_plugin_type,
)


class _NoopRuntime(IStageRuntime):
    def on_stage_open(self, context):  # noqa: ANN001, ANN201
        return None

    def on_player_event(self, event, trace):  # noqa: ANN001, ANN201
        return None

    def on_host_action(self, action, trace):  # noqa: ANN001, ANN201
        return None

    def is_finished(self, trace) -> bool:  # noqa: ANN001
        return False

    def build_outcome(self, trace):  # noqa: ANN001, ANN201
        raise NotImplementedError


class _FakePlugin(IPlugin):
    def __init__(
        self,
        plugin_id: str,
        *,
        version: str = "1.0.0",
        name: str = "Plugin",
        plugin_type: str = "quiz",
    ) -> None:
        self._manifest = PluginManifest(
            plugin_id=plugin_id,
            plugin_version=version,
            display_name=name,
            schema_version="v0",
            capabilities={"general_type": plugin_type},
        )

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id, stage):  # noqa: ANN001, ANN201
        return _NoopRuntime()


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "plugin_catalog.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())


def test_scan_and_sync_upserts_and_deletes_missing_plugins(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = PluginCatalogService()

    first_plugins = [
        _FakePlugin("alpha.quiz", name="Alpha", plugin_type="quiz"),
        _FakePlugin("slide", name="Slide", plugin_type="info"),
    ]
    second_plugins = [
        _FakePlugin("alpha.quiz", version="2.0.0", name="Alpha", plugin_type="quiz"),
        _FakePlugin("score.wall", name="Wall", plugin_type="scoreboard"),
    ]

    monkeypatch.setattr(
        "quiz_engine.services.plugin_catalog_service.discover_available_plugins",
        lambda include_sandbox_fallback=False: PluginDiscoveryResult(
            plugins=first_plugins, errors=[]
        ),
    )
    with get_session() as session:
        first = service.scan_and_sync(session)
        rows = service.list_catalog(session)

    assert first.added == ["alpha.quiz", "slide"]
    assert first.updated == []
    assert first.removed == []
    assert [row.plugin_id for row in rows] == ["alpha.quiz", "slide"]
    assert [row.plugin_type for row in rows] == ["quiz", "info"]

    monkeypatch.setattr(
        "quiz_engine.services.plugin_catalog_service.discover_available_plugins",
        lambda include_sandbox_fallback=False: PluginDiscoveryResult(
            plugins=second_plugins, errors=[]
        ),
    )
    with get_session() as session:
        second = service.scan_and_sync(session)
        rows = service.list_catalog(session)

    assert second.added == ["score.wall"]
    assert second.updated == ["alpha.quiz"]
    assert second.removed == ["slide"]
    assert [row.plugin_id for row in rows] == ["alpha.quiz", "score.wall"]
    assert [row.plugin_version for row in rows] == ["2.0.0", "1.0.0"]


def test_scan_reports_invalid_plugin_type_and_ignores_plugin(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = PluginCatalogService()

    monkeypatch.setattr(
        "quiz_engine.services.plugin_catalog_service.discover_available_plugins",
        lambda include_sandbox_fallback=False: PluginDiscoveryResult(
            plugins=[_FakePlugin("broken.form", plugin_type="not-a-type")],
            errors=[],
        ),
    )

    with get_session() as session:
        result = service.scan_and_sync(session)
        rows = service.list_catalog(session)

    assert result.errors
    assert rows == []


def test_scan_updates_display_name_and_plugin_type(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = PluginCatalogService()

    monkeypatch.setattr(
        "quiz_engine.services.plugin_catalog_service.discover_available_plugins",
        lambda include_sandbox_fallback=False: PluginDiscoveryResult(
            plugins=[_FakePlugin("alpha.quiz", name="Alpha", plugin_type="quiz")],
            errors=[],
        ),
    )
    with get_session() as session:
        first = service.scan_and_sync(session)
        assert first.added == ["alpha.quiz"]

    monkeypatch.setattr(
        "quiz_engine.services.plugin_catalog_service.discover_available_plugins",
        lambda include_sandbox_fallback=False: PluginDiscoveryResult(
            plugins=[_FakePlugin("alpha.quiz", name="Alpha v2", plugin_type="info")],
            errors=[],
        ),
    )
    with get_session() as session:
        second = service.scan_and_sync(session)
        rows = service.list_catalog(session)

    assert second.updated == ["alpha.quiz"]
    assert rows[0].display_name == "Alpha v2"
    assert rows[0].plugin_type == "info"


def test_resolve_plugin_type_supports_aliases_and_fallbacks() -> None:
    manifest = PluginManifest(
        plugin_id="plugin.x",
        plugin_version="1.0.0",
        display_name="X",
        schema_version="v0",
        capabilities={"plugin_type": "display_score"},
    )
    assert _resolve_plugin_type(manifest) == "scoreboard"

    slide_manifest = PluginManifest(
        plugin_id="slide",
        plugin_version="1.0.0",
        display_name="Slide",
        schema_version="v0",
        capabilities={},
    )
    assert _resolve_plugin_type(slide_manifest) == "info"

    bad_manifest = PluginManifest(
        plugin_id="bad",
        plugin_version="1.0.0",
        display_name="Bad",
        schema_version="v0",
        capabilities={"general_type": 123},
    )
    assert _resolve_plugin_type(bad_manifest) is None


def test_fake_plugin_runtime_helpers_are_exercised() -> None:
    runtime = _NoopRuntime()
    assert runtime.on_stage_open(None) is None
    assert runtime.on_player_event(None, None) is None
    assert runtime.on_host_action(None, None) is None
    assert runtime.is_finished(None) is False
    with pytest.raises(NotImplementedError):
        runtime.build_outcome(None)

    plugin = _FakePlugin("dummy")
    assert plugin.create_runtime("session-1", None) is not None
