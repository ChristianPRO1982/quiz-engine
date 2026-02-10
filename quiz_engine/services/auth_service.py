"""Authentication service helpers."""

from __future__ import annotations

from dataclasses import asdict

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.deps import SESSION_AUTH_USER_KEY
from auth.models import AuthUser
from auth.settings import AuthSettings
from quiz_engine.middleware.session import get_session_data
from quiz_engine.models.user import User

_DEV_USERS: dict[str, AuthUser] = {
    "user1": AuthUser(
        subject="dev-user1",
        display_name="Dev User 1",
        email="user1@local.test",
        auth_mode="dev",
    ),
    "user2": AuthUser(
        subject="dev-user2",
        display_name="Dev User 2",
        email="user2@local.test",
        auth_mode="dev",
    ),
}


def list_dev_user_keys() -> list[str]:
    return sorted(_DEV_USERS)


def resolve_dev_user(choice: str) -> AuthUser | None:
    return _DEV_USERS.get(choice)


def login_dev_user(request: Request, choice: str) -> AuthUser | None:
    user = resolve_dev_user(choice)
    if user is None:
        return None

    get_session_data(request)[SESSION_AUTH_USER_KEY] = asdict(user)
    return user


def logout_user(request: Request) -> None:
    get_session_data(request).pop(SESSION_AUTH_USER_KEY, None)


def auth_mode() -> str:
    return AuthSettings.from_env().mode


def ensure_user_record(session: Session, auth_user: AuthUser) -> User:
    stmt = select(User).where(User.subject == auth_user.subject)
    db_user = session.execute(stmt).scalar_one_or_none()
    if db_user is not None:
        return db_user

    db_user = User(subject=auth_user.subject)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
