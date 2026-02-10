"""Coverage tests for session middleware edge branches."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from types import SimpleNamespace

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from quiz_engine.middleware.session import (
    SessionCookieMiddleware,
    _decode,
    _encode,
    get_session_data,
)


def test_decode_returns_empty_dict_for_bad_cookie_format() -> None:
    assert _decode("not-a-cookie", "secret") == {}


def test_decode_returns_empty_dict_for_invalid_signature() -> None:
    encoded = _encode({"a": 1}, "secret")
    payload, _signature = encoded.split(".", 1)
    assert _decode(f"{payload}.bad-signature", "secret") == {}


def test_decode_returns_empty_dict_for_non_dict_json_payload() -> None:
    payload_b64 = base64.urlsafe_b64encode(json.dumps([1, 2]).encode("utf-8")).decode(
        "ascii"
    )
    signature = hmac.new(
        b"secret", payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    assert _decode(f"{payload_b64}.{signature}", "secret") == {}


def test_decode_returns_empty_dict_for_invalid_base64() -> None:
    payload_b64 = "!!!"
    signature = hmac.new(
        b"secret", payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    assert _decode(f"{payload_b64}.{signature}", "secret") == {}


def test_get_session_data_initializes_dict_when_missing_or_invalid() -> None:
    request = SimpleNamespace(state=SimpleNamespace(session="invalid"))
    data = get_session_data(request)
    assert data == {}
    assert isinstance(request.state.session, dict)


def test_session_cookie_middleware_set_noop_and_delete_paths() -> None:
    app = FastAPI()
    app.add_middleware(SessionCookieMiddleware, secret_key="secret")

    @app.get("/set")
    async def set_route(request: Request) -> JSONResponse:
        request.state.session["user"] = "alice"
        return JSONResponse({"ok": True})

    @app.get("/noop")
    async def noop_route(request: Request) -> JSONResponse:
        _ = request.state.session.get("user")
        return JSONResponse({"ok": True})

    @app.get("/clear")
    async def clear_route(request: Request) -> JSONResponse:
        request.state.session.clear()
        return JSONResponse({"ok": True})

    client = TestClient(app)

    set_response = client.get("/set")
    assert set_response.status_code == 200
    assert "set-cookie" in set_response.headers

    noop_response = client.get("/noop")
    assert noop_response.status_code == 200
    assert "set-cookie" not in noop_response.headers

    clear_response = client.get("/clear")
    assert clear_response.status_code == 200
    assert "set-cookie" in clear_response.headers
