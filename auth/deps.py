from __future__ import annotations

from fastapi import Request

from .models import AuthUser
from .settings import AuthSettings


DEV_USER = AuthUser(
    sub="dev-user-001",
    email="dev@local.test",
    name="Dev User",
    groups=["users", "admins"],
)


def get_current_user(request: Request) -> AuthUser:
    """Return authenticated user based on configured auth mode."""
    settings = AuthSettings.from_env()

    if settings.mode == "dev":
        return DEV_USER

    session_user = request.session.get("auth_user")
    if not isinstance(session_user, dict):
        raise PermissionError("Not authenticated")

    return AuthUser(
        sub=str(session_user.get("sub", "")),
        email=str(session_user.get("email", "")),
        name=str(session_user.get("name", "")),
        groups=list(session_user.get("groups", [])),
    )
