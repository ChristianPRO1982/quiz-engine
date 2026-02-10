"""Minimal cookie-based session middleware without external dependencies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from copy import deepcopy

from starlette.middleware.base import BaseHTTPMiddleware

SESSION_STATE_KEY = "session"


def _encode(data: dict, secret_key: str) -> str:
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload).decode("ascii")
    signature = hmac.new(
        secret_key.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _decode(raw: str, secret_key: str) -> dict:
    try:
        payload_b64, signature = raw.split(".", 1)
    except ValueError:
        return {}

    expected = hmac.new(
        secret_key.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return {}

    try:
        payload = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        data = json.loads(payload.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


class SessionCookieMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        secret_key: str,
        cookie_name: str = "qe_session",
        max_age: int = 60 * 60 * 24 * 7,
    ) -> None:
        super().__init__(app)
        self._secret_key = secret_key
        self._cookie_name = cookie_name
        self._max_age = max_age

    async def dispatch(self, request, call_next):
        raw = request.cookies.get(self._cookie_name)
        session_data = _decode(raw, self._secret_key) if raw else {}
        request.state.session = session_data
        before = deepcopy(session_data)

        response = await call_next(request)

        after = request.state.session
        if not after:
            response.delete_cookie(self._cookie_name)
        elif after != before:
            response.set_cookie(
                key=self._cookie_name,
                value=_encode(after, self._secret_key),
                max_age=self._max_age,
                httponly=True,
                samesite="lax",
            )

        return response


def get_session_data(request) -> dict:
    data = getattr(request.state, SESSION_STATE_KEY, None)
    if not isinstance(data, dict):
        data = {}
        request.state.session = data
    return data
