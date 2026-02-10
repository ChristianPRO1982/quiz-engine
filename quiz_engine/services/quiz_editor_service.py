"""Service layer for quiz editor payload load/save."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from quiz_engine.models.quiz import Quiz
from quiz_engine.repositories.quiz_repository import QuizRepository
from quiz_engine.schemas.quiz_editor_schemas import (
    QuizEditorDetailResponse,
    QuizEditorPayload,
    normalize_editor_payload,
    to_storage_payload,
)


class QuizEditorService:
    def __init__(self, repository: QuizRepository | None = None) -> None:
        self._repository = repository or QuizRepository()

    def create_quiz(self, session: Session, *, user_id: int) -> Quiz:
        payload = {
            "schema_version": "v1",
            "title": "Untitled quiz",
            "description": None,
            "questions": [],
        }
        return self._repository.create(
            session,
            schema_version="v1",
            payload=payload,
            created_by_user_id=user_id,
        )

    def get_editor_payload(
        self, session: Session, *, user_id: int, quiz_id: int
    ) -> QuizEditorDetailResponse:
        quiz = self._get_quiz_or_404(session, user_id=user_id, quiz_id=quiz_id)
        return normalize_editor_payload(
            quiz_id=quiz.id,
            schema_version=quiz.schema_version,
            payload=quiz.payload,
        )

    def save_editor_payload(
        self,
        session: Session,
        *,
        user_id: int,
        quiz_id: int,
        payload: QuizEditorPayload,
    ) -> QuizEditorDetailResponse:
        quiz = self._get_quiz_or_404(session, user_id=user_id, quiz_id=quiz_id)
        canonical_payload = to_storage_payload(payload)
        updated = self._repository.update_payload(
            session,
            quiz=quiz,
            schema_version=payload.schema_version,
            payload=canonical_payload,
        )
        return normalize_editor_payload(
            quiz_id=updated.id,
            schema_version=updated.schema_version,
            payload=updated.payload,
        )

    def _get_quiz_or_404(self, session: Session, *, user_id: int, quiz_id: int) -> Quiz:
        quiz = self._repository.get_by_id_for_user(
            session, quiz_id=quiz_id, user_id=user_id
        )
        if quiz is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found",
            )
        return quiz
