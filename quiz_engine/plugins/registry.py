"""Plugin registry for quiz-engine."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from importlib import import_module
from pkgutil import iter_modules

import quiz_engine.plugins as plugins_package
from quiz_engine.contracts.runtime_models import PluginManifest
from quiz_engine.plugins.interfaces import IPlugin

INTERNAL_PLUGIN_MODULES = {"interfaces", "registry", "sandbox_slide"}


@dataclass
class PluginDiscoveryResult:
    plugins: list[IPlugin] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


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
    """Build a plugin registry from discovered plugins."""

    registry = PluginRegistry()
    discovery = discover_available_plugins(include_sandbox_fallback=True)
    for plugin in discovery.plugins:
        registry.register(plugin)
    return registry


def discover_available_plugins(
    *, include_sandbox_fallback: bool = False
) -> PluginDiscoveryResult:
    result = PluginDiscoveryResult()

    discovered: dict[str, IPlugin] = {}
    for module_name in _iter_plugin_module_names():
        plugin = _load_plugin_from_module_name(module_name, result.errors)
        if plugin is None:
            continue
        manifest = plugin.get_manifest()
        if manifest.plugin_id in discovered:
            result.errors.append(
                f"Duplicate plugin_id discovered: {manifest.plugin_id} "
                f"(module: quiz_engine.plugins.{module_name})"
            )
            continue
        discovered[manifest.plugin_id] = plugin

    result.plugins = sorted(
        discovered.values(), key=lambda plugin: plugin.get_manifest().plugin_id
    )

    if include_sandbox_fallback and "slide" not in discovered:
        from quiz_engine.plugins.sandbox_slide import SandboxSlidePlugin

        result.plugins.append(SandboxSlidePlugin())

    return result


def _iter_plugin_module_names() -> list[str]:
    module_names: list[str] = []
    for module_info in iter_modules(plugins_package.__path__):
        name = module_info.name
        if name.startswith("_"):
            continue
        if name in INTERNAL_PLUGIN_MODULES:
            continue
        module_names.append(name)
    return sorted(module_names)


def _load_plugin_from_module_name(
    module_name: str,
    errors: list[str],
) -> IPlugin | None:
    module_path = f"quiz_engine.plugins.{module_name}"
    try:
        module = import_module(module_path)
    except Exception as exc:
        errors.append(f"Failed to import {module_path}: {exc}")
        return None

    plugin_classes = [
        candidate
        for _, candidate in inspect.getmembers(module, inspect.isclass)
        if (
            issubclass(candidate, IPlugin)
            and candidate is not IPlugin
            and candidate.__module__ == module.__name__
            and not inspect.isabstract(candidate)
        )
    ]
    if not plugin_classes:
        return None

    plugin_class = plugin_classes[0]
    try:
        plugin = plugin_class()
    except Exception as exc:
        errors.append(
            f"Failed to instantiate {module_path}.{plugin_class.__name__}: {exc}"
        )
        return None

    return plugin
