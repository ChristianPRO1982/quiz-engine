"""Pytest test-suite bootstrap configuration."""

from __future__ import annotations


def pytest_configure(config) -> None:  # noqa: ANN001
    plugin_manager = config.pluginmanager
    if plugin_manager.has_plugin("anyio") or plugin_manager.has_plugin(
        "anyio.pytest_plugin"
    ):
        return
    plugin_manager.import_plugin("anyio.pytest_plugin")
