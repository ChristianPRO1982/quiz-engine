"""Edge-case tests for serialization helpers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quiz_engine.contracts.serialization import (
    datetime_to_iso,
    dump_model,
    iso_to_datetime,
    load_model,
)


def test_datetime_to_iso_rejects_non_datetime() -> None:
    with pytest.raises(ValueError):
        datetime_to_iso("2024-01-01T00:00:00Z")  # type: ignore[arg-type]


def test_datetime_to_iso_accepts_naive_datetime() -> None:
    value = datetime(2024, 1, 1, 12, 0, 0)
    assert datetime_to_iso(value) == "2024-01-01T12:00:00Z"


def test_iso_to_datetime_rejects_non_string() -> None:
    with pytest.raises(ValueError):
        iso_to_datetime(123)  # type: ignore[arg-type]


def test_iso_to_datetime_accepts_naive_iso_and_sets_utc() -> None:
    parsed = iso_to_datetime("2024-01-01T12:00:00")
    assert parsed == datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


class _NoDump:
    pass


def test_dump_model_requires_to_transport_dict() -> None:
    with pytest.raises(TypeError):
        dump_model(_NoDump())


class _BadDump:
    def to_transport_dict(self):  # noqa: ANN201
        return {"bad": object()}


def test_dump_model_rejects_non_json_like_transport_payload() -> None:
    with pytest.raises(ValueError):
        dump_model(_BadDump())


class _NoLoad:
    pass


def test_load_model_requires_from_transport_dict() -> None:
    with pytest.raises(TypeError):
        load_model(_NoLoad, {})
