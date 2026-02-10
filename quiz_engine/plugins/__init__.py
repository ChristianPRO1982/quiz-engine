"""Plugin interfaces and registry."""

from .interfaces import IPlugin, IStageRuntime
from .registry import PluginRegistry, build_default_registry

__all__ = ["IPlugin", "IStageRuntime", "PluginRegistry", "build_default_registry"]
