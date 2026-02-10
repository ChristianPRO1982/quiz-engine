"""Tests for plugin registry service used by quiz editor."""

from __future__ import annotations

from types import SimpleNamespace

from quiz_engine.contracts.runtime_models import PluginManifest
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
