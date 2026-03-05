"""Schema helpers for the built-in MCQ plugin."""

from __future__ import annotations

from typing import Any

from quiz_engine.plugins.mcq.config import MCQConfig

_ALLOWED_ROOT_KEYS = {
    "schema_version",
    "type",
    "plugin",
    "title",
    "prompt",
    "body_format",
    "content",
    "mode",
    "time_limit_s",
    "points",
    "examination",
    "choices",
}
_ALLOWED_CONTENT_KEYS = {"title", "body", "body_format"}
_ALLOWED_CHOICE_KEYS = {"id", "label", "is_correct", "weight"}


def validate_mcq_plugin_spec(
    plugin_spec: dict[str, Any],
    config: MCQConfig,
    *,
    stage_title: str | None = None,
) -> dict[str, Any]:
    if not isinstance(plugin_spec, dict):
        raise ValueError("mcq plugin_spec must be an object.")

    _require_only_known_keys(
        plugin_spec, allowed=_ALLOWED_ROOT_KEYS, field_name="mcq plugin_spec"
    )
    _validate_schema_version(plugin_spec.get("schema_version"))
    _validate_type(plugin_spec.get("type"))
    _validate_plugin(plugin_spec.get("plugin"))

    mode = _require_text(plugin_spec.get("mode"), "mcq mode")
    if mode not in config.enabled_modes:
        raise ValueError(
            "mcq mode "
            f"{mode!r} is disabled. "
            f"Enabled modes: {', '.join(config.enabled_modes)}."
        )

    source = plugin_spec
    raw_content = plugin_spec.get("content")
    if raw_content is not None:
        if not isinstance(raw_content, dict):
            raise ValueError("mcq content must be an object when provided.")
        _require_only_known_keys(
            raw_content, allowed=_ALLOWED_CONTENT_KEYS, field_name="mcq content"
        )
        source = raw_content
    source_is_content = source is not plugin_spec

    title_raw = source.get("title")
    if title_raw is None and source_is_content:
        title_raw = plugin_spec.get("title")
    title = _normalize_optional_text(title_raw, "mcq title")
    if title is None:
        title = _normalize_optional_text(stage_title, "mcq stage_title")
    if title is None:
        raise ValueError("mcq title is required.")

    prompt_raw = source.get("body") if source_is_content else source.get("prompt")
    if prompt_raw is None and source_is_content:
        prompt_raw = plugin_spec.get("prompt")
    prompt = _require_text(prompt_raw, "mcq prompt")
    body_format = _normalize_body_format(source.get("body_format"))

    time_limit_s = plugin_spec.get("time_limit_s", config.default_time_limit_s)
    time_limit_s = _require_int(time_limit_s, "mcq time_limit_s")
    if time_limit_s not in config.allowed_time_limits_s:
        allowed = ", ".join(str(item) for item in config.allowed_time_limits_s)
        raise ValueError(f"mcq time_limit_s must be one of: {allowed}.")

    points = plugin_spec.get("points", config.default_points)
    points = _require_int(points, "mcq points")
    if points < config.min_points or points > config.max_points:
        raise ValueError(
            f"mcq points must be within [{config.min_points}, {config.max_points}]."
        )

    raw_examination = plugin_spec.get("examination", False)
    if not isinstance(raw_examination, bool):
        raise ValueError("mcq examination must be a boolean.")
    examination = raw_examination

    choices = _normalize_choices(plugin_spec.get("choices"), mode=mode, config=config)

    payload: dict[str, Any] = {
        "schema_version": "v1",
        "type": "quiz",
        "plugin": "mcq",
        "title": title,
        "prompt": prompt,
        "body_format": body_format,
        "content": {
            "title": title,
            "body": prompt,
            "body_format": body_format,
        },
        "mode": mode,
        "time_limit_s": time_limit_s,
        "points": points,
        "examination": examination,
        "choices": choices,
    }
    return payload


def build_mcq_frame_payload(
    plugin_spec: dict[str, Any],
    *,
    config: MCQConfig,
    stage_title: str | None = None,
    player_count: int,
    phase: str = "ANSWERING",
    prestart_countdown_s: int | None = None,
) -> dict[str, Any]:
    validated = validate_mcq_plugin_spec(
        plugin_spec, config=config, stage_title=stage_title
    )
    return {
        "plugin": "mcq",
        "phase": phase,
        "title": validated["title"],
        "prompt": validated["prompt"],
        "mode": validated["mode"],
        "time_limit_s": validated["time_limit_s"],
        "points": validated["points"],
        "examination": validated["examination"],
        "player_count": player_count,
        "prestart_countdown_s": prestart_countdown_s,
        "player_choice_view": {
            "default": config.default_player_choice_view,
            "allow_toggle": config.allow_player_toggle_choice_view,
        },
        "choice_grid_columns": {
            "smartphone": config.choice_columns_smartphone,
            "tablet": config.choice_columns_tablet,
            "desktop": config.choice_columns_desktop,
        },
        "choices": [
            {
                "id": choice["id"],
                "index": index,
                "label": choice["label"],
            }
            for index, choice in enumerate(validated["choices"])
        ],
    }


