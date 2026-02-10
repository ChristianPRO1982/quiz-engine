"""Session-backed quiz draft service."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from fastapi import Request

from quiz_engine.middleware.session import get_session_data
from quiz_engine.schemas.quiz_schemas import QuizCreateRequest

SESSION_QUIZ_DRAFT_KEY = "quiz_draft"


class QuizDraftService:
    """Manage multi-step quiz drafts stored in session."""

    def get_draft(self, request: Request) -> dict[str, Any]:
        session_data = get_session_data(request)
        raw = session_data.get(SESSION_QUIZ_DRAFT_KEY)
        if not isinstance(raw, dict):
            draft = self._blank_draft()
            session_data[SESSION_QUIZ_DRAFT_KEY] = draft
            return draft

        normalized = self._normalize_draft(raw)
        if normalized != raw:
            session_data[SESSION_QUIZ_DRAFT_KEY] = normalized
        return normalized

    def clear_draft(self, request: Request) -> None:
        get_session_data(request).pop(SESSION_QUIZ_DRAFT_KEY, None)

    def save_metadata(
        self, request: Request, *, title: str, description: str | None
    ) -> dict[str, Any]:
        draft = deepcopy(self.get_draft(request))
        draft["title"] = title.strip()
        cleaned_description = (description or "").strip()
        draft["description"] = cleaned_description
        self._persist(request, draft)
        return draft

    def add_question(
        self, request: Request, *, text: str, choices: list[str]
    ) -> dict[str, Any]:
        draft = deepcopy(self.get_draft(request))
        draft["questions"].append(
            {
                "type": "qcm_single",
                "text": text.strip(),
                "choices": [choice.strip() for choice in choices],
            }
        )
        self._persist(request, draft)
        return draft

    def duplicate_from_payload(self, request: Request, payload: dict[str, Any]) -> None:
        draft = self._blank_draft()
        draft["schema_version"] = str(payload.get("schema_version") or "v1")
        draft["title"] = str(payload.get("title") or "").strip()
        draft["description"] = str(payload.get("description") or "").strip()

        raw_questions = payload.get("questions")
        if isinstance(raw_questions, list):
            for raw_question in raw_questions:
                if not isinstance(raw_question, dict):
                    continue
                text = str(raw_question.get("text") or "").strip()
                raw_choices = raw_question.get("choices")
                if not isinstance(raw_choices, list):
                    continue
                choices = [
                    str(choice).strip() for choice in raw_choices if str(choice).strip()
                ]
                if text and len(choices) >= 2:
                    draft["questions"].append(
                        {"type": "qcm_single", "text": text, "choices": choices}
                    )

        self._persist(request, draft)

    def build_create_request(self, request: Request) -> QuizCreateRequest:
        draft = self.get_draft(request)
        description = str(draft.get("description") or "").strip() or None
        return QuizCreateRequest(
            schema_version=str(draft.get("schema_version") or "v1"),
            title=str(draft.get("title") or "").strip(),
            description=description,
            questions=list(draft.get("questions") or []),
        )

    def _persist(self, request: Request, draft: dict[str, Any]) -> None:
        draft["updated_at"] = self._now_iso()
        get_session_data(request)[SESSION_QUIZ_DRAFT_KEY] = self._normalize_draft(draft)

    def _blank_draft(self) -> dict[str, Any]:
        return {
            "schema_version": "v1",
            "title": "",
            "description": "",
            "questions": [],
            "updated_at": self._now_iso(),
        }

    def _normalize_draft(self, raw: dict[str, Any]) -> dict[str, Any]:
        questions: list[dict[str, Any]] = []
        raw_questions = raw.get("questions")
        if isinstance(raw_questions, list):
            for raw_question in raw_questions:
                if not isinstance(raw_question, dict):
                    continue
                text = str(raw_question.get("text") or "").strip()
                raw_choices = raw_question.get("choices")
                if not isinstance(raw_choices, list):
                    continue
                choices = [
                    str(choice).strip() for choice in raw_choices if str(choice).strip()
                ]
                question_type = str(raw_question.get("type") or "qcm_single")
                if text and len(choices) >= 2 and question_type == "qcm_single":
                    questions.append(
                        {
                            "type": "qcm_single",
                            "text": text,
                            "choices": choices,
                        }
                    )

        return {
            "schema_version": str(raw.get("schema_version") or "v1"),
            "title": str(raw.get("title") or "").strip(),
            "description": str(raw.get("description") or "").strip(),
            "questions": questions,
            "updated_at": str(raw.get("updated_at") or self._now_iso()),
        }

    def _now_iso(self) -> str:
        return datetime.now(UTC).isoformat()
