"""Tests for plugin registry service used by quiz editor."""

from __future__ import annotations

from types import SimpleNamespace

from quiz_engine.contracts.runtime_models import PluginManifest
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


def test_list_question_types_returns_slide_when_registry_missing() -> None:
    request = _request_with_registry(None)

    options = PluginRegistryService().list_question_types(request)

    assert len(options) == 1
    assert options[0].type == "slide"
    assert options[0].label == "Slide"


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


def test_build_preview_view_model_uses_plugin_runtime_for_slide() -> None:
    service = PluginRegistryService()
    request = _request_with_registry(build_default_registry())

    view_model = service.build_preview_view_model(
        request,
        quiz_id=42,
        stage_index=0,
        stage_id="slide-1",
        plugin_id="slide",
        stage_title="Welcome",
        plugin_spec={
            "schema_version": "v0",
            "type": "slide",
            "content": {
                "title": "Welcome",
                "body": "Body",
                "media": {"type": "none", "src": None},
            },
        },
    )

    assert view_model["kind"] == "plugin_frame"
    assert view_model["is_placeholder"] is False
    assert view_model["payload"]["title"] == "Welcome"
    assert view_model["payload"]["body"] == "Body"


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
