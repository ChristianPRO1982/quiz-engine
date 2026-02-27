"""Manifest for the built-in SLIDE plugin."""

from __future__ import annotations

from quiz_engine.contracts.runtime_models import PluginManifest

SLIDE_PLUGIN_ID = "slide"


def build_slide_manifest() -> PluginManifest:
    """Return the manifest for the SLIDE plugin."""
    return PluginManifest(
        plugin_id=SLIDE_PLUGIN_ID,
        plugin_version="1.0.0",
        display_name="Slide",
        schema_version="v0",
        description="Static informational stage with no interaction and no scoring.",
        capabilities={
            "general_type": "info",
            "produces_scoring": False,
            "produces_grading": False,
            "uses_seed": False,
            "supports_intermediate_updates": False,
            "entrypoint": "quiz_engine.plugins.slide.runtime:SlideStageRuntime",
            "stage_config_schema": {
                "type": "object",
                "required": ["schema_version"],
                "properties": {
                    "schema_version": {"type": "string"},
                    "type": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "body_format": {"type": "string"},
                    "media": {"type": ["object", "null"]},
                    "content": {"type": ["object", "null"]},
                },
            },
            "live_frames": True,
            "multi_phase": False,
            "supports_host_actions": False,
            "uses_random_seed": False,
            "supports_no_score": True,
        },
    )
