"""Manifest for the built-in SLIDE plugin."""

from __future__ import annotations

from quiz_engine.contracts.runtime_models import PluginManifest

SLIDE_PLUGIN_ID = "slide"


def build_slide_manifest() -> PluginManifest:
    """Return the v0 manifest for the SLIDE plugin."""
    return PluginManifest(
        plugin_id=SLIDE_PLUGIN_ID,
        plugin_version="0.1.0",
        display_name="Slide",
        schema_version="v0",
        description="Static informational stage with no interaction and no scoring.",
        capabilities={
            "live_frames": True,
            "multi_phase": False,
            "supports_host_actions": False,
            "uses_random_seed": False,
            "supports_no_score": True,
        },
    )
