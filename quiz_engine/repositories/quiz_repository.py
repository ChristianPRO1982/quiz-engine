"""Repository for quiz persistence."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from quiz_engine.models.quiz import Quiz
from quiz_engine.models.session import Player
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.stage_event import StageEvent
from quiz_engine.models.stage_outcome import StageOutcomeRecord


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

    def get_by_id(self, session: Session, *, quiz_id: int) -> Quiz | None:
        stmt = select(Quiz).where(Quiz.id == quiz_id)
        return session.execute(stmt).scalar_one_or_none()

    def update_payload(
        self,
        session: Session,
        *,
        quiz: Quiz,
        schema_version: str,
        payload: dict,
    ) -> Quiz:
        quiz.schema_version = schema_version
        quiz.payload = payload
        session.add(quiz)
        session.commit()
        session.refresh(quiz)
        return quiz

    def delete_by_id_for_user(
        self,
        session: Session,
        *,
        quiz_id: int,
        user_id: int,
    ) -> bool:
        quiz = self.get_by_id_for_user(session, quiz_id=quiz_id, user_id=user_id)
        if quiz is None:
            return False

        session_ids = list(
            session.execute(
                select(SessionModel.id).where(SessionModel.quiz_id == quiz_id)
            ).scalars()
        )
        if session_ids:
            session.execute(
                delete(StageEvent).where(StageEvent.session_id.in_(session_ids))
            )
            session.execute(
                delete(StageOutcomeRecord).where(
                    StageOutcomeRecord.session_id.in_(session_ids)
                )
            )
            session.execute(delete(Player).where(Player.session_id.in_(session_ids)))
            session.execute(delete(SessionModel).where(SessionModel.id.in_(session_ids)))

        session.delete(quiz)
        session.commit()
        return True
