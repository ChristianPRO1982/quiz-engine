"""Configuration loader for the built-in MCQ plugin."""

from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

MCQ_CONFIG_FILENAME = "mcq.ini"


@dataclass(frozen=True)
class MCQConfig:
    default_time_limit_s: int
    allowed_time_limits_s: tuple[int, ...]
    default_points: int
    min_points: int
    max_points: int
    default_choices_count: int
    min_choices: int
    max_choices: int
    choice_columns_smartphone: int
    choice_columns_tablet: int
    choice_columns_desktop: int
    default_player_choice_view: str
    allow_player_toggle_choice_view: bool
    enabled_modes: tuple[str, ...]
    min_bots: int
    bots_vote_early_ratio: float
    early_time_window_ratio: float
    bots_good_answer_ratio_nice: float
    bots_good_answer_ratio_evil: float


def load_mcq_config(config_path: Path | None = None) -> MCQConfig:
    path = config_path or (Path(__file__).resolve().parent / MCQ_CONFIG_FILENAME)
    parser = ConfigParser()
    read_paths = parser.read(path, encoding="utf-8")
    if not read_paths:
        raise ValueError(f"MCQ config file not found: {path}")

    if not parser.has_section("mcq"):
        raise ValueError("MCQ config is missing section [mcq].")
    if not parser.has_section("mcq.modes"):
        raise ValueError("MCQ config is missing section [mcq.modes].")
    if not parser.has_section("mcq.bots"):
        raise ValueError("MCQ config is missing section [mcq.bots].")

    default_time_limit_s = parser.getint("mcq", "default_time_limit_s")
    allowed_time_limits_s = _parse_int_csv(
        parser.get("mcq", "allowed_time_limits_s"),
        field_name="mcq.allowed_time_limits_s",
    )
    default_points = parser.getint("mcq", "default_points")
    min_points = parser.getint("mcq", "min_points")
    max_points = parser.getint("mcq", "max_points")
    default_choices_count = parser.getint("mcq", "default_choices_count")
    min_choices = parser.getint("mcq", "min_choices")
    max_choices = parser.getint("mcq", "max_choices")
    choice_columns_smartphone = parser.getint("mcq", "choice_columns_smartphone")
    choice_columns_tablet = parser.getint("mcq", "choice_columns_tablet")
    choice_columns_desktop = parser.getint("mcq", "choice_columns_desktop")
    default_player_choice_view = parser.get("mcq", "default_player_choice_view").strip()
    allow_player_toggle_choice_view = parser.getboolean(
        "mcq", "allow_player_toggle_choice_view"
    )

    enabled_modes = _parse_str_csv(
        parser.get("mcq.modes", "enabled_modes"),
        field_name="mcq.modes.enabled_modes",
    )

    min_bots = parser.getint("mcq.bots", "min_bots")
    bots_vote_early_ratio = parser.getfloat("mcq.bots", "bots_vote_early_ratio")
    early_time_window_ratio = parser.getfloat("mcq.bots", "early_time_window_ratio")
    bots_good_answer_ratio_nice = parser.getfloat(
        "mcq.bots", "bots_good_answer_ratio_nice"
    )
    bots_good_answer_ratio_evil = parser.getfloat(
        "mcq.bots", "bots_good_answer_ratio_evil"
    )

    _validate_ratio(bots_vote_early_ratio, "mcq.bots.bots_vote_early_ratio")
    _validate_ratio(early_time_window_ratio, "mcq.bots.early_time_window_ratio")
    _validate_ratio(bots_good_answer_ratio_nice, "mcq.bots.bots_good_answer_ratio_nice")
    _validate_ratio(bots_good_answer_ratio_evil, "mcq.bots.bots_good_answer_ratio_evil")

    if min_bots < 0:
        raise ValueError("mcq.bots.min_bots must be >= 0.")
    if default_time_limit_s not in allowed_time_limits_s:
        raise ValueError(
            "mcq.default_time_limit_s must be included in mcq.allowed_time_limits_s."
        )
    if min_points < 0:
        raise ValueError("mcq.min_points must be >= 0.")
    if min_points > max_points:
        raise ValueError("mcq.min_points must be <= mcq.max_points.")
    if not (min_points <= default_points <= max_points):
        raise ValueError(
            "mcq.default_points must be within [mcq.min_points, mcq.max_points]."
        )
    if min_choices < 1:
        raise ValueError("mcq.min_choices must be >= 1.")
    if min_choices > max_choices:
        raise ValueError("mcq.min_choices must be <= mcq.max_choices.")
    if not (min_choices <= default_choices_count <= max_choices):
        raise ValueError(
            "mcq.default_choices_count must be within "
            "[mcq.min_choices, mcq.max_choices]."
        )
    if choice_columns_smartphone < 1:
        raise ValueError("mcq.choice_columns_smartphone must be >= 1.")
    if choice_columns_tablet < 1:
        raise ValueError("mcq.choice_columns_tablet must be >= 1.")
    if choice_columns_desktop < 1:
        raise ValueError("mcq.choice_columns_desktop must be >= 1.")
    if default_player_choice_view not in {"compact", "label"}:
        raise ValueError("mcq.default_player_choice_view must be 'compact' or 'label'.")

    return MCQConfig(
        default_time_limit_s=default_time_limit_s,
        allowed_time_limits_s=allowed_time_limits_s,
        default_points=default_points,
        min_points=min_points,
        max_points=max_points,
        default_choices_count=default_choices_count,
        min_choices=min_choices,
        max_choices=max_choices,
        choice_columns_smartphone=choice_columns_smartphone,
        choice_columns_tablet=choice_columns_tablet,
        choice_columns_desktop=choice_columns_desktop,
        default_player_choice_view=default_player_choice_view,
        allow_player_toggle_choice_view=allow_player_toggle_choice_view,
        enabled_modes=enabled_modes,
        min_bots=min_bots,
        bots_vote_early_ratio=bots_vote_early_ratio,
        early_time_window_ratio=early_time_window_ratio,
        bots_good_answer_ratio_nice=bots_good_answer_ratio_nice,
        bots_good_answer_ratio_evil=bots_good_answer_ratio_evil,
    )


def _parse_int_csv(raw: str, *, field_name: str) -> tuple[int, ...]:
    values: list[int] = []
    for token in raw.split(","):
        value = token.strip()
        if not value:
            continue
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError(
                f"{field_name} contains a non-integer value: {value!r}"
            ) from exc
        values.append(parsed)
    if not values:
        raise ValueError(f"{field_name} must contain at least one value.")
    return tuple(values)


def _parse_str_csv(raw: str, *, field_name: str) -> tuple[str, ...]:
    values = tuple(token.strip() for token in raw.split(",") if token.strip())
    if not values:
        raise ValueError(f"{field_name} must contain at least one value.")
    return values


def _validate_ratio(value: float, field_name: str) -> None:
    if value < 0 or value > 1:
        raise ValueError(f"{field_name} must be within [0, 1].")
