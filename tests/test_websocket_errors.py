"""WebSocket error handling tests."""

from quiz_engine.protocol import PROTOCOL_VERSION


def _event(event_type, session_code, payload=None):
    return {
        "v": PROTOCOL_VERSION,
        "type": event_type,
        "session_code": session_code,
        "payload": payload or {},
    }


def _collect_events(websocket, expected_types):
    seen = {}
    while expected_types - seen.keys():
        event = websocket.receive_json()
        if event["type"] in expected_types:
            seen[event["type"]] = event
    return seen


def test_invalid_session_on_connect(client):
    with client.websocket_connect("/ws?role=host&session_code=NOPE") as host_ws:
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_session"


def test_host_create_session_via_websocket(client):
    with client.websocket_connect("/ws?role=host") as host_ws:
        host_ws.send_json(_event("create_session", ""))
        events = _collect_events(
            host_ws, {"session_created", "session_status", "lobby_snapshot"}
        )
        assert events["session_created"]["payload"]["session_code"]


def test_host_rejects_player_event(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(_event("join_session", session_code, {"nickname": "Host"}))
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_role"


def test_host_event_with_invalid_session_code(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(_event("host_start", "NOPE"))
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_session"


def test_player_rejects_host_event(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=player&session_code={session_code}"
    ) as player_ws:
        _collect_events(player_ws, {"session_status"})
        player_ws.send_json(_event("host_start", session_code))
        error = _collect_events(player_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_role"


def test_player_join_invalid_session(client):
    with client.websocket_connect("/ws?role=player") as player_ws:
        player_ws.send_json(_event("join_session", "NOPE", {"nickname": "Ava"}))
        error = _collect_events(player_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_session"


def test_player_double_join_in_lobby(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=player&session_code={session_code}"
    ) as player_ws:
        _collect_events(player_ws, {"session_status"})
        player_ws.send_json(_event("join_session", session_code, {"nickname": "Mia"}))
        _collect_events(player_ws, {"player_joined", "lobby_snapshot"})

        player_ws.send_json(_event("join_session", session_code, {"nickname": "Mia"}))
        error = _collect_events(player_ws, {"error"})["error"]
        assert error["payload"]["code"] == "already_joined"


def test_join_pending_when_running(client):
    session_code = client.post("/api/sessions").json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(_event("host_start", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            _collect_events(player_ws, {"session_status"})
            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Nia"})
            )
            _collect_events(host_ws, {"join_requested"})

            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Nia"})
            )
            error = _collect_events(player_ws, {"error"})["error"]
            assert error["payload"]["code"] == "join_pending"


def test_leave_session_in_lobby(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            _collect_events(player_ws, {"session_status"})
            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Kai"})
            )
            _collect_events(host_ws, {"player_joined", "lobby_snapshot"})

            player_ws.send_json(_event("leave_session", session_code))
            events = _collect_events(host_ws, {"player_left", "lobby_snapshot"})
            assert events["player_left"]["payload"]["player_id"]


def test_leave_session_invalid_state(client):
    session_code = client.post("/api/sessions").json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(_event("host_start", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            _collect_events(player_ws, {"session_status"})
            player_ws.send_json(_event("leave_session", session_code))
            error = _collect_events(player_ws, {"error"})["error"]
            assert error["payload"]["code"] == "invalid_session_state"


def test_host_approve_reject_errors(client):
    session_code = client.post("/api/sessions").json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(
            _event("host_approve_join", session_code, {"request_id": "req"})
        )
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_session_state"

        host_ws.send_json(_event("host_start", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        host_ws.send_json(
            _event("host_approve_join", session_code, {"request_id": "missing"})
        )
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_request"

        host_ws.send_json(
            _event("host_reject_join", session_code, {"request_id": "missing"})
        )
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_request"


def test_host_kick_invalid_player(client):
    session_code = client.post("/api/sessions").json()["session_code"]
    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"session_status", "lobby_snapshot"})
        host_ws.send_json(_event("host_kick", session_code, {"player_id": "missing"}))
        error = _collect_events(host_ws, {"error"})["error"]
        assert error["payload"]["code"] == "invalid_player"
