"""Built-in SLIDE plugin implementation."""

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
from quiz_engine.plugins.slide.schemas import (
    build_slide_frame_payload,
    validate_slide_plugin_spec,
)

SLIDE_PLUGIN_ID = "slide"


class SlidePlugin(IPlugin):
    """Simple informational plugin with no interaction and no scoring."""

    def __init__(self) -> None:
        self._manifest = PluginManifest(
            plugin_id=SLIDE_PLUGIN_ID,
            plugin_version="1.0.0",
            display_name="Slide",
            schema_version="v0",
            description="Informational slide stage (title, markdown body, image).",
            capabilities={
                "general_type": "info",
                "produces_scoring": False,
                "produces_grading": False,
                "uses_seed": False,
                "supports_intermediate_updates": False,
                "live_frames": True,
                "multi_phase": False,
                "supports_host_actions": False,
                "supports_no_score": True,
            },
        )

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        if stage.plugin_id != SLIDE_PLUGIN_ID:
            raise ValueError(
                f"SLIDE plugin cannot create runtime for plugin_id={stage.plugin_id!r}."
            )

        validated_spec = validate_slide_plugin_spec(stage.plugin_spec)
        frame_payload = build_slide_frame_payload(validated_spec)
        return SlideStageRuntime(
            session_id=session_id,
            stage=stage,
            frame_payload=frame_payload,
        )


class SlideStageRuntime(IStageRuntime):
    """Runtime for one slide stage instance."""

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
            plugin_state_out=None,
        )


__all__ = ["SlidePlugin", "SlideStageRuntime", "SLIDE_PLUGIN_ID"]
