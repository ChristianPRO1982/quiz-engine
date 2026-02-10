"""Quiz APIs."""

from __future__ import annotations

from fastapi import APIRouter, Request

from auth.deps import require_current_user
from quiz_engine.db.session import get_session
from quiz_engine.schemas.quiz_editor_schemas import (
    QuizEditorDetailResponse,
    QuizEditorPayload,
    normalize_editor_payload,
)
from quiz_engine.schemas.quiz_schemas import (
    QuizCreateRequest,
    QuizSummaryResponse,
)
from quiz_engine.services.auth_service import ensure_user_record
from quiz_engine.services.quiz_editor_service import QuizEditorService
from quiz_engine.services.quiz_service import QuizService

router = APIRouter()
quiz_service = QuizService()
quiz_editor_service = QuizEditorService()


def _quiz_to_summary(quiz) -> QuizSummaryResponse:
    payload = quiz.payload or {}
    return QuizSummaryResponse(
        id=quiz.id,
        schema_version=quiz.schema_version,
        title=str(payload.get("title", "")),
        description=payload.get("description"),
    )


def _quiz_to_detail(quiz) -> QuizEditorDetailResponse:
    return normalize_editor_payload(
        quiz_id=quiz.id,
        schema_version=quiz.schema_version,
        payload=quiz.payload,
    )


@router.post("/api/quizzes", response_model=QuizEditorDetailResponse, status_code=201)
async def create_quiz_api(
    request: Request, payload: QuizCreateRequest
) -> QuizEditorDetailResponse:
    auth_user = require_current_user(request)

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.create_quiz(session, user_id=db_user.id, payload=payload)

    return _quiz_to_detail(quiz)


@router.get("/api/quizzes", response_model=list[QuizSummaryResponse])
async def list_quizzes_api(request: Request) -> list[QuizSummaryResponse]:
    auth_user = require_current_user(request)

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quizzes = quiz_service.list_quizzes(session, user_id=db_user.id)

    return [_quiz_to_summary(quiz) for quiz in quizzes]


@router.get("/api/quizzes/{quiz_id}", response_model=QuizEditorDetailResponse)
async def quiz_detail_api(request: Request, quiz_id: int) -> QuizEditorDetailResponse:
    auth_user = require_current_user(request)

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        detail = quiz_editor_service.get_editor_payload(
            session, user_id=db_user.id, quiz_id=quiz_id
        )
    return detail


@router.put("/api/quizzes/{quiz_id}", response_model=QuizEditorDetailResponse)
async def quiz_update_api(
    request: Request,
    quiz_id: int,
    payload: QuizEditorPayload,
) -> QuizEditorDetailResponse:
    auth_user = require_current_user(request)

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        detail = quiz_editor_service.save_editor_payload(
            session,
            user_id=db_user.id,
            quiz_id=quiz_id,
            payload=payload,
        )
    return detail
