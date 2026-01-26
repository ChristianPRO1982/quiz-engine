"""Plugin interfaces and registry."""

from .interfaces import IPlugin, IStageRuntime
from .registry import PluginRegistry

__all__ = ["IPlugin", "IStageRuntime", "PluginRegistry"]
