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
        "ws_client_join.json",
        "ws_server_lobby_snapshot.json",
    )

    for filename in ws_files:
        data = load_json(FIXTURES_DIR / filename)

        for field in ("v", "type", "session_code", "payload"):
            assert field in data, f"{filename} missing field '{field}'"


def test_plugin_manifest_has_minimal_required_fields():
    data = load_json(FIXTURES_DIR / "plugin_manifest_minimal.json")

    for field in (
        "schema_version",
        "plugin_id",
        "plugin_version",
        "engine_version_compatibility",
        "capabilities",
    ):
        assert field in data, f"plugin_manifest missing field '{field}'"


def test_quiz_minimal_has_minimal_required_fields():
    data = load_json(FIXTURES_DIR / "quiz_minimal.json")

    for field in (
        "schema_version",
        "engine_version",
        "quiz_id",
        "nodes",
        "edges",
    ):
        assert field in data, f"quiz_minimal missing field '{field}'"

    assert isinstance(data["nodes"], list)
    assert len(data["nodes"]) >= 1


def test_question_result_minimal_has_minimal_required_fields():
    data = load_json(FIXTURES_DIR / "question_result_minimal.json")

    for field in (
        "schema_version",
        "question_id",
        "plugin_id",
        "plugin_version",
        "timestamp",
        "player_results",
    ):
        assert field in data, f"question_result missing field '{field}'"

    assert isinstance(data["player_results"], list)
