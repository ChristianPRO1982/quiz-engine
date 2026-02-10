"""Authentication pages and actions."""

from __future__ import annotations

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth.deps import get_current_user
from auth.settings import AuthSettings
from quiz_engine.db.session import get_session
from quiz_engine.services.auth_service import (
    auth_mode,
    list_dev_user_subjects,
    login_dev_user,
    logout_user,
)

router = APIRouter()


def _templates(request: Request):
    return request.app.state.templates


async def _parse_form_fields(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items() if values}


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if user is not None:
        return RedirectResponse(url="/account", status_code=303)

    settings = AuthSettings.from_env()
    dev_users: list[str] = []
    if settings.mode == "dev":
        with get_session() as session:
            dev_users = list_dev_user_subjects(session)

    return _templates(request).TemplateResponse(
        request,
        "auth/login.html",
        {
            "auth_mode": settings.mode,
            "dev_users": dev_users,
            "current_user": None,
        },
    )


@router.post("/login")
async def login_submit(request: Request) -> RedirectResponse:
    form = await _parse_form_fields(request)
    selected_user = str(form.get("user", "")).strip()

    if auth_mode() != "dev":
        return RedirectResponse(url="/login", status_code=303)

    with get_session() as session:
        user = login_dev_user(request, session, selected_user)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    return RedirectResponse(url="/account", status_code=303)


@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    logout_user(request)
    return RedirectResponse(url="/", status_code=303)


@router.get("/account", response_class=HTMLResponse)
async def account_page(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)

    return _templates(request).TemplateResponse(
        request,
        "auth/account.html",
        {"current_user": user},
    )
