"""Repository for quiz persistence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from quiz_engine.models.quiz import Quiz


class QuizRepository:
    def create(
        self,
        session: Session,
        *,
        schema_version: str,
        payload: dict,
        created_by_user_id: int,
    ) -> Quiz:
        quiz = Quiz(
            schema_version=schema_version,
            payload=payload,
            created_by_user_id=created_by_user_id,
        )
        session.add(quiz)
        session.commit()
        session.refresh(quiz)
        return quiz

    def list_by_user(self, session: Session, *, user_id: int) -> list[Quiz]:
        stmt = (
            select(Quiz)
            .where(Quiz.created_by_user_id == user_id)
            .order_by(Quiz.created_at.desc(), Quiz.id.desc())
        )
        return list(session.execute(stmt).scalars())

    def get_by_id_for_user(
        self, session: Session, *, quiz_id: int, user_id: int
    ) -> Quiz | None:
        stmt = select(Quiz).where(
            Quiz.id == quiz_id, Quiz.created_by_user_id == user_id
        )
        return session.execute(stmt).scalar_one_or_none()
