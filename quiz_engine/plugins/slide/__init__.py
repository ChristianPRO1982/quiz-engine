"""Built-in SLIDE plugin package."""

from .manifest import SLIDE_PLUGIN_ID, build_slide_manifest
from .runtime import SlidePlugin, SlideStageRuntime
from .schemas import build_slide_frame_payload, validate_slide_plugin_spec

__all__ = [
    "SLIDE_PLUGIN_ID",
    "SlidePlugin",
    "SlideStageRuntime",
    "build_slide_frame_payload",
    "build_slide_manifest",
    "validate_slide_plugin_spec",
]
