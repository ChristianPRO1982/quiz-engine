"""WebSocket session state transition tests."""


def _event(event_type, session_code, payload=None):
    return {
        "v": "2",
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


def test_host_state_transitions(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"lobby_snapshot"})

        host_ws.send_json(_event("host_start", session_code))
        events = _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        state_event = events["session_state_changed"]
        assert state_event["payload"]["previous_state"] == "LOBBY"
        assert state_event["payload"]["current_state"] == "RUNNING"

        host_ws.send_json(_event("host_end", session_code))
        events = _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        end_event = events["session_state_changed"]
        assert end_event["payload"]["previous_state"] == "RUNNING"
        assert end_event["payload"]["current_state"] == "ENDED"


def test_invalid_state_transition_emits_error(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"lobby_snapshot"})

        host_ws.send_json(_event("host_end", session_code))
        error_event = _collect_events(host_ws, {"error"})["error"]

        assert error_event["payload"]["code"] == "invalid_session_state"


def test_join_request_can_be_approved(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"lobby_snapshot"})

        host_ws.send_json(_event("host_start", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Bob"})
            )

            join_requested = _collect_events(host_ws, {"join_requested"})[
                "join_requested"
            ]
            request_id = join_requested["payload"]["request_id"]

            host_ws.send_json(
                _event("host_approve_join", session_code, {"request_id": request_id})
            )

            approved = _collect_events(player_ws, {"join_approved"})["join_approved"]
            assert approved["payload"]["request_id"] == request_id

            _collect_events(host_ws, {"player_joined", "lobby_snapshot"})


def test_join_rejected_when_ended(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"lobby_snapshot"})

        host_ws.send_json(_event("host_start", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        host_ws.send_json(_event("host_end", session_code))
        _collect_events(host_ws, {"session_state_changed", "lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Zoe"})
            )
            error_event = _collect_events(player_ws, {"error"})["error"]
            assert error_event["payload"]["code"] == "invalid_session_state"


def test_host_can_kick_player(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        _collect_events(host_ws, {"lobby_snapshot"})

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            player_ws.send_json(
                _event("join_session", session_code, {"nickname": "Mia"})
            )

            joined = _collect_events(host_ws, {"player_joined"})["player_joined"]
            player_id = joined["payload"]["player_id"]
            _collect_events(host_ws, {"lobby_snapshot"})

            host_ws.send_json(
                _event("host_kick", session_code, {"player_id": player_id})
            )

            kicked = _collect_events(player_ws, {"player_kicked"})["player_kicked"]
            assert kicked["payload"]["player_id"] == player_id

            _collect_events(host_ws, {"player_left", "lobby_snapshot"})
