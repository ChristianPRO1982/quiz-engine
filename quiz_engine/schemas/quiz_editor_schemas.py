"""Pydantic schemas and normalization helpers for the quiz editor."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import BaseModel, Field, model_validator


def _clean_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _normalize_legacy_spec(raw_question: dict[str, Any]) -> dict[str, Any]:
    text = _clean_text(raw_question.get("text"))
    raw_choices = raw_question.get("choices")
    if not isinstance(raw_choices, list):
        raw_choices = []
    choices = [_clean_text(choice) for choice in raw_choices if _clean_text(choice)]
    if text or choices:
        return {"text": text, "choices": choices}
    return {}


def _default_title(question_type: str, index: int) -> str:
    if question_type == "slide":
        return f"Slide {index + 1}"
    return f"Question {index + 1}"


def _as_question_dict(raw_question: Any) -> dict[str, Any]:
    if isinstance(raw_question, dict):
        return dict(raw_question)
    return {}


def _dedupe_question_ids(questions: list[EditorQuestion]) -> list[EditorQuestion]:
    seen: dict[str, int] = {}
    deduped: list[EditorQuestion] = []
    for question in questions:
        base = question.question_id
        count = seen.get(base, 0)
        seen[base] = count + 1
        if count == 0:
            deduped.append(question)
            continue
        suffix = count + 1
        deduped.append(question.model_copy(update={"question_id": f"{base}-{suffix}"}))
    return deduped


class EditorQuestion(BaseModel):
    question_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    title: str = Field(min_length=1)
    spec: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _normalize(self) -> EditorQuestion:
        self.question_id = _clean_text(self.question_id)
        self.type = _clean_text(self.type)
        self.title = _clean_text(self.title)
        if not self.question_id:
            raise ValueError("question_id is required")
        if not self.type:
            raise ValueError("type is required")
        if not self.title:
            raise ValueError("title is required")
        if not isinstance(self.spec, dict):
            raise ValueError("spec must be an object")
        return self


class QuizEditorPayload(BaseModel):
    schema_version: str = Field(default="v1", min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    questions: list[EditorQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_question_ids_unique(self) -> QuizEditorPayload:
        question_ids = [question.question_id for question in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("question_id values must be unique")
        return self


class QuizEditorDetailResponse(QuizEditorPayload):
    id: int
    quiz_id: int


class QuestionTypeOption(BaseModel):
    type: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str | None = None
    plugin_type: str | None = None
    stage_config_schema: dict[str, Any] | None = None
    default_stage_config: dict[str, Any] | None = None
    editor_hints: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _normalize(self) -> QuestionTypeOption:
        self.type = _clean_text(self.type)
        self.label = _clean_text(self.label)
        if not self.type:
            raise ValueError("type is required")
        if not self.label:
            raise ValueError("label is required")

        if self.description is not None:
            self.description = _clean_text(self.description) or None
        if self.plugin_type is not None:
            self.plugin_type = _clean_text(self.plugin_type) or None
        if self.stage_config_schema is not None and not isinstance(
            self.stage_config_schema, dict
        ):
            raise ValueError("stage_config_schema must be an object")
        if self.default_stage_config is not None and not isinstance(
            self.default_stage_config, dict
        ):
            raise ValueError("default_stage_config must be an object")
        if self.editor_hints is not None and not isinstance(self.editor_hints, dict):
            raise ValueError("editor_hints must be an object")
        return self


def normalize_editor_payload(
    *,
    quiz_id: int,
    schema_version: str,
    payload: Any,
) -> QuizEditorDetailResponse:
    raw_payload = payload if isinstance(payload, dict) else {}
    raw_questions = raw_payload.get("questions")
    if not isinstance(raw_questions, list):
        raw_questions = raw_payload.get("stages")
    if not isinstance(raw_questions, list):
        raw_questions = []

    normalized_questions: list[EditorQuestion] = []
    for index, raw_question in enumerate(raw_questions):
        question_dict = _as_question_dict(raw_question)
        question_type = _clean_text(
            question_dict.get("type") or question_dict.get("plugin_id"),
            "slide",
        )
        question_id = _clean_text(
            question_dict.get("question_id") or question_dict.get("stage_id"),
            f"question-{index + 1}",
        )

        raw_spec = question_dict.get("spec")
        if isinstance(raw_spec, dict):
            spec = deepcopy(raw_spec)
        else:
            plugin_spec = question_dict.get("plugin_spec")
            if isinstance(plugin_spec, dict):
                spec = deepcopy(plugin_spec)
            else:
                spec = _normalize_legacy_spec(question_dict)

        title = _clean_text(question_dict.get("title") or question_dict.get("text"))
        if not title and isinstance(spec, dict):
            content = spec.get("content")
            if isinstance(content, dict):
                title = _clean_text(content.get("title"))
        if not title:
            title = _default_title(question_type, index)

        normalized_questions.append(
            EditorQuestion(
                question_id=question_id,
                type=question_type,
                title=title,
                spec=spec,
            )
        )

    normalized_questions = _dedupe_question_ids(normalized_questions)
    description = raw_payload.get("description")
    if description is not None:
        description = _clean_text(description) or None
    else:
        description = None

    title = _clean_text(raw_payload.get("title"), "Untitled quiz")

    return QuizEditorDetailResponse(
        id=quiz_id,
        quiz_id=quiz_id,
        schema_version=_clean_text(
            raw_payload.get("schema_version") or schema_version, "v1"
        ),
        title=title,
        description=description,
        questions=normalized_questions,
    )


def to_storage_payload(payload: QuizEditorPayload) -> dict[str, Any]:
    """Return canonical persisted payload from editor model."""
    return {
        "schema_version": payload.schema_version,
        "title": payload.title,
        "description": payload.description,
        "questions": [question.model_dump() for question in payload.questions],
    }
