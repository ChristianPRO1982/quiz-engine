"""Tests for plugin registry behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module
from types import SimpleNamespace

import pytest

import quiz_engine.plugins.registry as registry_module
from quiz_engine.contracts.runtime_models import (
    PluginManifest,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime
from quiz_engine.plugins.registry import (
    PluginRegistry,
    _iter_plugin_module_names,
    _load_plugin_from_module_name,
    build_default_registry,
    discover_available_plugins,
)


class DummyStageRuntime(IStageRuntime):
    def __init__(self, session_id: str, stage: StageDefinition) -> None:
        self._session_id = session_id
        self._stage = stage

    def on_stage_open(self, context):
        return None

    def on_player_event(self, event, trace):
        return None

    def on_host_action(self, action, trace):
        return None

    def is_finished(self, trace: StageTrace) -> bool:
        return True

    def build_outcome(self, trace: StageTrace) -> StageOutcome:
        return StageOutcome(
            session_id=trace.session_id,
            stage_id=trace.stage_id,
            stage_index=trace.stage_index,
            plugin_id=self._stage.plugin_id,
            completed_at=datetime.now(UTC),
        )


class DummyPlugin(IPlugin):
    def __init__(self) -> None:
        self._manifest = PluginManifest(
            plugin_id="dummy.plugin",
            plugin_version="0.0.0",
            display_name="Dummy",
            schema_version="v0",
        )

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        return DummyStageRuntime(session_id, stage)


def _stage_definition() -> StageDefinition:
    return StageDefinition(
        stage_id="stage-1",
        stage_index=0,
        plugin_id="dummy.plugin",
        stage_kind="question",
        engine_prompt={},
        plugin_spec={},
    )


def test_registry_registers_and_gets_plugin() -> None:
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)

    resolved = registry.get("dummy.plugin")
    assert resolved is plugin


def test_registry_lists_manifests() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())

    manifests = registry.list_manifests()
    assert len(manifests) == 1
    assert manifests[0].plugin_id == "dummy.plugin"


def test_registry_rejects_duplicate_plugin_id() -> None:
    registry = PluginRegistry()
    registry.register(DummyPlugin())

    with pytest.raises(ValueError):
        registry.register(DummyPlugin())


def test_plugin_creates_runtime() -> None:
    plugin = DummyPlugin()
    runtime = plugin.create_runtime("session-1", _stage_definition())
    assert isinstance(runtime, DummyStageRuntime)


def test_default_registry_registers_slide_plugin() -> None:
    registry = build_default_registry()

    plugin = registry.get("slide")
    assert plugin is not None
    assert plugin.get_manifest().plugin_id == "slide"


def test_default_registry_falls_back_to_sandbox_slide_when_import_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = import_module

    def _failing_import(name: str):  # noqa: ANN202
        if name == "quiz_engine.plugins.slide":
            raise ModuleNotFoundError("slide package removed")
        return real_import(name)

    monkeypatch.setattr(registry_module, "import_module", _failing_import)

    registry = build_default_registry()
    plugin = registry.get("slide")

    assert plugin is not None
    assert plugin.get_manifest().plugin_id == "slide"
    assert plugin.get_manifest().capabilities is not None
    assert plugin.get_manifest().capabilities.get("sandbox_mode") is True


def test_discover_available_plugins_reports_duplicate_plugin_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _DuplicatePlugin(DummyPlugin):
        pass

    monkeypatch.setattr(
        registry_module,
        "_iter_plugin_module_names",
        lambda: ["mod_a", "mod_b"],
    )
    monkeypatch.setattr(
        registry_module,
        "_load_plugin_from_module_name",
        lambda _module, _errors: _DuplicatePlugin(),
    )

    result = discover_available_plugins()
    assert len(result.plugins) == 1
    assert len(result.errors) == 1
    assert "Duplicate plugin_id discovered" in result.errors[0]


def test_iter_plugin_module_names_skips_private_and_internal(monkeypatch) -> None:
    monkeypatch.setattr(
        registry_module,
        "iter_modules",
        lambda _path: [
            SimpleNamespace(name="_private"),
            SimpleNamespace(name="registry"),
            SimpleNamespace(name="slide"),
            SimpleNamespace(name="mcq"),
        ],
    )
    names = _iter_plugin_module_names()
    assert names == ["mcq", "slide"]


def test_load_plugin_from_module_name_handles_missing_plugin_class(monkeypatch) -> None:
    errors: list[str] = []
    module = SimpleNamespace(__name__="quiz_engine.plugins.empty")
    monkeypatch.setattr(registry_module, "import_module", lambda _path: module)

    loaded = _load_plugin_from_module_name("empty", errors)
    assert loaded is None
    assert errors == []


def test_load_plugin_from_module_name_handles_instantiation_error(monkeypatch) -> None:
    def _init(self) -> None:  # noqa: ANN001
        raise RuntimeError("boom")

    def _manifest(self) -> PluginManifest:  # noqa: ANN001
        return PluginManifest(
            plugin_id="broken",
            plugin_version="1.0.0",
            display_name="Broken",
            schema_version="v0",
        )

    def _runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:  # noqa: ANN001
        raise NotImplementedError

    broken_plugin = type(
        "BrokenPlugin",
        (IPlugin,),
        {
            "__init__": _init,
            "get_manifest": _manifest,
            "create_runtime": _runtime,
        },
    )
    broken_plugin.__module__ = "quiz_engine.plugins.broken"

    module = SimpleNamespace(
        __name__="quiz_engine.plugins.broken",
        BrokenPlugin=broken_plugin,
    )
    monkeypatch.setattr(registry_module, "import_module", lambda _path: module)

    errors: list[str] = []
    loaded = _load_plugin_from_module_name("broken", errors)
    assert loaded is None
    assert len(errors) == 1
    assert "Failed to instantiate quiz_engine.plugins.broken.BrokenPlugin" in errors[0]


def test_dummy_runtime_methods_are_exercised_for_coverage() -> None:
    runtime = DummyStageRuntime("session-1", _stage_definition())
    assert runtime.on_stage_open(None) is None
    assert runtime.on_player_event(None, None) is None
    assert runtime.on_host_action(None, None) is None
    assert runtime.is_finished(None) is True
    outcome = runtime.build_outcome(
        StageTrace(
            session_id="session-1",
            stage_id="stage-1",
            stage_index=0,
            started_at=datetime.now(UTC),
        )
    )
    assert outcome.plugin_id == "dummy.plugin"
