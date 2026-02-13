"""Host HTML routes for creating and managing live sessions."""

from __future__ import annotations

import base64
import io

import qrcode
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from auth.deps import get_current_user
from quiz_engine.db.session import get_session
from quiz_engine.services.auth_service import ensure_user_record
from quiz_engine.services.quiz_service import QuizService
from quiz_engine.services.session_persist_service import SessionPersistService
from quiz_engine.services.stage_orchestrator_service import StageOrchestratorService

router = APIRouter()
quiz_service = QuizService()
session_persist_service = SessionPersistService()
stage_orchestrator_service = StageOrchestratorService(session_persist_service)


def _templates(request: Request):
    return request.app.state.templates


def _require_html_user(request: Request):
    user = get_current_user(request)
    if user is None:
        return None, RedirectResponse(url="/login", status_code=303)
    return user, None


def _build_qr_data_url(content: str) -> str:
    image = qrcode.make(content)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


@router.post("/host/quizzes/{quiz_id}/start", response_model=None)
async def host_start_session_from_quiz(request: Request, quiz_id: int) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.get_quiz_detail(
            session,
            user_id=db_user.id,
            quiz_id=quiz_id,
        )
        created = session_persist_service.create_session(
            session,
            quiz_id=quiz.id,
            host_user_id=db_user.id,
        )
        stages = stage_orchestrator_service.build_stages_from_quiz_payload(quiz.payload)

    live_service = request.app.state.session_live_service
    await live_service.create_or_replace_session(
        session_id=created.id,
        quiz_id=quiz.id,
        session_code=created.session_code,
        lifecycle_state=created.state,
        stages=stages,
    )

    return RedirectResponse(url=f"/host/s/{created.session_code}", status_code=303)


@router.get("/host/s/{session_code}", response_class=HTMLResponse)
async def host_session_page(request: Request, session_code: str) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        db_session = session_persist_service.get_session_by_code(
            session,
            session_code=session_code,
        )
        if db_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if db_session.host_user_id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        players = session_persist_service.list_active_players(
            session,
            session_id=db_session.id,
        )

    join_url = str(request.url_for("join_session_page", session_code=session_code))
    qr_data_url = _build_qr_data_url(join_url)

    return _templates(request).TemplateResponse(
        request,
        "host/session.html",
        {
            "current_user": auth_user,
            "session_code": session_code,
            "join_url": join_url,
            "qr_data_url": qr_data_url,
            "session_state": db_session.state,
            "players": [
                {"player_id": player.id, "nickname": player.nickname}
                for player in players
            ],
        },
    )
