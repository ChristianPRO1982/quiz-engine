"""Built-in MCQ plugin implementation."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from quiz_engine.contracts.runtime_models import (
    PlayerEvent,
    PluginFrame,
    PluginManifest,
    ScoreDelta,
    StageContext,
    StageDefinition,
    StageOutcome,
    StageTrace,
)
from quiz_engine.plugins.interfaces import IPlugin, IStageRuntime
from quiz_engine.plugins.mcq.config import MCQConfig, load_mcq_config
from quiz_engine.plugins.mcq.schemas import (
    build_mcq_frame_payload,
    extract_choice_weights,
    extract_correct_choice_ids,
    validate_mcq_plugin_spec,
)

MCQ_PLUGIN_ID = "mcq"
_SUPPORTED_BOT_MODES = {
    "influence_bots",
    "influence_bots_nice",
    "influence_bots_evil",
}
_SUPPORTED_INFLUENCE_MODES = {
    "influence",
    "influence_bots",
    "influence_bots_nice",
    "influence_bots_evil",
}


class MCQPlugin(IPlugin):
    """Multiple-choice quiz plugin with deterministic scoring."""

    def __init__(self, *, config: MCQConfig | None = None) -> None:
        self._config = config or load_mcq_config()
        self._manifest = PluginManifest(
            plugin_id=MCQ_PLUGIN_ID,
            plugin_version="1.1.0",
            display_name="MCQ",
            schema_version="v0",
            description=(
                "Multiple-choice quiz stage with oneclick, multianswer and "
                "influence modes."
            ),
            plugin_type="quiz",
            capabilities={
                "general_type": "quiz",
                "produces_scoring": True,
                "produces_grading": False,
                "uses_seed": True,
                "supports_intermediate_updates": True,
                "live_frames": True,
                "multi_phase": True,
                "supports_host_actions": True,
                "supports_no_score": False,
            },
            stage_config_schema={
                "type": "object",
                "required": ["schema_version", "plugin", "mode", "content", "choices"],
                "properties": {
                    "schema_version": {
                        "type": "string",
                        "enum": ["v1"],
                        "title": "Schema version",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["quiz"],
                        "title": "Type",
                    },
                    "plugin": {
                        "type": "string",
                        "enum": ["mcq"],
                        "title": "Plugin",
                    },
                    "content": {
                        "type": "object",
                        "required": ["title", "body"],
                        "title": "Content",
                        "properties": {
                            "title": {
                                "type": "string",
                                "title": "Title",
                                "default": "New MCQ question",
                            },
                            "body": {
                                "type": "string",
                                "title": "Body",
                                "description": "Question prompt shown to players.",
                                "x-ui-widget": "markdown",
                                "default": "Write your question here.",
                            },
                            "body_format": {
                                "type": "string",
                                "title": "Body format",
                                "enum": ["text", "markdown"],
                                "default": "markdown",
                            },
                        },
                    },
                    "mode": {
                        "type": "string",
                        "title": "Mode",
                        "enum": list(self._config.enabled_modes),
                        "default": self._config.enabled_modes[0],
                    },
                    "time_limit_s": {
                        "type": "integer",
                        "title": "Time limit (seconds)",
                        "enum": list(self._config.allowed_time_limits_s),
                        "default": self._config.default_time_limit_s,
                    },
                    "points": {
                        "type": "integer",
                        "title": "Points",
                        "minimum": self._config.min_points,
                        "maximum": self._config.max_points,
                        "default": self._config.default_points,
                    },
                    "examination": {
                        "type": "boolean",
                        "title": "Examination mode",
                        "default": False,
                    },
                    "choices": {
                        "type": "array",
                        "title": "Choices",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "label": {"type": "string"},
                                "is_correct": {"type": "boolean"},
                                "weight": {"type": "integer"},
                            },
                        },
                    },
                },
            },
            default_stage_config={
                "schema_version": "v1",
                "type": "quiz",
                "plugin": "mcq",
                "content": {
                    "title": "New MCQ question",
                    "body": "Write your question here.",
                    "body_format": "markdown",
                },
                "mode": "oneclick",
                "time_limit_s": self._config.default_time_limit_s,
                "points": self._config.default_points,
                "examination": False,
                "choices": [
                    {"id": "a", "label": "Choice A", "is_correct": True},
                    {"id": "b", "label": "Choice B", "is_correct": False},
                ],
            },
            editor_hints={"default_title_prefix": "Question"},
        )

    def get_manifest(self) -> PluginManifest:
        return self._manifest

    def create_runtime(self, session_id: str, stage: StageDefinition) -> IStageRuntime:
        if stage.plugin_id != MCQ_PLUGIN_ID:
            raise ValueError(
                f"MCQ plugin cannot create runtime for plugin_id={stage.plugin_id!r}."
            )
        validated_spec = validate_mcq_plugin_spec(
            stage.plugin_spec,
            config=self._config,
        )
        return MCQStageRuntime(
            session_id=session_id,
            stage=stage,
            plugin_spec=validated_spec,
            config=self._config,
        )


@dataclass
class _PlayerAnswerState:
    selected_choice_ids: set[str] = field(default_factory=set)
    submitted_choice_ids: set[str] | None = None
    submitted_at: datetime | None = None
    locked: bool = False


class MCQStageRuntime(IStageRuntime):
    """Runtime for one MCQ stage instance."""

    def __init__(
        self,
        *,
        session_id: str,
        stage: StageDefinition,
        plugin_spec: dict[str, Any],
        config: MCQConfig,
    ) -> None:
        self._session_id = session_id
        self._stage = stage
        self._plugin_spec = plugin_spec
        self._config = config
        self._host_ended = False
        self._opened_player_ids: list[str] = []

    def on_stage_open(self, context: StageContext) -> list[PluginFrame] | None:
        self._opened_player_ids = [player.player_id for player in context.players]
        prestart_countdown_s = _extract_prestart_countdown_s(context.transport_hints)
        payload = build_mcq_frame_payload(
            self._plugin_spec,
            config=self._config,
            player_count=len(context.players),
            phase="ANSWERING",
            prestart_countdown_s=prestart_countdown_s,
        )
        return [
            PluginFrame(
                session_id=context.session_id,
                stage_id=context.stage.stage_id,
                stage_index=context.stage.stage_index,
                plugin_id=context.stage.plugin_id,
                audience="ALL",
                frame_type="VIEW_MODEL",
                payload=payload,
                sent_at=context.server_now,
            )
        ]

    def on_player_event(
        self, event: PlayerEvent, trace: StageTrace
    ) -> list[PluginFrame] | None:
        if event.type not in {"MCQ_PLAYER_SELECT", "MCQ_PLAYER_SUBMIT"}:
            return None

        states = self._compute_player_states(trace)
        answered_count = sum(
            1 for state in states.values() if state.submitted_choice_ids is not None
        )
        payload = {
            "plugin": "mcq",
            "stage_id": trace.stage_id,
            "mode": self._plugin_spec["mode"],
            "answered_count": answered_count,
            "player_count": max(len(self._opened_player_ids), len(states)),
        }
        return [
            PluginFrame(
                session_id=trace.session_id,
                stage_id=trace.stage_id,
                stage_index=trace.stage_index,
                plugin_id=self._stage.plugin_id,
                audience="ALL",
                frame_type="MCQ_LIVE_STATS",
                payload=payload,
                sent_at=event.server_received_at,
            )
        ]

    def on_host_action(
        self, action: dict[str, Any], trace: StageTrace
    ) -> list[PluginFrame] | None:
        action_type = str(action.get("type") or "").strip()
        if action_type == "MCQ_HOST_END":
            self._host_ended = True
        return None

    def is_finished(self, trace: StageTrace) -> bool:
        return self._host_ended

    def build_outcome(self, trace: StageTrace) -> StageOutcome:
        player_states = self._compute_player_states(trace)
        player_ids = set(self._opened_player_ids) | set(player_states.keys())
        ordered_player_ids = sorted(player_ids)
        score_deltas: list[ScoreDelta] = []
        distribution = _empty_distribution(self._plugin_spec["choices"])

        for player_id in ordered_player_ids:
            state = player_states.get(player_id, _PlayerAnswerState())
            chosen_ids = state.submitted_choice_ids or set()
            for choice_id in chosen_ids:
                if choice_id in distribution:
                    distribution[choice_id] += 1
            score_value, reason = self._compute_player_score(state, trace)
            score_deltas.append(
                ScoreDelta(
                    player_id=player_id,
                    delta_score=score_value,
                    reason=reason,
                )
            )

        bot_stats = self._simulate_bot_votes(
            player_count=max(len(self._opened_player_ids), len(ordered_player_ids))
        )
        for choice_id, bot_votes in bot_stats["distribution"].items():
            if choice_id in distribution:
                distribution[choice_id] += bot_votes

        render_summary = {
            "plugin": "mcq",
            "mode": self._plugin_spec["mode"],
            "title": self._plugin_spec["title"],
            "prompt": self._plugin_spec["prompt"],
            "examination": self._plugin_spec["examination"],
            "time_limit_s": self._plugin_spec["time_limit_s"],
            "points": self._plugin_spec["points"],
            "correct_choice_ids": sorted(extract_correct_choice_ids(self._plugin_spec)),
            "distribution": distribution,
            "player_count": len(ordered_player_ids),
            "answered_count": sum(
                1
                for player_id in ordered_player_ids
                if (
                    player_states.get(player_id) or _PlayerAnswerState()
                ).submitted_choice_ids
            ),
            "bot_count": bot_stats["bot_count"],
            "bot_distribution": bot_stats["distribution"],
        }

        return StageOutcome(
            session_id=self._session_id,
            stage_id=self._stage.stage_id,
            stage_index=self._stage.stage_index,
            plugin_id=self._stage.plugin_id,
            completed_at=trace.ended_at or trace.started_at,
            score_deltas=score_deltas,
            grade_deltas=None,
            render_summary=render_summary,
            plugin_state_out={
                "phase": "DONE",
                "host_ended": self._host_ended,
                "mode": self._plugin_spec["mode"],
            },
        )

    def _compute_player_score(
        self,
        state: _PlayerAnswerState,
        trace: StageTrace,
    ) -> tuple[int, str]:
        submitted_ids = state.submitted_choice_ids
        if submitted_ids is None:
            return 0, "no_answer"

        mode = self._plugin_spec["mode"]
        if mode == "multianswer":
            weights = extract_choice_weights(self._plugin_spec)
            mode_value = sum(weights.get(choice_id, 0) for choice_id in submitted_ids)
        else:
            correct_choice_ids = extract_correct_choice_ids(self._plugin_spec)
            selected_id = next(iter(submitted_ids), None)
            mode_value = 1 if selected_id in correct_choice_ids else 0

        score = self._compute_final_score(
            points=self._plugin_spec["points"],
            mode_value=mode_value,
            submitted_at=state.submitted_at,
            started_at=trace.started_at,
            time_limit_s=self._plugin_spec["time_limit_s"],
        )
        if mode == "multianswer":
            return score, "multianswer"
        return score, "correct" if mode_value > 0 else "incorrect"

    def _compute_player_states(
        self, trace: StageTrace
    ) -> dict[str, _PlayerAnswerState]:
        mode = self._plugin_spec["mode"]
        choice_ids = {choice["id"] for choice in self._plugin_spec["choices"]}
        states: dict[str, _PlayerAnswerState] = {}

        for event in trace.events:
            if event.type not in {"MCQ_PLAYER_SELECT", "MCQ_PLAYER_SUBMIT"}:
                continue

            state = states.setdefault(event.player_id, _PlayerAnswerState())
            payload = event.payload if isinstance(event.payload, dict) else {}

            if mode == "multianswer":
                if event.type == "MCQ_PLAYER_SELECT" and not state.locked:
                    next_selection = _resolve_multianswer_selection(
                        payload=payload,
                        current_selection=state.selected_choice_ids,
                        valid_choice_ids=choice_ids,
                    )
                    if next_selection is not None:
                        state.selected_choice_ids = next_selection
                elif event.type == "MCQ_PLAYER_SUBMIT" and not state.locked:
                    state.submitted_choice_ids = set(state.selected_choice_ids)
                    state.submitted_at = event.server_received_at
                    state.locked = True
                continue

            if event.type != "MCQ_PLAYER_SELECT":
                continue

            choice_id = _extract_single_choice_id(payload, choice_ids=choice_ids)
            if choice_id is None:
                continue

            if mode == "oneclick":
                if state.locked:
                    continue
                state.selected_choice_ids = {choice_id}
                state.submitted_choice_ids = {choice_id}
                state.submitted_at = event.server_received_at
                state.locked = True
                continue

            if mode in _SUPPORTED_INFLUENCE_MODES:
                state.selected_choice_ids = {choice_id}
                state.submitted_choice_ids = {choice_id}
                state.submitted_at = event.server_received_at
                continue

        return states

    def _compute_final_score(
        self,
        *,
        points: int,
        mode_value: int,
        submitted_at: datetime | None,
        started_at: datetime,
        time_limit_s: int,
    ) -> int:
        if mode_value == 0:
            return 0
        if time_limit_s == 0:
            return points * mode_value
        if submitted_at is None:
            return 0

        elapsed_s = (submitted_at - started_at).total_seconds()
        clamped_elapsed_s = min(max(elapsed_s, 0.0), float(time_limit_s))
        time_factor = 1.0 - (clamped_elapsed_s / float(time_limit_s))
        raw_score = float(points * mode_value) * time_factor
        return int(round(raw_score))

    def _simulate_bot_votes(self, *, player_count: int) -> dict[str, Any]:
        mode = self._plugin_spec["mode"]
        distribution = _empty_distribution(self._plugin_spec["choices"])
        if mode not in _SUPPORTED_BOT_MODES:
            return {"bot_count": 0, "distribution": distribution}

        bot_count = max(self._config.min_bots, player_count)
        if bot_count == 0:
            return {"bot_count": 0, "distribution": distribution}

        choice_ids = [choice["id"] for choice in self._plugin_spec["choices"]]
        correct_ids = sorted(extract_correct_choice_ids(self._plugin_spec))
        incorrect_ids = [
            choice_id for choice_id in choice_ids if choice_id not in correct_ids
        ]
        rng = random.Random(_derive_runtime_seed(self._stage, self._session_id))

        for _ in range(bot_count):
            choice_id = _draw_bot_choice(
                rng=rng,
                mode=mode,
                choice_ids=choice_ids,
                correct_ids=correct_ids,
                incorrect_ids=incorrect_ids,
                config=self._config,
            )
            distribution[choice_id] += 1

        return {"bot_count": bot_count, "distribution": distribution}


def _resolve_multianswer_selection(
    *,
    payload: dict[str, Any],
    current_selection: set[str],
    valid_choice_ids: set[str],
) -> set[str] | None:
    choice_ids_payload = payload.get("choice_ids")
    if isinstance(choice_ids_payload, list):
        normalized = {
            str(choice_id).strip()
            for choice_id in choice_ids_payload
            if isinstance(choice_id, str) and choice_id.strip() in valid_choice_ids
        }
        return normalized

    choice_id = payload.get("choice_id")
    if not isinstance(choice_id, str):
        return None
    normalized_choice_id = choice_id.strip()
    if normalized_choice_id not in valid_choice_ids:
        return None

    selected_flag = payload.get("selected")
    updated = set(current_selection)
    if isinstance(selected_flag, bool):
        if selected_flag:
            updated.add(normalized_choice_id)
        else:
            updated.discard(normalized_choice_id)
        return updated

    if normalized_choice_id in updated:
        updated.discard(normalized_choice_id)
    else:
        updated.add(normalized_choice_id)
    return updated


def _extract_single_choice_id(
    payload: dict[str, Any],
    *,
    choice_ids: set[str],
) -> str | None:
    choice_id = payload.get("choice_id")
    if not isinstance(choice_id, str):
        return None
    normalized = choice_id.strip()
    if normalized not in choice_ids:
        return None
    return normalized


def _extract_prestart_countdown_s(transport_hints: dict[str, Any] | None) -> int | None:
    if not isinstance(transport_hints, dict):
        return None
    value = transport_hints.get("prestart_countdown_s")
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _derive_runtime_seed(stage: StageDefinition, session_id: str) -> int:
    if isinstance(stage.random_seed, int) and not isinstance(stage.random_seed, bool):
        return stage.random_seed
    token = f"{session_id}:{stage.stage_id}:{stage.stage_index}"
    return sum((index + 1) * ord(char) for index, char in enumerate(token))


def _draw_bot_choice(
    *,
    rng: random.Random,
    mode: str,
    choice_ids: list[str],
    correct_ids: list[str],
    incorrect_ids: list[str],
    config: MCQConfig,
) -> str:
    if mode == "influence_bots":
        return rng.choice(choice_ids)

    if mode == "influence_bots_nice":
        correct_ratio = config.bots_good_answer_ratio_nice
    else:
        correct_ratio = config.bots_good_answer_ratio_evil

    draw_correct = rng.random() < correct_ratio
    if draw_correct and correct_ids:
        return rng.choice(correct_ids)
    if incorrect_ids:
        return rng.choice(incorrect_ids)
    return rng.choice(choice_ids)


def _empty_distribution(choices: list[dict[str, Any]]) -> dict[str, int]:
    return {choice["id"]: 0 for choice in choices}


__all__ = ["MCQPlugin", "MCQStageRuntime", "MCQ_PLUGIN_ID"]
