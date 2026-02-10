"""Plugin registry for quiz-engine."""

from __future__ import annotations

from quiz_engine.contracts.runtime_models import PluginManifest
from quiz_engine.plugins.interfaces import IPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, IPlugin] = {}

    def register(self, plugin: IPlugin) -> None:
        manifest = plugin.get_manifest()
        plugin_id = manifest.plugin_id
        if plugin_id in self._plugins:
            raise ValueError(f"Plugin already registered: {plugin_id}")
        self._plugins[plugin_id] = plugin

    def get(self, plugin_id: str) -> IPlugin | None:
        return self._plugins.get(plugin_id)

    def list_manifests(self) -> list[PluginManifest]:
        return [plugin.get_manifest() for plugin in self._plugins.values()]


def build_default_registry() -> PluginRegistry:
    """Build a plugin registry with built-in plugins explicitly registered."""
    from quiz_engine.plugins.slide import SlidePlugin

    registry = PluginRegistry()
    registry.register(SlidePlugin())
    return registry
