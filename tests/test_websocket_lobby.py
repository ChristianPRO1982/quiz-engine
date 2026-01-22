"""WebSocket lobby join/leave behavior tests."""


def _join_payload(session_code, nickname):
    return {
        "v": "2",
        "type": "join_session",
        "session_code": session_code,
        "payload": {"nickname": nickname},
    }


def _collect_events(websocket, expected_types):
    seen = {}
    while expected_types - seen.keys():
        event = websocket.receive_json()
        if event["type"] in expected_types:
            seen[event["type"]] = event
    return seen


def test_player_join_leave_broadcast(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        snapshot = _collect_events(host_ws, {"lobby_snapshot"})["lobby_snapshot"]
        assert snapshot["type"] == "lobby_snapshot"
        assert snapshot["payload"]["players"] == []

        with client.websocket_connect(
            f"/ws?role=player&session_code={session_code}"
        ) as player_ws:
            player_ws.send_json(_join_payload(session_code, "Alice"))

            events = _collect_events(host_ws, {"player_joined", "lobby_snapshot"})

            assert events["player_joined"]["type"] == "player_joined"
            assert events["lobby_snapshot"]["type"] == "lobby_snapshot"

            player_id = events["player_joined"]["payload"]["player_id"]
            players = events["lobby_snapshot"]["payload"]["players"]
            assert any(entry["player_id"] == player_id for entry in players)

        events = _collect_events(host_ws, {"player_left", "lobby_snapshot"})

        assert events["player_left"]["type"] == "player_left"
        assert events["lobby_snapshot"]["type"] == "lobby_snapshot"
