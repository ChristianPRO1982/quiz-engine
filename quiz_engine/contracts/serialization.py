"""Serialization helpers for runtime contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from math import isfinite
from typing import Any


def is_json_like(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (str, int)):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, list):
        return all(is_json_like(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and is_json_like(item) for key, item in value.items()
        )
    return False


def ensure_json_like(value: Any, path: str) -> None:
    if not is_json_like(value):
        raise ValueError(f"{path} must be JSON-like.")


def datetime_to_iso(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise ValueError("value must be a datetime.")
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)
    return value.isoformat().replace("+00:00", "Z")


def iso_to_datetime(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("value must be a string.")
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def dump_model(model: Any) -> dict[str, Any]:
    if not hasattr(model, "to_transport_dict"):
        raise TypeError("model must implement to_transport_dict().")
    data = model.to_transport_dict()
    ensure_json_like(data, "model")
    return data


def load_model[T](cls: type[T], data: dict[str, Any]) -> T:
    if not hasattr(cls, "from_transport_dict"):
        raise TypeError("class must implement from_transport_dict().")
    return cls.from_transport_dict(data)