def extract_correct_choice_ids(plugin_spec: dict[str, Any]) -> set[str]:
    mode = plugin_spec["mode"]
    if mode == "multianswer":
        return {
            choice["id"]
            for choice in plugin_spec["choices"]
            if choice.get("weight", 0) > 0
        }
    return {
        choice["id"] for choice in plugin_spec["choices"] if choice.get("is_correct")
    }


def extract_choice_weights(plugin_spec: dict[str, Any]) -> dict[str, int]:
    mode = plugin_spec["mode"]
    if mode != "multianswer":
        return {}
    return {choice["id"]: int(choice["weight"]) for choice in plugin_spec["choices"]}


def _normalize_choices(
    raw_value: Any, *, mode: str, config: MCQConfig
) -> list[dict[str, Any]]:
    if not isinstance(raw_value, list):
        raise ValueError("mcq choices must be a list.")
    if len(raw_value) < config.min_choices or len(raw_value) > config.max_choices:
        raise ValueError(
            "mcq choices count must be within "
            f"[{config.min_choices}, {config.max_choices}]."
        )

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_choice in enumerate(raw_value):
        if not isinstance(raw_choice, dict):
            raise ValueError(f"mcq choice #{index + 1} must be an object.")
        _require_only_known_keys(
            raw_choice,
            allowed=_ALLOWED_CHOICE_KEYS,
            field_name=f"mcq choice #{index + 1}",
        )

        choice_id = _require_text(raw_choice.get("id"), f"mcq choice #{index + 1}.id")
        if choice_id in seen_ids:
            raise ValueError(f"mcq choice ids must be unique: {choice_id!r}")
        seen_ids.add(choice_id)

        label = _require_text(raw_choice.get("label"), f"mcq choice #{index + 1}.label")
        choice: dict[str, Any] = {"id": choice_id, "label": label}

        if mode == "multianswer":
            if "is_correct" in raw_choice:
                raise ValueError("mcq multianswer choices must not declare is_correct.")
            weight = _require_int(raw_choice.get("weight"), "mcq choice weight")
            if weight < -config.max_points or weight > config.max_points:
                raise ValueError(
                    "mcq choice weight must be within "
                    f"[-{config.max_points}, {config.max_points}]."
                )
            choice["weight"] = weight
        else:
            if "weight" in raw_choice:
                raise ValueError(f"mcq mode {mode!r} choices must not declare weight.")
            is_correct = raw_choice.get("is_correct")
            if not isinstance(is_correct, bool):
                raise ValueError("mcq choices must declare boolean is_correct.")
            choice["is_correct"] = is_correct

        normalized.append(choice)

    if mode != "multianswer" and not any(choice["is_correct"] for choice in normalized):
        raise ValueError("mcq choices must include at least one correct answer.")

    return normalized


def _validate_schema_version(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError("mcq schema_version must be a string when provided.")
    normalized = value.strip().lower()
    if normalized not in {"v1"}:
        raise ValueError("mcq schema_version must be 'v1' when provided.")


def _validate_type(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError("mcq type must be a string when provided.")
    normalized = value.strip().lower()
    if normalized != "quiz":
        raise ValueError("mcq type must be 'quiz' when provided.")


def _validate_plugin(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise ValueError("mcq plugin must be a string when provided.")
    normalized = value.strip().lower()
    if normalized != "mcq":
        raise ValueError("mcq plugin must be 'mcq' when provided.")


def _normalize_body_format(value: Any) -> str:
    if value is None:
        return "markdown"
    if not isinstance(value, str):
        raise ValueError("mcq body_format must be a string when provided.")
    normalized = value.strip().lower()
    if normalized not in {"text", "markdown"}:
        raise ValueError("mcq body_format must be 'text' or 'markdown'.")
    return normalized


def _require_only_known_keys(
    source: dict[str, Any],
    *,
    allowed: set[str],
    field_name: str,
) -> None:
    unknown = sorted(set(source) - allowed)
    if unknown:
        raise ValueError(f"{field_name} contains unknown key(s): {', '.join(unknown)}")


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")
    text = value.strip()
    return text or None


def _require_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer.")
    return value
