"""Plugin interfaces for quiz-engine runtime."""

from __future__ import annotations

from abc import ABC, abstractmethod
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


class IPlugin(ABC):
    """Minimal plugin API for quiz-engine."""

    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Return the plugin manifest."""

    @abstractmethod
    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        """Create a stage runtime for the given session and stage."""


class IStageRuntime(ABC):
    """Runtime controller for one stage instance."""

    @abstractmethod
    def on_stage_open(self, context: StageContext) -> list[PluginFrame] | None:
        """Handle stage open; may return frames."""

    @abstractmethod
    def on_player_event(
        self, event: PlayerEvent, trace: StageTrace
    ) -> list[PluginFrame] | None:
        """Handle a player event; may return frames."""

    @abstractmethod
    def on_host_action(
        self, action: dict[str, Any], trace: StageTrace
    ) -> list[PluginFrame] | None:
        """Handle a host action; may return frames."""

    @abstractmethod
    def is_finished(self, trace: StageTrace) -> bool:
        """Return True when the stage is finished."""

    @abstractmethod
    def build_outcome(self, trace: StageTrace) -> StageOutcome:
        """Build the final stage outcome."""
