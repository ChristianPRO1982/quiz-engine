"""Runtime implementation for the SLIDE plugin."""

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
from quiz_engine.plugins.slide.manifest import SLIDE_PLUGIN_ID, build_slide_manifest
from quiz_engine.plugins.slide.schemas import build_slide_frame_payload


class SlidePlugin(IPlugin):
    """Built-in non-interactive SLIDE plugin."""

    def __init__(self) -> None:
        self._manifest = build_slide_manifest()

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        if stage.plugin_id != SLIDE_PLUGIN_ID:
            raise ValueError(
                f"SLIDE plugin cannot create runtime for plugin_id={stage.plugin_id!r}."
            )
        frame_payload = build_slide_frame_payload(stage.plugin_spec)
        return SlideStageRuntime(
            session_id=session_id,
            stage=stage,
            frame_payload=frame_payload,
        )


class SlideStageRuntime(IStageRuntime):
    """Runtime for one SLIDE stage instance."""

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
