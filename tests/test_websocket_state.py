"""WebSocket session state transition tests."""


def _host_event(event_type, session_code):
    return {
        "v": "1",
        "type": event_type,
        "session_code": session_code,
        "payload": {},
    }


def test_host_state_transitions(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        host_ws.receive_json()

        host_ws.send_json(_host_event("host_start", session_code))
        state_event = host_ws.receive_json()
        snapshot_event = host_ws.receive_json()

        assert state_event["type"] == "session_state_changed"
        assert state_event["payload"]["previous_state"] == "LOBBY"
        assert state_event["payload"]["current_state"] == "RUNNING"
        assert snapshot_event["type"] == "lobby_snapshot"

        host_ws.send_json(_host_event("host_end", session_code))
        end_event = host_ws.receive_json()
        end_snapshot = host_ws.receive_json()

        assert end_event["type"] == "session_state_changed"
        assert end_event["payload"]["previous_state"] == "RUNNING"
        assert end_event["payload"]["current_state"] == "ENDED"
        assert end_snapshot["type"] == "lobby_snapshot"


def test_invalid_state_transition_emits_error(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        host_ws.receive_json()

        host_ws.send_json(_host_event("host_end", session_code))
        error_event = host_ws.receive_json()

        assert error_event["type"] == "error"
        assert error_event["payload"]["code"] == "invalid_session_state"


def test_join_rejected_when_running(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        host_ws.receive_json()
        host_ws.send_json(_host_event("host_start", session_code))
        host_ws.receive_json()
        host_ws.receive_json()

        with client.websocket_connect("/ws?role=player") as player_ws:
            player_ws.send_json(
                {
                    "v": "1",
                    "type": "join_session",
                    "session_code": session_code,
                    "payload": {"nickname": "Bob"},
                }
            )
            error_event = player_ws.receive_json()
            assert error_event["type"] == "error"
            assert error_event["payload"]["code"] == "invalid_session_state"
