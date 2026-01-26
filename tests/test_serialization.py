"""Tests for contract serialization helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from quiz_engine.contracts.runtime_models import ScoreDelta
from quiz_engine.contracts.serialization import (
    datetime_to_iso,
    dump_model,
    ensure_json_like,
    is_json_like,
    iso_to_datetime,
    load_model,
)


def test_is_json_like_accepts_nested_values() -> None:
    payload = {"a": [1, "b", None, True, {"c": 1.5}]}
    assert is_json_like(payload)


def test_is_json_like_rejects_non_string_keys() -> None:
    assert not is_json_like({1: "nope"})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_is_json_like_rejects_non_finite(value: float) -> None:
    assert not is_json_like({"bad": value})


def test_ensure_json_like_raises_for_invalid() -> None:
    with pytest.raises(ValueError):
        ensure_json_like({"bad": object()}, "payload")


def test_datetime_to_iso_outputs_utc_z() -> None:
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert datetime_to_iso(dt) == "2024-01-01T12:00:00Z"


def test_datetime_to_iso_converts_offset() -> None:
    dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    assert datetime_to_iso(dt) == "2024-01-01T10:00:00Z"


def test_iso_to_datetime_parses_z() -> None:
    dt = iso_to_datetime("2024-01-01T12:00:00Z")
    assert dt.tzinfo == UTC
    assert dt == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_dump_load_model_roundtrip() -> None:
    delta = ScoreDelta(player_id="player-1", delta_score=5.0)
    data = dump_model(delta)
    restored = load_model(ScoreDelta, data)
    assert restored == delta
