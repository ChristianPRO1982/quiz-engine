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


def list_dev_user_subjects(session: Session) -> list[str]:
    stmt = select(User.subject).order_by(User.subject.asc())
    return [subject for subject in session.execute(stmt).scalars()]


def resolve_dev_user(session: Session, subject: str) -> AuthUser | None:
    stmt = select(User).where(User.subject == subject)
    db_user = session.execute(stmt).scalar_one_or_none()
    if db_user is None:
        return None

    user = AuthUser(
        subject=db_user.subject,
        display_name=db_user.subject,
        email=None,
        auth_mode="dev",
    )
    return user


def login_dev_user(request: Request, session: Session, subject: str) -> AuthUser | None:
    user = resolve_dev_user(session, subject)
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
