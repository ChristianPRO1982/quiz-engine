"""Quiz APIs and admin pages."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from auth.deps import get_current_user, require_current_user
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


def _templates(request: Request):
    return request.app.state.templates


async def _parse_form_fields(request: Request) -> dict[str, str]:
    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {key: values[-1] for key, values in parsed.items() if values}


def _require_html_user(request: Request):
    user = get_current_user(request)
    if user is None:
        return None, RedirectResponse(url="/login", status_code=303)
    return user, None


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


@router.get("/admin/quizzes", response_class=HTMLResponse)
async def quizzes_list_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quizzes = quiz_service.list_quizzes(session, user_id=db_user.id)

    items = [_quiz_to_summary(quiz) for quiz in quizzes]
    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_list.html",
        {"current_user": auth_user, "quizzes": items},
    )


@router.get("/admin/quizzes/new", response_class=HTMLResponse)
async def quizzes_new_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_new.html",
        {"current_user": auth_user, "error": None},
    )


@router.post("/admin/quizzes/new", response_model=None)
async def quizzes_new_submit(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    form = await _parse_form_fields(request)
    title = str(form.get("title", "")).strip()
    description = str(form.get("description", "")).strip()
    question = str(form.get("question", "")).strip()
    raw_choices = [
        str(form.get("choice1", "")).strip(),
        str(form.get("choice2", "")).strip(),
        str(form.get("choice3", "")).strip(),
    ]
    choices = [choice for choice in raw_choices if choice]

    try:
        payload = QuizCreateRequest(
            schema_version="v1",
            title=title,
            description=description or None,
            questions=[
                {
                    "type": "qcm_single",
                    "text": question,
                    "choices": choices,
                }
            ],
        )
    except Exception as exc:  # noqa: BLE001
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new.html",
            {
                "current_user": auth_user,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.create_quiz(session, user_id=db_user.id, payload=payload)

    return RedirectResponse(url=f"/admin/quizzes/{quiz.id}", status_code=303)


@router.get("/admin/quizzes/{quiz_id}", response_class=HTMLResponse)
async def quizzes_detail_page(request: Request, quiz_id: int) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        try:
            quiz = quiz_service.get_quiz_detail(
                session, user_id=db_user.id, quiz_id=quiz_id
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(status_code=404, detail="Quiz not found") from exc
            raise

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_detail.html",
        {
            "current_user": auth_user,
            "quiz": quiz,
            "quiz_payload_json": json.dumps(
                quiz.payload,
                ensure_ascii=True,
                indent=2,
            ),
        },
    )
