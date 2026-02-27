"""Sandbox fallback implementation for the SLIDE plugin."""

from __future__ import annotations

from typing import Any

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PluginFrame,
    PluginManifest,
    StageContext,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime

SANDBOX_SLIDE_PLUGIN_ID = "slide"


class SandboxSlidePlugin(IPlugin):
    """Fallback non-interactive SLIDE plugin.

    Used when the main slide plugin package is unavailable.
    """

    def __init__(self) -> None:
        self._manifest = PluginManifest(
            plugin_id=SANDBOX_SLIDE_PLUGIN_ID,
            plugin_version="1.0.0-sandbox",
            display_name="Slide",
            schema_version="v0",
            description=(
                "Sandbox fallback slide plugin. "
                "Used when the built-in slide package is unavailable."
            ),
            capabilities={
                "general_type": "info",
                "produces_scoring": False,
                "produces_grading": False,
                "uses_seed": False,
                "supports_intermediate_updates": False,
                "sandbox_mode": True,
                "live_frames": True,
                "multi_phase": False,
                "supports_host_actions": False,
                "uses_random_seed": False,
                "supports_no_score": True,
            },
        )

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        if stage.plugin_id != SANDBOX_SLIDE_PLUGIN_ID:
            raise ValueError(
                "Sandbox SLIDE plugin cannot create runtime for "
                f"plugin_id={stage.plugin_id!r}."
            )
        return SandboxSlideStageRuntime(
            session_id=session_id,
            stage=stage,
            frame_payload=_build_sandbox_payload(stage),
        )


class SandboxSlideStageRuntime(IStageRuntime):
    """Fallback runtime for one SLIDE stage instance."""

    def __init__(
        self,
        session_id: str,
        stage: StageDefinition,
        frame_payload: dict[str, Any],
    ) -> None:
        self._session_id = session_id
        self._stage = stage
        self._frame_payload = frame_payload

    def on_stage_open(self, context: StageContext) -> list[PluginFrame] | None:
        return [
            PluginFrame(
                session_id=context.session_id,
                stage_id=context.stage.stage_id,
                stage_index=context.stage.stage_index,
                plugin_id=context.stage.plugin_id,
                audience="ALL",
                frame_type="VIEW_MODEL",
                payload=self._frame_payload,
                sent_at=context.server_now,
            )
        ]

    def on_player_event(
        self, event: PlayerEvent, trace: StageTrace
    ) -> list[PluginFrame] | None:
        return None

    def on_host_action(
        self, action: dict[str, Any], trace: StageTrace
    ) -> list[PluginFrame] | None:
        return None

    def is_finished(self, trace: StageTrace) -> bool:
        return False

    def build_outcome(self, trace: StageTrace) -> StageOutcome:
        return StageOutcome(
            session_id=self._session_id,
            stage_id=self._stage.stage_id,
            stage_index=self._stage.stage_index,
            plugin_id=self._stage.plugin_id,
            completed_at=trace.ended_at or trace.started_at,
            score_deltas=None,
            grade_deltas=None,
            render_summary=None,
            plugin_state_out={"sandbox_mode": True},
        )


def _build_sandbox_payload(stage: StageDefinition) -> dict[str, Any]:
    plugin_spec = stage.plugin_spec if isinstance(stage.plugin_spec, dict) else {}
    content = plugin_spec.get("content")
    source = content if isinstance(content, dict) else plugin_spec

    title = _coerce_text(source.get("title"), _fallback_title(stage))
    body = _coerce_text(
        source.get("body"),
        "Slide content rendered by sandbox fallback plugin.",
    )
    body_format = _coerce_body_format(source.get("body_format"))

    payload: dict[str, Any] = {
        "title": title,
        "body": body,
        "body_format": body_format,
    }

    media = source.get("media")
    if isinstance(media, dict):
        media_type = _coerce_text(media.get("type"), "none").strip().lower()
        media_src = media.get("src")
        if media_type == "image" and isinstance(media_src, str) and media_src.strip():
            payload["media"] = {"type": "image", "src": media_src}
        elif media_type == "none":
            payload["media"] = {"type": "none", "src": None}

    return payload


def _fallback_title(stage: StageDefinition) -> str:
    if isinstance(stage.metadata, dict):
        metadata_title = stage.metadata.get("title")
        if isinstance(metadata_title, str) and metadata_title.strip():
            return metadata_title.strip()
    return f"Stage {stage.stage_index + 1}"


def _coerce_body_format(value: Any) -> str:
    if isinstance(value, str) and value.strip().lower() == "markdown":
        return "markdown"
    return "text"


def _coerce_text(value: Any, default: str) -> str:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
    return default
