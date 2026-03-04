"""Coverage tests for admin helper branches and legacy handlers."""

from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi.responses import RedirectResponse

from auth.models import AuthUser
from quiz_engine.routers import admin as admin_router
from quiz_engine.routers.admin import _parse_int_query, _scan_summary_from_query


async def _async_result(value):  # noqa: ANN001, ANN201
    return value


class _TemplateRenderer:
    def __init__(self) -> None:
        self.last_template = ""
        self.last_context: dict[str, object] = {}

    def TemplateResponse(self, _request, template_name, context, status_code=200):  # noqa: N802, ANN001
        self.last_template = template_name
        self.last_context = context
        return SimpleNamespace(status_code=status_code, context=context)


@pytest.mark.anyio
async def test_admin_step1_submit_legacy_validation(monkeypatch) -> None:
    renderer = _TemplateRenderer()
    fake_user = AuthUser(
        subject="user1",
        display_name="User 1",
        email=None,
        auth_mode="dev",
    )
    request = SimpleNamespace()

    monkeypatch.setattr(admin_router, "_templates", lambda _request: renderer)
    monkeypatch.setattr(
        admin_router,
        "_require_html_user",
        lambda _request: (fake_user, None),
    )
    monkeypatch.setattr(
        admin_router,
        "_parse_form_fields",
        lambda _request: _async_result({"title": "  ", "description": ""}),
    )
    monkeypatch.setattr(
        admin_router.draft_service,
        "get_draft",
        lambda _request: {"title": ""},
    )

    invalid = await admin_router.quizzes_new_step1_submit(request)
    assert invalid.status_code == 400
    assert renderer.last_template == "admin/quizzes_new_step1.html"
    assert renderer.last_context["error"] == "Title is required."

    saved: dict[str, str | None] = {}

    def _save_metadata(_request, *, title, description):  # noqa: ANN001
        saved["title"] = title
        saved["description"] = description
        return {"title": title, "description": description}

    monkeypatch.setattr(
        admin_router,
        "_parse_form_fields",
        lambda _request: _async_result({"title": "Quiz title", "description": "Desc"}),
    )
    monkeypatch.setattr(admin_router.draft_service, "save_metadata", _save_metadata)

    valid = await admin_router.quizzes_new_step1_submit(request)
    assert isinstance(valid, RedirectResponse)
    assert valid.status_code == 303
    assert valid.headers["location"] == "/admin/quizzes/new/step-2"
    assert saved == {"title": "Quiz title", "description": "Desc"}


@pytest.mark.anyio
async def test_admin_duplicate_handles_non_dict_payload(monkeypatch) -> None:
    fake_user = AuthUser(
        subject="user1",
        display_name="User 1",
        email=None,
        auth_mode="dev",
    )
    request = SimpleNamespace()
    captured: dict[str, object] = {}

    @contextmanager
    def _fake_session():
        yield SimpleNamespace()

    monkeypatch.setattr(admin_router, "get_session", _fake_session)
    monkeypatch.setattr(
        admin_router,
        "_require_html_user",
        lambda _request: (fake_user, None),
    )
    monkeypatch.setattr(
        admin_router,
        "ensure_user_record",
        lambda _session, _auth_user: SimpleNamespace(id=1),
    )
    monkeypatch.setattr(
        admin_router.quiz_service,
        "get_quiz_detail",
        lambda _session, user_id, quiz_id: SimpleNamespace(payload="not-a-dict"),
    )
    monkeypatch.setattr(
        admin_router.draft_service,
        "duplicate_from_payload",
        lambda _request, payload: captured.setdefault("payload", payload),
    )

    response = await admin_router.quiz_duplicate(request, quiz_id=42)
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/quizzes"
    assert captured["payload"] == {}


def test_admin_scan_summary_and_int_parser_helpers() -> None:
    request = SimpleNamespace(
        query_params={
            "scan_status": "weird",
            "scan_added": "7",
            "scan_updated": "-2",
            "scan_removed": "bad",
            "scan_errors": None,
        }
    )
    summary = _scan_summary_from_query(request)
    assert summary == {
        "status": "partial",
        "added": 7,
        "updated": 0,
        "removed": 0,
        "errors": 0,
    }

    empty = SimpleNamespace(query_params={})
    assert _scan_summary_from_query(empty) is None
    assert _parse_int_query(request, "scan_added") == 7
    assert _parse_int_query(request, "scan_removed") == 0
