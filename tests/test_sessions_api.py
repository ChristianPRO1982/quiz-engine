"""Tests for the session creation API."""


def test_create_session_returns_join_url(client, app):
    response = client.post("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["schema_version"] == "1"
    assert "session_code" in data
    assert "join_url" in data
    assert data["join_url"].endswith(f"/join/{data['session_code']}")

    store = app.state.store
    assert store.get_session(data["session_code"]) is not None
