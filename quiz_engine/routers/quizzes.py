"""Quiz APIs."""

from __future__ import annotations

from fastapi import APIRouter, Request

from auth.deps import require_current_user
from quiz_engine.db.session import get_session
from quiz_engine.schemas.quiz_schemas import (
    QuizCreateRequest,
    QuizDetailResponse,
    QuizSummaryResponse,
)
from quiz_engine.services.auth_service import ensure_user_record
from quiz_engine.services.quiz_service import QuizService

router = APIRouter()
quiz_service = QuizService()


def _quiz_to_summary(quiz) -> QuizSummaryResponse:
    payload = quiz.payload or {}
    return QuizSummaryResponse(
        id=quiz.id,
        schema_version=quiz.schema_version,
        title=str(payload.get("title", "")),
        description=payload.get("description"),
    )


def _quiz_to_detail(quiz) -> QuizDetailResponse:
    payload = quiz.payload or {}
    return QuizDetailResponse(
        id=quiz.id,
        schema_version=quiz.schema_version,
        title=str(payload.get("title", "")),
        description=payload.get("description"),
        questions=list(payload.get("questions", [])),
    )


@router.post("/api/quizzes", response_model=QuizDetailResponse, status_code=201)
async def create_quiz_api(
    request: Request, payload: QuizCreateRequest
) -> QuizDetailResponse:
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


@router.get("/api/quizzes/{quiz_id}", response_model=QuizDetailResponse)
async def quiz_detail_api(request: Request, quiz_id: int) -> QuizDetailResponse:
    auth_user = require_current_user(request)

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.get_quiz_detail(
            session, user_id=db_user.id, quiz_id=quiz_id
        )

    return _quiz_to_detail(quiz)
