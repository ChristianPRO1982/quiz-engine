"""Tests for plugin registry service used by quiz editor."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from quiz_engine.contracts.runtime_models import PluginFrame, PluginManifest
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.services.plugin_registry_service import PluginRegistryService


class _FakeRegistry:
    def __init__(self, manifests):
        self._manifests = manifests

    def list_manifests(self):  # noqa: ANN201
        return self._manifests


def _request_with_registry(registry):  # noqa: ANN001, ANN201
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(plugin_registry=registry))
    )


class _FakeRuntimeNoViewModel(IStageRuntime):
    def on_stage_open(self, context):  # noqa: ANN001, ANN201
        return [
            PluginFrame(
                session_id=context.session_id,
                stage_id=context.stage.stage_id,
                stage_index=context.stage.stage_index,
                plugin_id=context.stage.plugin_id,
                audience="ALL",
                frame_type="PATCH",
                payload={"delta": 1},
                sent_at=datetime.now(UTC),
            )
        ]

    def on_player_event(self, event, trace):  # noqa: ANN001, ANN201
        return None

    def on_host_action(self, action, trace):  # noqa: ANN001, ANN201
        return None

    def is_finished(self, trace) -> bool:  # noqa: ANN001
        return False

    def build_outcome(self, trace):  # noqa: ANN001, ANN201
        raise NotImplementedError


class _FakePluginRaises(IPlugin):
    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="boom",
            plugin_version="1.0.0",
            display_name="Boom",
            schema_version="v0",
        )

    def create_runtime(self, session_id, stage):  # noqa: ANN001, ANN201
        raise RuntimeError("boom runtime")


class _FakePluginNoViewModel(IPlugin):
    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id="patch-only",
            plugin_version="1.0.0",
            display_name="Patch only",
            schema_version="v0",
        )

    def create_runtime(self, session_id, stage):  # noqa: ANN001, ANN201
        return _FakeRuntimeNoViewModel()


class _FakeLookupRegistry:
    def __init__(self, plugin=None):  # noqa: ANN001
        self._plugin = plugin

    def list_manifests(self):  # noqa: ANN201
        return []

    def get(self, plugin_id):  # noqa: ANN001, ANN201
        if self._plugin is None:
            return None
        return self._plugin


def test_list_question_types_returns_slide_when_registry_missing() -> None:
    request = _request_with_registry(None)

    options = PluginRegistryService().list_question_types(request)

    assert len(options) == 1
    assert options[0].type == "slide"
    assert options[0].label == "Slide"
    assert options[0].plugin_type == "info"
    assert options[0].default_stage_config == {}


def test_list_question_types_adds_slide_and_sorts_when_missing() -> None:
    manifests = [
        PluginManifest(
            plugin_id="poll",
            plugin_version="1.0.0",
            display_name="Poll",
            schema_version="v0",
            description="poll",
        ),
        PluginManifest(
            plugin_id="alpha",
            plugin_version="1.0.0",
            display_name="Alpha",
            schema_version="v0",
            description="alpha",
        ),
    ]
    request = _request_with_registry(_FakeRegistry(manifests))

    options = PluginRegistryService().list_question_types(request)

    assert [option.type for option in options] == ["alpha", "poll", "slide"]


def test_list_question_types_keeps_existing_slide_without_duplicate() -> None:
    manifests = [
        PluginManifest(
            plugin_id="slide",
            plugin_version="1.0.0",
            display_name="Slide",
            schema_version="v0",
            description="slide",
        ),
        PluginManifest(
            plugin_id="poll",
            plugin_version="1.0.0",
            display_name="Poll",
            schema_version="v0",
            description="poll",
        ),
    ]
    request = _request_with_registry(_FakeRegistry(manifests))

    options = PluginRegistryService().list_question_types(request)

    slide_count = len([option for option in options if option.type == "slide"])
    assert slide_count == 1


def test_list_question_types_exposes_plugin_authoring_metadata() -> None:
    manifests = [
        PluginManifest(
            plugin_id="alpha",
            plugin_version="1.0.0",
            display_name="Alpha",
            schema_version="v0",
            plugin_type="quiz",
            stage_config_schema={"type": "object"},
            default_stage_config={"prompt": "Hello"},
            editor_hints={"default_title_prefix": "Alpha"},
        )
    ]
    request = _request_with_registry(_FakeRegistry(manifests))

    options = PluginRegistryService().list_question_types(request)
    alpha = next(option for option in options if option.type == "alpha")

    assert alpha.plugin_type == "quiz"
    assert alpha.stage_config_schema == {"type": "object"}
    assert alpha.default_stage_config == {"prompt": "Hello"}
    assert alpha.editor_hints == {"default_title_prefix": "Alpha"}


def test_build_preview_view_model_uses_plugin_runtime_for_slide() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(build_default_registry())

    view_model = service.build_preview_view_model(
        request,
        quiz_id=42,
        stage_index=0,
        stage_id="slide-1",
        plugin_id="slide",
        stage_title="Question title",
        plugin_spec={
            "schema_version": "v0",
            "type": "slide",
            "content": {
                "title": "Legacy spec title",
                "body": "Body",
                "body_format": "markdown",
                "media": {"type": "none", "src": None},
            },
        },
    )

    assert view_model["kind"] == "plugin_frame"
    assert view_model["is_placeholder"] is False
    assert view_model["payload"]["title"] == "Question title"
    assert view_model["payload"]["body"] == "Body"
    assert view_model["payload"]["body_format"] == "markdown"


def test_build_preview_view_model_falls_back_to_placeholder() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(build_default_registry())

    view_model = service.build_preview_view_model(
        request,
        quiz_id=42,
        stage_index=1,
        stage_id="poll-1",
        plugin_id="poll",
        stage_title="Poll",
        plugin_spec={"options": ["A", "B"]},
    )

    assert view_model["kind"] == "placeholder"
    assert view_model["is_placeholder"] is True
    assert "Preview unavailable" in view_model["payload"]["body"]


def test_build_preview_view_model_returns_placeholder_when_registry_missing() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(None)

    view_model = service.build_preview_view_model(
        request,
        quiz_id=10,
        stage_index=0,
        stage_id="x",
        plugin_id="slide",
        stage_title="Stage",
        plugin_spec={},
    )

    assert view_model["kind"] == "placeholder"
    assert view_model["reason"] == "Plugin registry unavailable."


def test_build_preview_view_model_handles_runtime_exception() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(_FakeLookupRegistry(plugin=_FakePluginRaises()))

    view_model = service.build_preview_view_model(
        request,
        quiz_id=10,
        stage_index=0,
        stage_id="x",
        plugin_id="boom",
        stage_title="Stage",
        plugin_spec={},
    )

    assert view_model["kind"] == "placeholder"
    assert view_model["reason"] == "boom runtime"


def test_build_preview_view_model_handles_missing_view_model_frame() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(
        _FakeLookupRegistry(plugin=_FakePluginNoViewModel())
    )

    view_model = service.build_preview_view_model(
        request,
        quiz_id=10,
        stage_index=0,
        stage_id="x",
        plugin_id="patch-only",
        stage_title="Stage",
        plugin_spec={},
    )

    assert view_model["kind"] == "placeholder"
    assert view_model["reason"] == "No VIEW_MODEL frame produced."
