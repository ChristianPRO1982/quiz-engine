from __future__ import annotations

from fastapi import HTTPException, Request, status

from quiz_engine.middleware.session import get_session_data

from .models import AuthUser

SESSION_AUTH_USER_KEY = "auth_user"


def get_current_user(request: Request) -> AuthUser | None:
    """Return current authenticated user or None."""
    session_user = get_session_data(request).get(SESSION_AUTH_USER_KEY)
    if not isinstance(session_user, dict):
        return None

    subject = str(session_user.get("subject", "")).strip()
    display_name = str(session_user.get("display_name", "")).strip()
    auth_mode = str(session_user.get("auth_mode", "")).strip()
    email = session_user.get("email")
    if email is not None:
        email = str(email)

    if not subject or not display_name or not auth_mode:
        return None

    return AuthUser(
        subject=subject,
        display_name=display_name,
        email=email,
        auth_mode=auth_mode,
    )


def require_current_user(request: Request) -> AuthUser:
    """Return current authenticated user or raise HTTP 401."""
    user = get_current_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return user
