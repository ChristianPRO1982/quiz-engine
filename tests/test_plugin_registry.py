"""Tests for plugin registry behavior."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quiz_engine.contracts.runtime_models import (
    PluginManifest,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime
from quiz_engine.plugins.registry import PluginRegistry


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
