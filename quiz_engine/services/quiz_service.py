"""Quiz service layer."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from quiz_engine.models.quiz import Quiz
from quiz_engine.repositories.quiz_repository import QuizRepository
from quiz_engine.schemas.quiz_schemas import QuizCreateRequest


class QuizService:
    def __init__(self, repository: QuizRepository | None = None) -> None:
        self._repository = repository or QuizRepository()

    def create_quiz(
        self, session: Session, *, user_id: int, payload: QuizCreateRequest
    ) -> Quiz:
        payload_dict = payload.model_dump()
        return self._repository.create(
            session,
            schema_version=payload.schema_version,
            payload=payload_dict,
            created_by_user_id=user_id,
        )

    def list_quizzes(self, session: Session, *, user_id: int) -> list[Quiz]:
        return self._repository.list_by_user(session, user_id=user_id)

    def get_quiz_detail(self, session: Session, *, user_id: int, quiz_id: int) -> Quiz:
        quiz = self._repository.get_by_id_for_user(
            session, quiz_id=quiz_id, user_id=user_id
        )
        if quiz is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )
        return quiz
