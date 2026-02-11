"""Admin quiz preview routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth.deps import get_current_user
from quiz_engine.db.session import get_session
from quiz_engine.schemas.quiz_editor_schemas import normalize_editor_payload
from quiz_engine.services.auth_service import ensure_user_record
from quiz_engine.services.quiz_preview_service import QuizPreviewService

router = APIRouter()
preview_service = QuizPreviewService()


def _templates(request: Request):
    return request.app.state.templates


def _require_html_user(request: Request):
    user = get_current_user(request)
    if user is None:
        return None, RedirectResponse(url="/login", status_code=303)
    return user, None


@router.get("/admin/quizzes/{quiz_id}/preview", response_class=HTMLResponse)
async def quiz_preview_page(request: Request, quiz_id: int) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = preview_service.load_quiz(session, user_id=db_user.id, quiz_id=quiz_id)

    editor_payload = normalize_editor_payload(
        quiz_id=quiz.id,
        schema_version=quiz.schema_version,
        payload=quiz.payload,
    )
    preview_payload = preview_service.build_preview_payload(request, quiz=quiz)

    return _templates(request).TemplateResponse(
        request,
        "admin/quiz_preview.html",
        {
            "current_user": auth_user,
            "show_admin_chrome": False,
            "quiz": quiz,
            "editor_payload": editor_payload.model_dump(),
            "preview_payload": preview_payload,
        },
    )
