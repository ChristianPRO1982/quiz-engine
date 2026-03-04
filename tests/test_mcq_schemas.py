"""Tests for MCQ plugin schema validation."""

from __future__ import annotations

import pytest

from quiz_engine.plugins.mcq.config import load_mcq_config
from quiz_engine.plugins.mcq.schemas import validate_mcq_plugin_spec


def _base_oneclick_spec() -> dict:
    return {
        "schema_version": "v1",
        "type": "quiz",
        "plugin": "mcq",
        "title": "Math",
        "prompt": "2 + 2 = ?",
        "mode": "oneclick",
        "time_limit_s": 30,
        "points": 1000,
        "examination": False,
        "choices": [
            {"id": "a", "label": "3", "is_correct": False},
            {"id": "b", "label": "4", "is_correct": True},
        ],
    }


def test_validate_mcq_plugin_spec_accepts_minimal_valid_payload() -> None:
    config = load_mcq_config()
    validated = validate_mcq_plugin_spec(_base_oneclick_spec(), config=config)

    assert validated["plugin"] == "mcq"
    assert validated["mode"] == "oneclick"
    assert validated["time_limit_s"] == 30
    assert len(validated["choices"]) == 2


def test_validate_mcq_plugin_spec_accepts_content_wrapper_markdown() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec.pop("title")
    spec.pop("prompt")
    spec["content"] = {
        "title": "Capitales",
        "body": "Quelle est la capitale de la France ?",
        "body_format": "markdown",
    }

    validated = validate_mcq_plugin_spec(spec, config=config)

    assert validated["title"] == "Capitales"
    assert validated["prompt"] == "Quelle est la capitale de la France ?"
    assert validated["body_format"] == "markdown"
    assert validated["content"]["body_format"] == "markdown"


def test_validate_mcq_plugin_spec_rejects_disabled_mode() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec["mode"] = "unknown_mode"

    with pytest.raises(ValueError):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_requires_weight_for_multianswer() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec["mode"] = "multianswer"
    spec["choices"] = [
        {"id": "a", "label": "A", "weight": 1},
        {"id": "b", "label": "B", "is_correct": False},
    ]

    with pytest.raises(ValueError):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_out_of_range_points() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec["points"] = 1

    with pytest.raises(ValueError):
        validate_mcq_plugin_spec(spec, config=config)
