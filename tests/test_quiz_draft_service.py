"""Coverage tests for quiz draft session service."""

from __future__ import annotations

from starlette.requests import Request

from quiz_engine.services.quiz_draft_service import (
    SESSION_QUIZ_DRAFT_KEY,
    QuizDraftService,
)


def _make_request(session: dict | None = None) -> Request:
    request = Request({"type": "http", "method": "GET", "path": "/", "headers": []})
    request.state.session = session or {}
    return request


def test_get_draft_normalizes_and_updates_session_value() -> None:
    service = QuizDraftService()
    request = _make_request(
        {
            SESSION_QUIZ_DRAFT_KEY: {
                "schema_version": "v1",
                "title": "  My quiz  ",
                "description": "  Desc  ",
                "questions": [
                    {"type": "qcm_single", "text": "  Q  ", "choices": [" A ", " "]}
                ],
                "updated_at": "old",
            }
        }
    )

    draft = service.get_draft(request)

    assert draft["title"] == "My quiz"
    assert draft["description"] == "Desc"
    assert draft["questions"] == []
    assert request.state.session[SESSION_QUIZ_DRAFT_KEY] == draft


def test_duplicate_from_payload_filters_invalid_question_structures() -> None:
    service = QuizDraftService()
    request = _make_request()

    service.duplicate_from_payload(
        request,
        {
            "schema_version": "v2",
            "title": " Duplicate ",
            "description": " Text ",
            "questions": [
                "not-a-dict",
                {"type": "qcm_single", "text": "", "choices": ["A", "B"]},
                {"type": "qcm_single", "text": "Q1", "choices": "not-list"},
                {"type": "qcm_single", "text": "Q2", "choices": ["", "A", "B"]},
            ],
        },
    )

    draft = request.state.session[SESSION_QUIZ_DRAFT_KEY]
    assert draft["schema_version"] == "v2"
    assert draft["title"] == "Duplicate"
    assert draft["description"] == "Text"
    assert len(draft["questions"]) == 1
    assert draft["questions"][0]["text"] == "Q2"


def test_build_create_request_and_clear_draft() -> None:
    service = QuizDraftService()
    request = _make_request()

    service.save_metadata(request, title="Quiz", description="Desc")
    service.add_question(request, text="Q", choices=["A", "B"])

    payload = service.build_create_request(request)
    assert payload.title == "Quiz"
    assert payload.questions[0].type == "qcm_single"

    service.clear_draft(request)
    assert SESSION_QUIZ_DRAFT_KEY not in request.state.session


def test_get_draft_skips_non_dict_questions_and_non_list_choices() -> None:
    service = QuizDraftService()
    request = _make_request(
        {
            SESSION_QUIZ_DRAFT_KEY: {
                "schema_version": "v1",
                "title": "Quiz",
                "description": "Desc",
                "questions": [
                    "string-entry",
                    {"type": "qcm_single", "text": "Q", "choices": "no-list"},
                    {"type": "other", "text": "Q", "choices": ["A", "B"]},
                    {"type": "qcm_single", "text": "Valid", "choices": ["A", "B"]},
                ],
                "updated_at": "stamp",
            }
        }
    )

    draft = service.get_draft(request)

    assert len(draft["questions"]) == 1
    assert draft["questions"][0]["text"] == "Valid"
