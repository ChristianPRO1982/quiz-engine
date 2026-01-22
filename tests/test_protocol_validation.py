"""Protocol validation tests."""

import pytest

from quiz_engine.protocol import PROTOCOL_VERSION, ProtocolError, parse_event


def _base_event():
    return {
        "v": PROTOCOL_VERSION,
        "type": "leave_session",
        "session_code": "ABC123",
        "payload": {},
    }


def _assert_error(data, code):
    with pytest.raises(ProtocolError) as excinfo:
        parse_event(data)
    assert excinfo.value.code == code
    return excinfo.value


def test_parse_event_rejects_non_dict():
    _assert_error(["nope"], "invalid_envelope")


@pytest.mark.parametrize("missing_field", ["v", "type", "session_code", "payload"])
def test_parse_event_requires_fields(missing_field):
    data = _base_event()
    data.pop(missing_field)
    error = _assert_error(data, "invalid_envelope")
    expected_session = "" if missing_field == "session_code" else "ABC123"
    assert error.session_code == expected_session


def test_parse_event_rejects_bad_version():
    data = _base_event()
    data["v"] = "1"
    error = _assert_error(data, "invalid_version")
    assert error.details["expected"] == PROTOCOL_VERSION


def test_parse_event_rejects_unknown_event():
    data = _base_event()
    data["type"] = "unknown"
    error = _assert_error(data, "unknown_event")
    assert error.details["type"] == "unknown"


def test_parse_event_rejects_non_string_session_code():
    data = _base_event()
    data["session_code"] = 123
    _assert_error(data, "invalid_envelope")


def test_parse_event_rejects_non_object_payload():
    data = _base_event()
    data["payload"] = "nope"
    _assert_error(data, "invalid_envelope")


@pytest.mark.parametrize("payload", [{"nickname": 123}, {"nickname": "  "}])
def test_join_session_requires_valid_nickname(payload):
    data = _base_event()
    data["type"] = "join_session"
    data["payload"] = payload
    _assert_error(data, "invalid_payload")


def test_host_approve_requires_request_id():
    data = _base_event()
    data["type"] = "host_approve_join"
    _assert_error(data, "invalid_payload")


def test_host_kick_requires_player_id():
    data = _base_event()
    data["type"] = "host_kick"
    _assert_error(data, "invalid_payload")


def test_payload_must_be_empty_for_leave():
    data = _base_event()
    data["payload"] = {"extra": "nope"}
    _assert_error(data, "invalid_payload")
