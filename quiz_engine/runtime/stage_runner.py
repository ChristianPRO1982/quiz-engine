"""Stage runner orchestration."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PluginFrame,
    StageContext,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.contracts.serialization import ensure_json_like, iso_to_datetime
from quiz_engine.plugins.interfaces import IStageRuntime


class StageRunner:
    def __init__(
        self,
        runtime: IStageRuntime,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._runtime = runtime
        self._clock = clock or (lambda: datetime.now(UTC))
        self._context: StageContext | None = None
        self._trace: StageTrace | None = None
        self._outcome: StageOutcome | None = None

    @property
    def trace(self) -> StageTrace | None:
        return self._trace

    def open_stage(self, context: StageContext) -> list[PluginFrame]:
        if self._context is not None:
            raise ValueError("Stage already opened.")
        self._context = context
        self._trace = StageTrace(
            session_id=context.session_id,
            stage_id=context.stage.stage_id,
            stage_index=context.stage.stage_index,
            started_at=context.server_now,
        )
        frames = self._runtime.on_stage_open(context)
        return self._validate_frames(frames)

    def handle_player_event(self, event_payload: dict[str, Any]) -> list[PluginFrame]:
        if self._context is None or self._trace is None:
            raise ValueError("Stage is not open.")
        if self._outcome is not None:
            raise ValueError("Stage is already closed.")
        if not isinstance(event_payload, dict):
            raise ValueError("event_payload must be a dict.")
        payload = event_payload.get("payload")
        _require_dict(payload, "payload")
        ensure_json_like(payload, "payload")

        client_sent_at = _parse_datetime(event_payload.get("client_sent_at"))

        event = PlayerEvent(
            event_id=event_payload["event_id"],
            session_id=self._context.session_id,
            stage_id=self._context.stage.stage_id,
            stage_index=self._context.stage.stage_index,
            player_id=event_payload["player_id"],
            type=event_payload["type"],
            server_received_at=self._clock(),
            payload=payload,
            client_sent_at=client_sent_at,
            seq=event_payload.get("seq"),
            correlation_id=event_payload.get("correlation_id"),
        )
        self._trace.events.append(event)
        frames = self._runtime.on_player_event(event, self._trace)
        return self._validate_frames(frames)

    def handle_host_action(self, action: dict[str, Any]) -> list[PluginFrame]:
        if self._trace is None:
            raise ValueError("Stage is not open.")
        if self._outcome is not None:
            raise ValueError("Stage is already closed.")
        _require_dict(action, "action")
        ensure_json_like(action, "action")
        frames = self._runtime.on_host_action(action, self._trace)
        return self._validate_frames(frames)

    def close_stage(self) -> StageOutcome:
        """Force stage closure from engine flow (host/quiz progression)."""
        if self._trace is None:
            raise ValueError("Stage is not open.")
        if self._outcome is not None:
            return self._outcome
        if self._trace.ended_at is None:
            self._trace.ended_at = self._clock()
        self._outcome = self._runtime.build_outcome(self._trace)
        self._validate_outcome(self._outcome, self._trace)
        return self._outcome

    def maybe_close(self) -> StageOutcome | None:
        if self._trace is None or self._context is None:
            raise ValueError("Stage is not open.")
        if self._outcome is not None:
            return self._outcome

        if self._is_time_limit_reached(self._context.stage, self._trace):
            return self.close_stage()

        if self._runtime.is_finished(self._trace):
            return self.close_stage()

        return None

    def _is_time_limit_reached(self, stage: StageDefinition, trace: StageTrace) -> bool:
        if stage.time_limit_ms is None:
            return False
        elapsed_ms = (self._clock() - trace.started_at).total_seconds() * 1000
        return elapsed_ms >= stage.time_limit_ms

    @staticmethod
    def _validate_outcome(outcome: StageOutcome, trace: StageTrace) -> None:
        if outcome.session_id != trace.session_id:
            raise ValueError("Outcome session_id does not match trace.")
        if outcome.stage_id != trace.stage_id:
            raise ValueError("Outcome stage_id does not match trace.")
        if outcome.stage_index != trace.stage_index:
            raise ValueError("Outcome stage_index does not match trace.")

    @staticmethod
    def _validate_frames(frames: list[PluginFrame] | None) -> list[PluginFrame]:
        if frames is None:
            return []
        if not isinstance(frames, list):
            raise ValueError("Plugin frames must be a list.")
        for frame in frames:
            if not isinstance(frame, PluginFrame):
                raise ValueError("Plugin frames must contain PluginFrame objects.")
        return frames


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return iso_to_datetime(value)
    raise ValueError("client_sent_at must be an ISO string or datetime.")


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a dict.")
    return value
