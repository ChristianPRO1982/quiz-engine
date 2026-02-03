"""Tests for the home endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from quiz_engine.app import create_app


def test_home_endpoint_renders_dev_badge(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "dev")
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Quiz Engine" in response.text
    assert "Dev" in response.text
