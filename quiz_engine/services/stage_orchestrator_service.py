"""Open/close stage orchestration with plugin lifecycle and persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from quiz_engine.contracts.runtime_models import (
    PlayerIdentity,
    PluginFrame,
    StageContext,
    StageDefinition,
    StageOutcome,
)
from quiz_engine.contracts.serialization import datetime_to_iso
from quiz_engine.plugins.registry import PluginRegistry
from quiz_engine.runtime.stage_runner import StageRunner
from quiz_engine.services.session_live_service import LiveSessionState
from quiz_engine.services.session_persist_service import SessionPersistService


class StageOrchestratorService:
    def __init__(self, persist_service: SessionPersistService | None = None) -> None:
        self._persist_service = persist_service or SessionPersistService()

    def build_stages_from_quiz_payload(
        self,
        payload: dict[str, Any] | None,
    ) -> list[StageDefinition]:
        source = payload if isinstance(payload, dict) else {}
        raw_stages = source.get("questions")
        if not isinstance(raw_stages, list):
            raw_stages = source.get("stages")
        if not isinstance(raw_stages, list):
            raw_stages = []

        stages: list[StageDefinition] = []
        for index, raw_stage in enumerate(raw_stages):
            if not isinstance(raw_stage, dict):
                continue
            stage_id = str(
                raw_stage.get("stage_id")
                or raw_stage.get("question_id")
                or f"stage-{index + 1}"
            ).strip()
            plugin_id = str(
                raw_stage.get("plugin_id") or raw_stage.get("type") or "slide"
            ).strip()
            stage_kind = str(raw_stage.get("stage_kind") or plugin_id).strip()

            plugin_spec: dict[str, Any] = {}
            if isinstance(raw_stage.get("plugin_spec"), dict):
                plugin_spec = dict(raw_stage["plugin_spec"])
            elif isinstance(raw_stage.get("spec"), dict):
                plugin_spec = dict(raw_stage["spec"])

            metadata: dict[str, Any] = {}
            title = raw_stage.get("title")
            if isinstance(title, str) and title.strip():
                metadata["title"] = title.strip()

            stages.append(
                StageDefinition(
                    stage_id=stage_id,
                    stage_index=index,
                    plugin_id=plugin_id,
                    stage_kind=stage_kind,
                    engine_prompt={},
                    plugin_spec=plugin_spec,
                    metadata=metadata or None,
                )
            )
        return stages

    def open_stage(
        self,
        session: Session,
        *,
        live_session: LiveSessionState,
        stage_index: int,
        plugin_registry: PluginRegistry,
    ) -> tuple[StageDefinition, list[PluginFrame]] | None:
        if stage_index < 0 or stage_index >= len(live_session.stages):
            return None

        stage = live_session.stages[stage_index]
        plugin = plugin_registry.get(stage.plugin_id)
        if plugin is None:
            raise ValueError(f"Plugin not registered: {stage.plugin_id}")

        runtime = plugin.create_runtime(str(live_session.session_id), stage)
        runner = StageRunner(runtime=runtime)
        context = StageContext(
            session_id=str(live_session.session_id),
            quiz_id=str(live_session.quiz_id),
            stage=stage,
            server_now=datetime.now(UTC),
            players=self._players_for_context(live_session),
        )
        frames = runner.open_stage(context)

        live_session.stage_index = stage.stage_index
        live_session.current_stage_id = stage.stage_id
        live_session.stage_runner = runner

        self._persist_service.record_stage_event(
            session,
            session_id=live_session.session_id,
            stage_id=stage.stage_id,
            stage_index=stage.stage_index,
            payload={
                "event": "stage_opened",
                "at": datetime_to_iso(context.server_now),
            },
        )

        return stage, frames

    def close_current_stage(
        self,
        session: Session,
        *,
        live_session: LiveSessionState,
    ) -> StageOutcome | None:
        runner = live_session.stage_runner
        if runner is None or live_session.stage_index is None:
            return None

        outcome = runner.close_stage()
        self._persist_service.record_stage_outcome(
            session,
            session_id=live_session.session_id,
            outcome=outcome,
        )
        self._persist_service.record_stage_event(
            session,
            session_id=live_session.session_id,
            stage_id=outcome.stage_id,
            stage_index=outcome.stage_index,
            payload={
                "event": "stage_closed",
                "at": datetime_to_iso(outcome.completed_at),
            },
        )

        live_session.current_stage_id = None
        live_session.stage_runner = None
        return outcome

    @staticmethod
    def _players_for_context(live_session: LiveSessionState) -> list[PlayerIdentity]:
        players: list[PlayerIdentity] = []
        for player in sorted(
            live_session.players.values(),
            key=lambda value: (value.nickname.lower(), value.player_id),
        ):
            players.append(
                PlayerIdentity(
                    player_id=str(player.player_id),
                    display_name=player.nickname,
                    is_authenticated=False,
                    participation_mode="GUEST",
                    consents={
                        "gameplay_identity": True,
                        "email_results": False,
                    },
                )
            )
        return players
