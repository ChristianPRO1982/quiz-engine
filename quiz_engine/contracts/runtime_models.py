"""Runtime contract models (schema v0)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from .serialization import datetime_to_iso, ensure_json_like, iso_to_datetime


def _require_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or value.strip() == "":
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer.")
    return value


def _normalize_datetime(value: Any, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime.")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _ensure_json_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dict.")
    ensure_json_like(value, field_name)
    return value


def _optional_field(data: dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        data[key] = value


@dataclass
class PluginManifest:
    plugin_id: str
    plugin_version: str
    display_name: str
    schema_version: str
    description: str | None = None
    plugin_type: str | None = None
    capabilities: dict[str, Any] | None = None
    stage_config_schema: dict[str, Any] | None = None
    default_stage_config: dict[str, Any] | None = None
    editor_hints: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.plugin_id, "plugin_id")
        _require_non_empty_str(self.plugin_version, "plugin_version")
        _require_non_empty_str(self.display_name, "display_name")
        _require_non_empty_str(self.schema_version, "schema_version")
        if self.schema_version != "v0":
            raise ValueError("schema_version must be 'v0'.")
        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("description must be a string or None.")
        if self.plugin_type is not None:
            _require_non_empty_str(self.plugin_type, "plugin_type")
        if self.capabilities is not None:
            _ensure_json_dict(self.capabilities, "capabilities")
        if self.stage_config_schema is not None:
            _ensure_json_dict(self.stage_config_schema, "stage_config_schema")
        if self.default_stage_config is not None:
            _ensure_json_dict(self.default_stage_config, "default_stage_config")
        if self.editor_hints is not None:
            _ensure_json_dict(self.editor_hints, "editor_hints")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "plugin_id": self.plugin_id,
            "plugin_version": self.plugin_version,
            "display_name": self.display_name,
            "schema_version": self.schema_version,
        }
        _optional_field(data, "description", self.description)
        _optional_field(data, "plugin_type", self.plugin_type)
        _optional_field(data, "capabilities", self.capabilities)
        _optional_field(data, "stage_config_schema", self.stage_config_schema)
        _optional_field(data, "default_stage_config", self.default_stage_config)
        _optional_field(data, "editor_hints", self.editor_hints)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> PluginManifest:
        return cls(
            plugin_id=data["plugin_id"],
            plugin_version=data["plugin_version"],
            display_name=data["display_name"],
            schema_version=data["schema_version"],
            description=data.get("description"),
            plugin_type=data.get("plugin_type"),
            capabilities=data.get("capabilities"),
            stage_config_schema=data.get("stage_config_schema"),
            default_stage_config=data.get("default_stage_config"),
            editor_hints=data.get("editor_hints"),
        )


@dataclass
class StageDefinition:
    stage_id: str
    stage_index: int
    plugin_id: str
    stage_kind: str
    engine_prompt: dict[str, Any]
    plugin_spec: dict[str, Any]
    time_limit_ms: int | None = None
    random_seed: int | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.stage_id, "stage_id")
        _require_int(self.stage_index, "stage_index")
        if self.stage_index < 0:
            raise ValueError("stage_index must be >= 0.")
        _require_non_empty_str(self.plugin_id, "plugin_id")
        _require_non_empty_str(self.stage_kind, "stage_kind")
        _ensure_json_dict(self.engine_prompt, "engine_prompt")
        _ensure_json_dict(self.plugin_spec, "plugin_spec")
        if self.time_limit_ms is not None:
            _require_int(self.time_limit_ms, "time_limit_ms")
        if self.random_seed is not None:
            _require_int(self.random_seed, "random_seed")
        if self.metadata is not None:
            _ensure_json_dict(self.metadata, "metadata")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "plugin_id": self.plugin_id,
            "stage_kind": self.stage_kind,
            "engine_prompt": self.engine_prompt,
            "plugin_spec": self.plugin_spec,
        }
        _optional_field(data, "time_limit_ms", self.time_limit_ms)
        _optional_field(data, "random_seed", self.random_seed)
        _optional_field(data, "metadata", self.metadata)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> StageDefinition:
        return cls(
            stage_id=data["stage_id"],
            stage_index=data["stage_index"],
            plugin_id=data["plugin_id"],
            stage_kind=data["stage_kind"],
            engine_prompt=data["engine_prompt"],
            plugin_spec=data["plugin_spec"],
            time_limit_ms=data.get("time_limit_ms"),
            random_seed=data.get("random_seed"),
            metadata=data.get("metadata"),
        )


@dataclass
class PlayerIdentity:
    player_id: str
    display_name: str
    is_authenticated: bool | None = None
    participation_mode: str | None = None
    consents: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.player_id, "player_id")
        _require_non_empty_str(self.display_name, "display_name")
        if self.is_authenticated is not None and not isinstance(
            self.is_authenticated, bool
        ):
            raise ValueError("is_authenticated must be a bool or None.")
        if self.participation_mode is not None:
            if self.participation_mode not in {"LOGGED", "GUEST"}:
                raise ValueError("participation_mode must be LOGGED or GUEST.")
        if self.consents is None:
            raise ValueError("consents is required for participants.")
        _ensure_json_dict(self.consents, "consents")
        gameplay_identity = self.consents.get("gameplay_identity")
        if gameplay_identity is not True:
            raise ValueError("consents.gameplay_identity must be true.")
        email_results = self.consents.get("email_results")
        if email_results is not None and not isinstance(email_results, bool):
            raise ValueError("consents.email_results must be a bool if provided.")
        if self.is_authenticated is False:
            if self.participation_mode not in {None, "GUEST"}:
                raise ValueError("participation_mode must be GUEST if unauthenticated.")
            if email_results:
                raise ValueError("email_results cannot be true for guests.")
        if self.participation_mode == "GUEST" and email_results:
            raise ValueError("email_results cannot be true for guests.")
        if self.metadata is not None:
            _ensure_json_dict(self.metadata, "metadata")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "player_id": self.player_id,
            "display_name": self.display_name,
            "consents": self.consents,
        }
        _optional_field(data, "is_authenticated", self.is_authenticated)
        _optional_field(data, "participation_mode", self.participation_mode)
        _optional_field(data, "metadata", self.metadata)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> PlayerIdentity:
        return cls(
            player_id=data["player_id"],
            display_name=data["display_name"],
            is_authenticated=data.get("is_authenticated"),
            participation_mode=data.get("participation_mode"),
            consents=data.get("consents"),
            metadata=data.get("metadata"),
        )


@dataclass
class StageContext:
    session_id: str
    quiz_id: str
    stage: StageDefinition
    server_now: datetime
    players: list[PlayerIdentity]
    scoreboard_snapshot: dict[str, Any] | None = None
    plugin_state_in: dict[str, Any] | None = None
    transport_hints: dict[str, Any] | None = None
    session_flags: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.session_id, "session_id")
        _require_non_empty_str(self.quiz_id, "quiz_id")
        if not isinstance(self.stage, StageDefinition):
            raise ValueError("stage must be a StageDefinition.")
        self.server_now = _normalize_datetime(self.server_now, "server_now")
        if not isinstance(self.players, list):
            raise ValueError("players must be a list.")
        for player in self.players:
            if not isinstance(player, PlayerIdentity):
                raise ValueError("players must contain PlayerIdentity objects.")
        if self.scoreboard_snapshot is not None:
            _ensure_json_dict(self.scoreboard_snapshot, "scoreboard_snapshot")
        if self.plugin_state_in is not None:
            _ensure_json_dict(self.plugin_state_in, "plugin_state_in")
        if self.transport_hints is not None:
            _ensure_json_dict(self.transport_hints, "transport_hints")
        if self.session_flags is not None:
            _ensure_json_dict(self.session_flags, "session_flags")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "session_id": self.session_id,
            "quiz_id": self.quiz_id,
            "stage": self.stage.to_transport_dict(),
            "server_now": datetime_to_iso(self.server_now),
            "players": [player.to_transport_dict() for player in self.players],
        }
        _optional_field(data, "scoreboard_snapshot", self.scoreboard_snapshot)
        _optional_field(data, "plugin_state_in", self.plugin_state_in)
        _optional_field(data, "transport_hints", self.transport_hints)
        _optional_field(data, "session_flags", self.session_flags)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> StageContext:
        return cls(
            session_id=data["session_id"],
            quiz_id=data["quiz_id"],
            stage=StageDefinition.from_transport_dict(data["stage"]),
            server_now=iso_to_datetime(data["server_now"]),
            players=[
                PlayerIdentity.from_transport_dict(player)
                for player in data.get("players", [])
            ],
            scoreboard_snapshot=data.get("scoreboard_snapshot"),
            plugin_state_in=data.get("plugin_state_in"),
            transport_hints=data.get("transport_hints"),
            session_flags=data.get("session_flags"),
        )


@dataclass
class PlayerEvent:
    event_id: str
    session_id: str
    stage_id: str
    stage_index: int
    player_id: str
    type: str
    server_received_at: datetime
    payload: dict[str, Any]
    client_sent_at: datetime | None = None
    seq: int | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.event_id, "event_id")
        _require_non_empty_str(self.session_id, "session_id")
        _require_non_empty_str(self.stage_id, "stage_id")
        _require_int(self.stage_index, "stage_index")
        _require_non_empty_str(self.player_id, "player_id")
        _require_non_empty_str(self.type, "type")
        self.server_received_at = _normalize_datetime(
            self.server_received_at, "server_received_at"
        )
        _ensure_json_dict(self.payload, "payload")
        if self.client_sent_at is not None:
            self.client_sent_at = _normalize_datetime(
                self.client_sent_at, "client_sent_at"
            )
        if self.seq is not None:
            _require_int(self.seq, "seq")
        if self.correlation_id is not None:
            _require_non_empty_str(self.correlation_id, "correlation_id")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "event_id": self.event_id,
            "session_id": self.session_id,
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "player_id": self.player_id,
            "type": self.type,
            "server_received_at": datetime_to_iso(self.server_received_at),
            "payload": self.payload,
        }
        if self.client_sent_at is not None:
            data["client_sent_at"] = datetime_to_iso(self.client_sent_at)
        _optional_field(data, "seq", self.seq)
        _optional_field(data, "correlation_id", self.correlation_id)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> PlayerEvent:
        client_sent_at = data.get("client_sent_at")
        return cls(
            event_id=data["event_id"],
            session_id=data["session_id"],
            stage_id=data["stage_id"],
            stage_index=data["stage_index"],
            player_id=data["player_id"],
            type=data["type"],
            server_received_at=iso_to_datetime(data["server_received_at"]),
            payload=data["payload"],
            client_sent_at=(
                iso_to_datetime(client_sent_at) if client_sent_at else None
            ),
            seq=data.get("seq"),
            correlation_id=data.get("correlation_id"),
        )


@dataclass
class StageTrace:
    session_id: str
    stage_id: str
    stage_index: int
    started_at: datetime
    events: list[PlayerEvent] = field(default_factory=list)
    ended_at: datetime | None = None
    engine_events: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.session_id, "session_id")
        _require_non_empty_str(self.stage_id, "stage_id")
        _require_int(self.stage_index, "stage_index")
        self.started_at = _normalize_datetime(self.started_at, "started_at")
        if self.ended_at is not None:
            self.ended_at = _normalize_datetime(self.ended_at, "ended_at")
        if not isinstance(self.events, list):
            raise ValueError("events must be a list.")
        for event in self.events:
            if not isinstance(event, PlayerEvent):
                raise ValueError("events must contain PlayerEvent objects.")
            if event.session_id != self.session_id:
                raise ValueError("event session_id mismatch in StageTrace.")
            if event.stage_id != self.stage_id:
                raise ValueError("event stage_id mismatch in StageTrace.")
            if event.stage_index != self.stage_index:
                raise ValueError("event stage_index mismatch in StageTrace.")
        if self.engine_events is not None:
            if not isinstance(self.engine_events, list):
                raise ValueError("engine_events must be a list.")
            for entry in self.engine_events:
                _ensure_json_dict(entry, "engine_events entry")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "session_id": self.session_id,
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "started_at": datetime_to_iso(self.started_at),
            "events": [event.to_transport_dict() for event in self.events],
        }
        if self.ended_at is not None:
            data["ended_at"] = datetime_to_iso(self.ended_at)
        _optional_field(data, "engine_events", self.engine_events)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> StageTrace:
        ended_at = data.get("ended_at")
        return cls(
            session_id=data["session_id"],
            stage_id=data["stage_id"],
            stage_index=data["stage_index"],
            started_at=iso_to_datetime(data["started_at"]),
            events=[
                PlayerEvent.from_transport_dict(event)
                for event in data.get("events", [])
            ],
            ended_at=iso_to_datetime(ended_at) if ended_at else None,
            engine_events=data.get("engine_events"),
        )


@dataclass
class PluginFrame:
    session_id: str
    stage_id: str
    stage_index: int
    plugin_id: str
    audience: str
    frame_type: str
    payload: dict[str, Any]
    sent_at: datetime
    seq: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.session_id, "session_id")
        _require_non_empty_str(self.stage_id, "stage_id")
        _require_int(self.stage_index, "stage_index")
        _require_non_empty_str(self.plugin_id, "plugin_id")
        _require_non_empty_str(self.audience, "audience")
        _require_non_empty_str(self.frame_type, "frame_type")
        _ensure_json_dict(self.payload, "payload")
        self.sent_at = _normalize_datetime(self.sent_at, "sent_at")
        if self.seq is not None:
            _require_int(self.seq, "seq")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "session_id": self.session_id,
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "plugin_id": self.plugin_id,
            "audience": self.audience,
            "frame_type": self.frame_type,
            "payload": self.payload,
            "sent_at": datetime_to_iso(self.sent_at),
        }
        _optional_field(data, "seq", self.seq)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> PluginFrame:
        return cls(
            session_id=data["session_id"],
            stage_id=data["stage_id"],
            stage_index=data["stage_index"],
            plugin_id=data["plugin_id"],
            audience=data["audience"],
            frame_type=data["frame_type"],
            payload=data["payload"],
            sent_at=iso_to_datetime(data["sent_at"]),
            seq=data.get("seq"),
        )


@dataclass
class ScoreDelta:
    player_id: str
    delta_score: float
    meta: dict[str, Any] | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.player_id, "player_id")
        if isinstance(self.delta_score, bool) or not isinstance(
            self.delta_score, (int, float)
        ):
            raise ValueError("delta_score must be a number.")
        self.delta_score = float(self.delta_score)
        if not isfinite(self.delta_score):
            raise ValueError("delta_score must be finite.")
        if self.meta is not None:
            _ensure_json_dict(self.meta, "meta")
        if self.reason is not None and not isinstance(self.reason, str):
            raise ValueError("reason must be a string or None.")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "player_id": self.player_id,
            "delta_score": self.delta_score,
        }
        _optional_field(data, "meta", self.meta)
        _optional_field(data, "reason", self.reason)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> ScoreDelta:
        return cls(
            player_id=data["player_id"],
            delta_score=data["delta_score"],
            meta=data.get("meta"),
            reason=data.get("reason"),
        )


@dataclass
class GradeDelta:
    player_id: str
    value: float
    max_value: float | None = None
    scale: str | None = None
    meta: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.player_id, "player_id")
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("value must be a number.")
        self.value = float(self.value)
        if self.max_value is not None:
            if isinstance(self.max_value, bool) or not isinstance(
                self.max_value, (int, float)
            ):
                raise ValueError("max_value must be a number.")
            self.max_value = float(self.max_value)
            if self.max_value <= 0:
                raise ValueError("max_value must be > 0.")
        if self.scale is not None and not isinstance(self.scale, str):
            raise ValueError("scale must be a string or None.")
        if self.meta is not None:
            _ensure_json_dict(self.meta, "meta")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "player_id": self.player_id,
            "value": self.value,
        }
        _optional_field(data, "max_value", self.max_value)
        _optional_field(data, "scale", self.scale)
        _optional_field(data, "meta", self.meta)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> GradeDelta:
        return cls(
            player_id=data["player_id"],
            value=data["value"],
            max_value=data.get("max_value"),
            scale=data.get("scale"),
            meta=data.get("meta"),
        )


@dataclass
class StageOutcome:
    session_id: str
    stage_id: str
    stage_index: int
    plugin_id: str
    completed_at: datetime
    score_deltas: list[ScoreDelta] | None = None
    grade_deltas: list[GradeDelta] | None = None
    plugin_state_out: dict[str, Any] | None = None
    render_summary: dict[str, Any] | None = None
    attachments: dict[str, Any] | None = None
    next_hint: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_str(self.session_id, "session_id")
        _require_non_empty_str(self.stage_id, "stage_id")
        _require_int(self.stage_index, "stage_index")
        _require_non_empty_str(self.plugin_id, "plugin_id")
        self.completed_at = _normalize_datetime(self.completed_at, "completed_at")
        if self.score_deltas is not None:
            if not isinstance(self.score_deltas, list):
                raise ValueError("score_deltas must be a list.")
            for delta in self.score_deltas:
                if not isinstance(delta, ScoreDelta):
                    raise ValueError("score_deltas must contain ScoreDelta objects.")
        if self.grade_deltas is not None:
            if not isinstance(self.grade_deltas, list):
                raise ValueError("grade_deltas must be a list.")
            for delta in self.grade_deltas:
                if not isinstance(delta, GradeDelta):
                    raise ValueError("grade_deltas must contain GradeDelta objects.")
        if self.plugin_state_out is not None:
            _ensure_json_dict(self.plugin_state_out, "plugin_state_out")
        if self.render_summary is not None:
            _ensure_json_dict(self.render_summary, "render_summary")
        if self.attachments is not None:
            _ensure_json_dict(self.attachments, "attachments")
        if self.next_hint is not None:
            _ensure_json_dict(self.next_hint, "next_hint")

    def to_transport_dict(self) -> dict[str, Any]:
        data = {
            "session_id": self.session_id,
            "stage_id": self.stage_id,
            "stage_index": self.stage_index,
            "plugin_id": self.plugin_id,
            "completed_at": datetime_to_iso(self.completed_at),
        }
        if self.score_deltas is not None:
            data["score_deltas"] = [
                delta.to_transport_dict() for delta in self.score_deltas
            ]
        if self.grade_deltas is not None:
            data["grade_deltas"] = [
                delta.to_transport_dict() for delta in self.grade_deltas
            ]
        _optional_field(data, "plugin_state_out", self.plugin_state_out)
        _optional_field(data, "render_summary", self.render_summary)
        _optional_field(data, "attachments", self.attachments)
        _optional_field(data, "next_hint", self.next_hint)
        return data

    @classmethod
    def from_transport_dict(cls, data: dict[str, Any]) -> StageOutcome:
        score_deltas = data.get("score_deltas")
        grade_deltas = data.get("grade_deltas")
        return cls(
            session_id=data["session_id"],
            stage_id=data["stage_id"],
            stage_index=data["stage_index"],
            plugin_id=data["plugin_id"],
            completed_at=iso_to_datetime(data["completed_at"]),
            score_deltas=(
                [ScoreDelta.from_transport_dict(delta) for delta in score_deltas]
                if score_deltas is not None
                else None
            ),
            grade_deltas=(
                [GradeDelta.from_transport_dict(delta) for delta in grade_deltas]
                if grade_deltas is not None
                else None
            ),
            plugin_state_out=data.get("plugin_state_out"),
            render_summary=data.get("render_summary"),
            attachments=data.get("attachments"),
            next_hint=data.get("next_hint"),
        )
