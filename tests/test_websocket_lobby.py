"""WebSocket lobby join/leave behavior tests."""


def _join_payload(session_code, nickname):
    return {
        "v": "1",
        "type": "join_session",
        "session_code": session_code,
        "payload": {"nickname": nickname},
    }


def test_player_join_leave_broadcast(client):
    create_response = client.post("/api/sessions")
    session_code = create_response.json()["session_code"]

    with client.websocket_connect(
        f"/ws?role=host&session_code={session_code}"
    ) as host_ws:
        snapshot = host_ws.receive_json()
        assert snapshot["type"] == "lobby_snapshot"
        assert snapshot["payload"]["players"] == []

        with client.websocket_connect("/ws?role=player") as player_ws:
            player_ws.send_json(_join_payload(session_code, "Alice"))

            event_one = host_ws.receive_json()
            event_two = host_ws.receive_json()

            assert event_one["type"] == "player_joined"
            assert event_two["type"] == "lobby_snapshot"

            player_id = event_one["payload"]["player_id"]
            players = event_two["payload"]["players"]
            assert any(entry["player_id"] == player_id for entry in players)

        event_three = host_ws.receive_json()
        event_four = host_ws.receive_json()

        assert event_three["type"] == "player_left"
        assert event_four["type"] == "lobby_snapshot"
