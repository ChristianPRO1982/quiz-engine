"""Service layer for read-only quiz preview rendering."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from quiz_engine.models.quiz import Quiz
from quiz_engine.schemas.quiz_editor_schemas import normalize_editor_payload
from quiz_engine.services.plugin_registry_service import PluginRegistryService
from quiz_engine.services.quiz_service import QuizService


class QuizPreviewService:
    """Load quiz data and build deterministic preview stages."""

    def __init__(
        self,
        *,
        quiz_service: QuizService | None = None,
        plugin_registry_service: PluginRegistryService | None = None,
    ) -> None:
        self._quiz_service = quiz_service or QuizService()
        self._plugin_registry_service = (
            plugin_registry_service or PluginRegistryService()
        )

    def load_quiz(self, session: Session, *, user_id: int, quiz_id: int) -> Quiz:
        return self._quiz_service.get_quiz_detail(
            session,
            user_id=user_id,
            quiz_id=quiz_id,
        )

    def build_preview_payload(self, request: Request, *, quiz: Quiz) -> dict[str, Any]:
        editor_payload = normalize_editor_payload(
            quiz_id=quiz.id,
            schema_version=quiz.schema_version,
            payload=quiz.payload,
        )

        stages: list[dict[str, Any]] = []
        for stage_index, question in enumerate(editor_payload.questions):
            view_model = self._plugin_registry_service.build_preview_view_model(
                request,
                quiz_id=quiz.id,
                stage_index=stage_index,
                stage_id=question.question_id,
                plugin_id=question.type,
                stage_title=question.title,
                plugin_spec=question.spec,
            )
            stages.append(
                {
                    "stage_id": question.question_id,
                    "stage_index": stage_index,
                    "plugin_id": question.type,
                    "title": question.title,
                    "view_model": view_model,
                }
            )

        return {
            "quiz_id": editor_payload.quiz_id,
            "schema_version": editor_payload.schema_version,
            "title": editor_payload.title,
            "description": editor_payload.description,
            "stages": stages,
        }
