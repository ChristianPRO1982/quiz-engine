"""Admin HTML routes for navigation and guided quiz creation."""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError

from auth.deps import get_current_user
from quiz_engine.db.session import get_session
from quiz_engine.plugins.registry import build_default_registry
from quiz_engine.schemas.quiz_editor_schemas import normalize_editor_payload
from quiz_engine.schemas.quiz_schemas import QuizCreateRequest
from quiz_engine.services.auth_service import (
    ensure_user_record,
    list_user_roles,
    user_has_role,
)
from quiz_engine.services.plugin_catalog_service import PluginCatalogService
from quiz_engine.services.plugin_registry_service import PluginRegistryService
from quiz_engine.services.quiz_draft_service import QuizDraftService
from quiz_engine.services.quiz_editor_service import QuizEditorService
from quiz_engine.services.quiz_service import QuizService

router = APIRouter()
quiz_service = QuizService()
draft_service = QuizDraftService()
quiz_editor_service = QuizEditorService()
plugin_registry_service = PluginRegistryService()
plugin_catalog_service = PluginCatalogService()


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


@router.get("/admin", response_class=HTMLResponse)
async def admin_index_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        user_roles = list_user_roles(session, user_id=db_user.id)
        plugin_catalog_rows = plugin_catalog_service.list_catalog(session)

    scan_summary = _scan_summary_from_query(request)

    return _templates(request).TemplateResponse(
        request,
        "admin/index.html",
        {
            "current_user": auth_user,
            "can_scan_plugins": "admin" in user_roles,
            "plugin_catalog": plugin_catalog_rows,
            "scan_summary": scan_summary,
        },
    )


@router.post("/admin/plugins/scan", response_model=None)
async def admin_scan_plugins(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        if not user_has_role(session, user_id=db_user.id, role="admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role is required to scan plugins.",
            )
        scan_result = plugin_catalog_service.scan_and_sync(session)

    request.app.state.plugin_registry = build_default_registry()

    query = {
        "scan_status": "ok" if not scan_result.errors else "partial",
        "scan_added": str(len(scan_result.added)),
        "scan_updated": str(len(scan_result.updated)),
        "scan_removed": str(len(scan_result.removed)),
        "scan_errors": str(len(scan_result.errors)),
    }
    return RedirectResponse(url=f"/admin?{urlencode(query)}", status_code=303)


@router.get("/admin/quizzes", response_class=HTMLResponse)
async def quizzes_list_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quizzes = quiz_service.list_quizzes(session, user_id=db_user.id)

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_list.html",
        {
            "current_user": auth_user,
            "quizzes": quizzes,
        },
    )


