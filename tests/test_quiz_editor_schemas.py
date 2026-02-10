"""Tests for quiz editor schema normalization and validation."""

from __future__ import annotations

import pytest

from quiz_engine.schemas.quiz_editor_schemas import (
    EditorQuestion,
    QuizEditorPayload,
    normalize_editor_payload,
    to_storage_payload,
)


def test_editor_question_strips_fields() -> None:
    question = EditorQuestion(
        question_id="  q1  ",
        type="  slide ",
        title="  Title ",
        spec={},
    )
    assert question.question_id == "q1"
    assert question.type == "slide"
    assert question.title == "Title"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {"question_id": "  ", "type": "slide", "title": "t", "spec": {}},
            "question_id is required",
        ),
        (
            {"question_id": "q", "type": "  ", "title": "t", "spec": {}},
            "type is required",
        ),
        (
            {"question_id": "q", "type": "slide", "title": "  ", "spec": {}},
            "title is required",
        ),
    ],
)
def test_editor_question_validation_errors(payload: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        EditorQuestion(**payload)


def test_editor_question_validation_rejects_non_dict_spec_on_manual_normalize() -> None:
    question = EditorQuestion.model_construct(
        question_id="q",
        type="slide",
        title="t",
        spec=[],
    )
    with pytest.raises(ValueError, match="spec must be an object"):
        question._normalize()


def test_quiz_editor_payload_rejects_duplicate_question_ids() -> None:
    with pytest.raises(ValueError, match="question_id values must be unique"):
        QuizEditorPayload(
            schema_version="v1",
            title="Quiz",
            questions=[
                {"question_id": "same", "type": "slide", "title": "A", "spec": {}},
                {"question_id": "same", "type": "slide", "title": "B", "spec": {}},
            ],
        )


def test_normalize_editor_payload_covers_stages_legacy_and_deduping() -> None:
    detail = normalize_editor_payload(
        quiz_id=9,
        schema_version="v9",
        payload={
            "title": "  ",
            "description": "   ",
            "stages": [
                "not-a-dict",
                {
                    "plugin_id": "poll",
                    "stage_id": "stage-1",
                    "plugin_spec": {"kind": "poll"},
                },
                {
                    "type": "slide",
                    "question_id": "dup",
                    "spec": {"content": {"title": "From content"}},
                },
                {
                    "type": "slide",
                    "question_id": "dup",
                    "text": " Legacy text ",
                    "choices": [" A ", ""],
                },
                {
                    "type": "slide",
                    "question_id": "raw-spec-not-dict",
                    "spec": "bad",
                    "plugin_spec": "bad-too",
                    "text": "X",
                    "choices": "bad-choices",
                },
            ],
        },
    )

    assert detail.quiz_id == 9
    assert detail.title == "Untitled quiz"
    assert detail.description is None
    assert detail.schema_version == "v9"
    assert [question.question_id for question in detail.questions] == [
        "question-1",
        "stage-1",
        "dup",
        "dup-2",
        "raw-spec-not-dict",
    ]
    assert detail.questions[1].title == "Question 2"
    assert detail.questions[1].spec == {"kind": "poll"}
    assert detail.questions[2].title == "From content"
    assert detail.questions[3].spec == {"text": "Legacy text", "choices": ["A"]}
    assert detail.questions[4].spec == {"text": "X", "choices": []}


def test_normalize_editor_payload_accepts_non_dict_payload() -> None:
    detail = normalize_editor_payload(quiz_id=1, schema_version="v1", payload=[])
    assert detail.title == "Untitled quiz"
    assert detail.questions == []


def test_to_storage_payload_roundtrip_shape() -> None:
    payload = QuizEditorPayload(
        schema_version="v1",
        title="Quiz",
        description="Desc",
        questions=[{"question_id": "q1", "type": "slide", "title": "T", "spec": {}}],
    )

    stored = to_storage_payload(payload)

    assert stored == {
        "schema_version": "v1",
        "title": "Quiz",
        "description": "Desc",
        "questions": [{"question_id": "q1", "type": "slide", "title": "T", "spec": {}}],
    }
