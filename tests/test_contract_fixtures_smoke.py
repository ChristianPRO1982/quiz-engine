"""
Smoke tests for contract fixtures.

Goal:
- ensure all contract JSON fixtures are valid
- ensure minimal required top-level fields exist
- prevent accidental format regressions
"""

import json
from pathlib import Path

FIXTURES_DIR = Path("tests/fixtures/contracts")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_all_contract_fixtures_are_valid_json():
    for path in FIXTURES_DIR.glob("*.json"):
        data = load_json(path)
        assert isinstance(data, dict), f"{path.name} must contain a JSON object"


def test_ws_fixtures_have_mandatory_envelope_fields():
    ws_files = (
        "ws_player_event.json",
        "ws_plugin_frame.json",
    )

    for filename in ws_files:
        data = load_json(FIXTURES_DIR / filename)

        for field in ("type", "payload"):
            assert field in data, f"{filename} missing field '{field}'"


def test_plugin_manifest_has_minimal_required_fields():
    data = load_json(FIXTURES_DIR / "plugin_manifest_minimal.json")

    for field in (
        "schema_version",
        "plugin_id",
        "plugin_version",
        "display_name",
    ):
        assert field in data, f"plugin_manifest missing field '{field}'"


def test_stage_outcome_minimal_has_required_fields():
    data = load_json(FIXTURES_DIR / "stage_outcome_minimal.json")

    for field in (
        "session_id",
        "stage_id",
        "stage_index",
        "plugin_id",
        "completed_at",
    ):
        assert field in data, f"stage_outcome missing field '{field}'"


def test_stage_trace_minimal_has_required_fields():
    data = load_json(FIXTURES_DIR / "stage_trace_minimal.json")

    for field in (
        "session_id",
        "stage_id",
        "stage_index",
        "started_at",
        "events",
    ):
        assert field in data, f"stage_trace missing field '{field}'"

    assert isinstance(data["events"], list)