@router.post("/admin/quizzes", response_model=None)
async def quizzes_create_and_edit(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_editor_service.create_quiz(session, user_id=db_user.id)

    return RedirectResponse(url=f"/admin/quizzes/{quiz.id}", status_code=303)


@router.post("/admin/quizzes/{quiz_id}/delete", response_model=None)
async def quiz_delete(request: Request, quiz_id: int) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz_service.delete_quiz(session, user_id=db_user.id, quiz_id=quiz_id)

    return RedirectResponse(url="/admin/quizzes", status_code=303)


@router.get("/admin/quizzes/new", response_class=HTMLResponse)
async def quizzes_new_entry(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    return RedirectResponse(url="/admin/quizzes", status_code=303)


@router.post("/admin/quizzes/new", response_model=None)
async def quizzes_new_legacy_submit(request: Request) -> Response:
    """Compatibility endpoint kept for Sprint 2 form submissions."""
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    form = await _parse_form_fields(request)

    question_text = str(form.get("question", "")).strip()
    if question_text:
        raw_choices = [
            str(form.get("choice1", "")).strip(),
            str(form.get("choice2", "")).strip(),
            str(form.get("choice3", "")).strip(),
        ]
        choices = [choice for choice in raw_choices if choice]

        try:
            payload = QuizCreateRequest(
                schema_version="v1",
                title=str(form.get("title", "")).strip(),
                description=str(form.get("description", "")).strip() or None,
                questions=[
                    {
                        "type": "qcm_single",
                        "text": question_text,
                        "choices": choices,
                    }
                ],
            )
        except ValidationError as exc:
            draft = draft_service.save_metadata(
                request,
                title=str(form.get("title", "")).strip(),
                description=str(form.get("description", "")).strip() or None,
            )
            return _templates(request).TemplateResponse(
                request,
                "admin/quizzes_new_step1.html",
                {
                    "current_user": auth_user,
                    "draft": draft,
                    "error": str(exc),
                },
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        with get_session() as session:
            db_user = ensure_user_record(session, auth_user)
            quiz = quiz_service.create_quiz(
                session, user_id=db_user.id, payload=payload
            )

        draft_service.clear_draft(request)
        return RedirectResponse(url=f"/admin/quizzes/{quiz.id}", status_code=303)

    title = str(form.get("title", "")).strip()
    description = str(form.get("description", "")).strip()
    if not title:
        draft = draft_service.get_draft(request)
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_step1.html",
            {
                "current_user": auth_user,
                "draft": draft,
                "error": "Title is required.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    draft_service.save_metadata(request, title=title, description=description or None)
    return RedirectResponse(url="/admin/quizzes/new/step-2", status_code=303)


@router.get("/admin/quizzes/new/step-1", response_class=HTMLResponse)
async def quizzes_new_step1_page(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    return RedirectResponse(url="/admin/quizzes", status_code=303)


@router.post("/admin/quizzes/new/step-1", response_model=None)
async def quizzes_new_step1_submit(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    form = await _parse_form_fields(request)
    title = str(form.get("title", "")).strip()
    description = str(form.get("description", "")).strip()
    if not title:
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_step1.html",
            {
                "current_user": auth_user,
                "draft": draft_service.get_draft(request),
                "error": "Title is required.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    draft_service.save_metadata(request, title=title, description=description or None)
    return RedirectResponse(url="/admin/quizzes/new/step-2", status_code=303)


@router.get("/admin/quizzes/new/step-2", response_class=HTMLResponse)
async def quizzes_new_step2_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_new_step2.html",
        {
            "current_user": auth_user,
            "draft": draft_service.get_draft(request),
            "error": None,
        },
    )


@router.post("/admin/quizzes/new/step-2", response_model=None)
async def quizzes_new_step2_submit(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    form = await _parse_form_fields(request)
    action = str(form.get("action", "add")).strip()

    if action == "back":
        return RedirectResponse(url="/admin/quizzes", status_code=303)

    if action == "review":
        return RedirectResponse(url="/admin/quizzes/new/review", status_code=303)

    question_text = str(form.get("question", "")).strip()
    choices = [
        str(form.get("choice1", "")).strip(),
        str(form.get("choice2", "")).strip(),
        str(form.get("choice3", "")).strip(),
        str(form.get("choice4", "")).strip(),
    ]
    cleaned_choices = [choice for choice in choices if choice]

    if not question_text:
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_step2.html",
            {
                "current_user": auth_user,
                "draft": draft_service.get_draft(request),
                "error": "Question text is required.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(cleaned_choices) < 2:
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_step2.html",
            {
                "current_user": auth_user,
                "draft": draft_service.get_draft(request),
                "error": "At least two non-empty choices are required.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    draft_service.add_question(request, text=question_text, choices=cleaned_choices)

    if str(form.get("next", "")).strip() == "review":
        return RedirectResponse(url="/admin/quizzes/new/review", status_code=303)

    return RedirectResponse(url="/admin/quizzes/new/step-2", status_code=303)


@router.get("/admin/quizzes/new/review", response_class=HTMLResponse)
async def quizzes_new_review_page(request: Request) -> HTMLResponse:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_new_review.html",
        {
            "current_user": auth_user,
            "draft": draft_service.get_draft(request),
            "error": None,
        },
    )


@router.post("/admin/quizzes/new/save", response_model=None)
async def quizzes_new_save(request: Request) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    draft = draft_service.get_draft(request)
    questions = draft.get("questions")
    if not isinstance(questions, list) or not questions:
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_review.html",
            {
                "current_user": auth_user,
                "draft": draft,
                "error": "At least one question is required before saving.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = draft_service.build_create_request(request)
    except ValidationError as exc:
        return _templates(request).TemplateResponse(
            request,
            "admin/quizzes_new_review.html",
            {
                "current_user": auth_user,
                "draft": draft_service.get_draft(request),
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.create_quiz(session, user_id=db_user.id, payload=payload)

    draft_service.clear_draft(request)
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

    editor_payload = normalize_editor_payload(
        quiz_id=quiz.id,
        schema_version=quiz.schema_version,
        payload=quiz.payload,
    )
    question_types = plugin_registry_service.list_question_types(request)

    return _templates(request).TemplateResponse(
        request,
        "admin/quizzes_editor.html",
        {
            "current_user": auth_user,
            "quiz": quiz,
            "editor_payload": editor_payload.model_dump(),
            "question_types": [option.model_dump() for option in question_types],
        },
    )


@router.post("/admin/quizzes/{quiz_id}/duplicate", response_model=None)
async def quiz_duplicate(request: Request, quiz_id: int) -> Response:
    auth_user, redirect = _require_html_user(request)
    if redirect is not None:
        return redirect

    with get_session() as session:
        db_user = ensure_user_record(session, auth_user)
        quiz = quiz_service.get_quiz_detail(
            session, user_id=db_user.id, quiz_id=quiz_id
        )

    payload = quiz.payload or {}
    if not isinstance(payload, dict):
        payload = {}

    draft_service.duplicate_from_payload(request, payload)
    return RedirectResponse(url="/admin/quizzes", status_code=303)


def _scan_summary_from_query(request: Request) -> dict[str, int | str] | None:
    status_text = str(request.query_params.get("scan_status", "")).strip()
    if not status_text:
        return None
    if status_text not in {"ok", "partial"}:
        status_text = "partial"
    return {
        "status": status_text,
        "added": _parse_int_query(request, "scan_added"),
        "updated": _parse_int_query(request, "scan_updated"),
        "removed": _parse_int_query(request, "scan_removed"),
        "errors": _parse_int_query(request, "scan_errors"),
    }


def _parse_int_query(request: Request, key: str) -> int:
    raw = request.query_params.get(key)
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return 0
    return max(value, 0)
