"""Tests for MCQ config parsing and validation branches."""

from __future__ import annotations

from pathlib import Path

import pytest

from quiz_engine.plugins.mcq.config import (
    _parse_int_csv,
    _parse_str_csv,
    _validate_ratio,
    load_mcq_config,
)


def _write_ini(path: Path, *, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


def _valid_ini() -> str:
    return """
[mcq]
default_time_limit_s = 30
allowed_time_limits_s = 0,15,30
default_points = 1000
min_points = 10
max_points = 2000
default_player_choice_view = compact
allow_player_toggle_choice_view = true

[mcq.modes]
enabled_modes = oneclick,multianswer

[mcq.bots]
min_bots = 0
bots_vote_early_ratio = 0.8
early_time_window_ratio = 0.2
bots_good_answer_ratio_nice = 0.8
bots_good_answer_ratio_evil = 0.2
""".strip()


def test_load_mcq_config_accepts_valid_ini(tmp_path: Path) -> None:
    path = _write_ini(tmp_path / "mcq.ini", body=_valid_ini())
    config = load_mcq_config(path)

    assert config.default_time_limit_s == 30
    assert config.allowed_time_limits_s == (0, 15, 30)
    assert config.enabled_modes == ("oneclick", "multianswer")


def test_load_mcq_config_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not found"):
        load_mcq_config(tmp_path / "missing.ini")


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("mcq", "missing section \\[mcq\\]"),
        ("mcq.modes", "missing section \\[mcq.modes\\]"),
        ("mcq.bots", "missing section \\[mcq.bots\\]"),
    ],
)
def test_load_mcq_config_rejects_missing_sections(
    tmp_path: Path, section: str, message: str
) -> None:
    content = _valid_ini().splitlines()
    marker = f"[{section}]"
    start = content.index(marker)
    end = next(
        (idx for idx in range(start + 1, len(content)) if content[idx].startswith("[")),
        len(content),
    )
    stripped = "\n".join(
        line for idx, line in enumerate(content) if idx < start or idx >= end
    )
    path = _write_ini(tmp_path / "mcq.ini", body=stripped)

    with pytest.raises(ValueError, match=message):
        load_mcq_config(path)


@pytest.mark.parametrize(
    ("needle", "replacement", "message"),
    [
        (
            "min_bots = 0",
            "min_bots = -1",
            "mcq.bots.min_bots must be >= 0.",
        ),
        (
            "default_time_limit_s = 30",
            "default_time_limit_s = 31",
            "must be included in mcq.allowed_time_limits_s",
        ),
        (
            "min_points = 10",
            "min_points = -1",
            "mcq.min_points must be >= 0.",
        ),
        (
            "min_points = 10",
            "min_points = 5000",
            "mcq.min_points must be <= mcq.max_points.",
        ),
        (
            "default_points = 1000",
            "default_points = 1",
            "mcq.default_points must be within",
        ),
        (
            "default_player_choice_view = compact",
            "default_player_choice_view = full",
            "must be 'compact' or 'label'",
        ),
        (
            "bots_good_answer_ratio_evil = 0.2",
            "bots_good_answer_ratio_evil = 1.2",
            "must be within \\[0, 1\\]",
        ),
    ],
)
def test_load_mcq_config_rejects_invalid_values(
    tmp_path: Path, needle: str, replacement: str, message: str
) -> None:
    path = _write_ini(
        tmp_path / "mcq.ini",
        body=_valid_ini().replace(needle, replacement),
    )
    with pytest.raises(ValueError, match=message):
        load_mcq_config(path)


def test_parse_int_and_str_csv_helpers_cover_edge_cases() -> None:
    assert _parse_int_csv(" 1, ,2 ", field_name="f") == (1, 2)
    with pytest.raises(ValueError, match="non-integer"):
        _parse_int_csv("1,x", field_name="f")
    with pytest.raises(ValueError, match="at least one value"):
        _parse_int_csv(" , ", field_name="f")

    assert _parse_str_csv(" one, ,two ", field_name="f") == ("one", "two")
    with pytest.raises(ValueError, match="at least one value"):
        _parse_str_csv(" , ", field_name="f")


def test_validate_ratio_rejects_out_of_bounds() -> None:
    _validate_ratio(0.0, "f")
    _validate_ratio(1.0, "f")
    with pytest.raises(ValueError, match="within \\[0, 1\\]"):
        _validate_ratio(-0.1, "f")
