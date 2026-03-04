"""Tests for MCQ plugin schema validation."""

from __future__ import annotations

import pytest

from quiz_engine.plugins.mcq.config import load_mcq_config
from quiz_engine.plugins.mcq.schemas import (
    build_mcq_frame_payload,
    extract_choice_weights,
    extract_correct_choice_ids,
    validate_mcq_plugin_spec,
)


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


def test_validate_mcq_plugin_spec_uses_stage_title_when_title_missing() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec.pop("title")
    spec["content"] = {
        "body": "Prompt only",
    }

    validated = validate_mcq_plugin_spec(
        spec, config=config, stage_title="Question title"
    )

    assert validated["title"] == "Question title"
    assert validated["prompt"] == "Prompt only"


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


def test_validate_mcq_plugin_spec_rejects_non_dict_spec() -> None:
    config = load_mcq_config()
    with pytest.raises(ValueError, match="must be an object"):
        validate_mcq_plugin_spec("bad", config=config)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("schema_version", 1, "schema_version must be a string"),
        ("schema_version", "v2", "schema_version must be 'v1'"),
        ("type", 1, "type must be a string"),
        ("type", "slide", "type must be 'quiz'"),
        ("plugin", 1, "plugin must be a string"),
        ("plugin", "slide", "plugin must be 'mcq'"),
        ("body_format", 1, "body_format must be a string"),
        ("body_format", "html", "body_format must be 'text' or 'markdown'"),
    ],
)
def test_validate_mcq_plugin_spec_rejects_invalid_meta_fields(
    field: str, value: object, message: str
) -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec[field] = value
    with pytest.raises(ValueError, match=message):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_unknown_keys_in_root_and_content() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec["unknown"] = True
    with pytest.raises(ValueError, match="contains unknown key"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["content"] = {"body": "Q", "oops": 1}
    with pytest.raises(ValueError, match="contains unknown key"):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_invalid_content_and_examination_types() -> (
    None
):
    config = load_mcq_config()

    spec = _base_oneclick_spec()
    spec["content"] = "bad"
    with pytest.raises(ValueError, match="content must be an object"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["examination"] = "yes"
    with pytest.raises(ValueError, match="examination must be a boolean"):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_invalid_time_limit_and_int_fields() -> None:
    config = load_mcq_config()
    spec = _base_oneclick_spec()
    spec["time_limit_s"] = True
    with pytest.raises(ValueError, match="time_limit_s must be an integer"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["time_limit_s"] = 999
    with pytest.raises(ValueError, match="must be one of"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["points"] = False
    with pytest.raises(ValueError, match="points must be an integer"):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_invalid_choices_variants() -> None:
    config = load_mcq_config()

    spec = _base_oneclick_spec()
    spec["choices"] = "bad"
    with pytest.raises(ValueError, match="choices must be a list"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [{"id": "a", "label": "A", "is_correct": True}]
    with pytest.raises(ValueError, match="at least 2 choices"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [{"id": "a", "label": "A", "is_correct": True}, "bad"]
    with pytest.raises(ValueError, match="must be an object"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [
        {"id": "a", "label": "A", "is_correct": True, "x": 1},
        {"id": "b", "label": "B", "is_correct": False},
    ]
    with pytest.raises(ValueError, match="contains unknown key"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [
        {"id": "a", "label": "A", "is_correct": True},
        {"id": "a", "label": "B", "is_correct": False},
    ]
    with pytest.raises(ValueError, match="must be unique"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [
        {"id": "a", "label": "A", "is_correct": False},
        {"id": "b", "label": "B", "is_correct": False},
    ]
    with pytest.raises(ValueError, match="at least one correct"):
        validate_mcq_plugin_spec(spec, config=config)


def test_validate_mcq_plugin_spec_rejects_mode_specific_choice_fields() -> None:
    config = load_mcq_config()

    spec = _base_oneclick_spec()
    spec["choices"] = [
        {"id": "a", "label": "A", "is_correct": True, "weight": 1},
        {"id": "b", "label": "B", "is_correct": False},
    ]
    with pytest.raises(ValueError, match="must not declare weight"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["choices"] = [
        {"id": "a", "label": "A", "is_correct": "yes"},
        {"id": "b", "label": "B", "is_correct": False},
    ]
    with pytest.raises(ValueError, match="boolean is_correct"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["mode"] = "multianswer"
    spec["choices"] = [
        {"id": "a", "label": "A", "weight": 1, "is_correct": True},
        {"id": "b", "label": "B", "weight": 0},
    ]
    with pytest.raises(ValueError, match="must not declare is_correct"):
        validate_mcq_plugin_spec(spec, config=config)

    spec = _base_oneclick_spec()
    spec["mode"] = "multianswer"
    spec["choices"] = [
        {"id": "a", "label": "A", "weight": True},
        {"id": "b", "label": "B", "weight": 0},
    ]
    with pytest.raises(ValueError, match="must be an integer"):
        validate_mcq_plugin_spec(spec, config=config)


def test_extract_helpers_and_build_payload_cover_remaining_branches() -> None:
    config = load_mcq_config()
    oneclick = validate_mcq_plugin_spec(_base_oneclick_spec(), config=config)
    assert extract_correct_choice_ids(oneclick) == {"b"}
    assert extract_choice_weights(oneclick) == {}

    multi = _base_oneclick_spec()
    multi["mode"] = "multianswer"
    multi["choices"] = [
        {"id": "a", "label": "A", "weight": 2},
        {"id": "b", "label": "B", "weight": -1},
    ]
    validated_multi = validate_mcq_plugin_spec(multi, config=config)
    assert extract_correct_choice_ids(validated_multi) == {"a"}
    assert extract_choice_weights(validated_multi) == {"a": 2, "b": -1}

    frame = build_mcq_frame_payload(
        _base_oneclick_spec(),
        config=config,
        stage_title=None,
        player_count=3,
    )
    assert frame["player_choice_view"] == {"default": "compact", "allow_toggle": True}
