"""Player join/session HTML routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse

from quiz_engine.db.session import get_session
from quiz_engine.services.session_persist_service import SessionPersistService

router = APIRouter()
session_persist_service = SessionPersistService()


def _templates(request: Request):
    return request.app.state.templates


@router.get(
    "/join/{session_code}",
    response_class=HTMLResponse,
    name="join_session_page",
)
async def join_page(request: Request, session_code: str) -> HTMLResponse:
    with get_session() as session:
        db_session = session_persist_service.get_session_by_code(
            session,
            session_code=session_code,
        )
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return _templates(request).TemplateResponse(
        request,
        "player/join.html",
        {
            "current_user": None,
            "show_admin_chrome": False,
            "session_code": session_code,
        },
    )


@router.get(
    "/player/s/{session_code}",
    response_class=HTMLResponse,
    name="player_session_page",
)
async def player_session_page(request: Request, session_code: str) -> HTMLResponse:
    with get_session() as session:
        db_session = session_persist_service.get_session_by_code(
            session,
            session_code=session_code,
        )
    if db_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    nickname = str(request.query_params.get("nickname", "")).strip()[:32]

    return _templates(request).TemplateResponse(
        request,
        "player/session.html",
        {
            "current_user": None,
            "show_admin_chrome": False,
            "session_code": session_code,
            "nickname": nickname,
            "session_state": db_session.state,
        },
    )
