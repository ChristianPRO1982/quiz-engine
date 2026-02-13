"""Database persistence helpers for live sessions."""

from __future__ import annotations

from datetime import UTC, datetime
from secrets import choice
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from quiz_engine.contracts.runtime_models import StageOutcome
from quiz_engine.contracts.serialization import ensure_json_like
from quiz_engine.models.session import Player
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.stage_event import StageEvent
from quiz_engine.models.stage_outcome import StageOutcomeRecord


class SessionPersistService:
    """Persistence layer for session/player/stage records."""

    SESSION_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    SESSION_CODE_LENGTH = 6

    def build_session_code_candidate(self) -> str:
        return "".join(
            choice(self.SESSION_CODE_ALPHABET) for _ in range(self.SESSION_CODE_LENGTH)
        )

    def create_session(
        self,
        session: Session,
        *,
        quiz_id: int,
        host_user_id: int | None,
        max_attempts: int = 20,
    ) -> SessionModel:
        for _ in range(max_attempts):
            session_code = self.build_session_code_candidate()
            existing = session.execute(
                select(SessionModel.id).where(SessionModel.session_code == session_code)
            ).scalar_one_or_none()
            if existing is not None:
                continue

            model = SessionModel(
                session_code=session_code,
                quiz_id=quiz_id,
                host_user_id=host_user_id,
                state="LOBBY",
            )
            session.add(model)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                continue
            session.refresh(model)
            return model

        raise RuntimeError("Unable to generate a unique session code.")

    def get_session_by_code(
        self,
        session: Session,
        *,
        session_code: str,
    ) -> SessionModel | None:
        stmt = select(SessionModel).where(SessionModel.session_code == session_code)
        return session.execute(stmt).scalar_one_or_none()

    def set_session_state(
        self,
        session: Session,
        *,
        session_id: int,
        state: str,
    ) -> SessionModel:
        model = session.get(SessionModel, session_id)
        if model is None:
            raise ValueError("Session not found.")
        model.state = state
        if state == "ENDED" and model.ended_at is None:
            model.ended_at = datetime.now(UTC)
        session.add(model)
        session.commit()
        session.refresh(model)
        return model

    def add_player(
        self,
        session: Session,
        *,
        session_id: int,
        nickname: str,
        user_id: int | None = None,
        is_guest: bool = True,
    ) -> Player:
        model = Player(
            session_id=session_id,
            user_id=user_id,
            player_code=uuid4().hex,
            nickname=nickname,
            is_guest=is_guest,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model

    def mark_player_left(self, session: Session, *, player_id: int) -> None:
        model = session.get(Player, player_id)
        if model is None:
            return
        model.left_at = datetime.now(UTC)
        session.add(model)
        session.commit()

    def list_active_players(self, session: Session, *, session_id: int) -> list[Player]:
        stmt = (
            select(Player)
            .where(Player.session_id == session_id, Player.left_at.is_(None))
            .order_by(Player.joined_at.asc(), Player.id.asc())
        )
        return list(session.execute(stmt).scalars())

    def record_stage_event(
        self,
        session: Session,
        *,
        session_id: int,
        stage_id: str,
        stage_index: int,
        payload: dict[str, Any],
    ) -> StageEvent:
        ensure_json_like(payload, "payload")
        model = StageEvent(
            session_id=session_id,
            stage_id=stage_id,
            stage_index=stage_index,
            payload=payload,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model

    def record_stage_outcome(
        self,
        session: Session,
        *,
        session_id: int,
        outcome: StageOutcome,
    ) -> StageOutcomeRecord:
        payload = outcome.to_transport_dict()
        ensure_json_like(payload, "outcome")
        model = StageOutcomeRecord(
            session_id=session_id,
            stage_id=outcome.stage_id,
            stage_index=outcome.stage_index,
            payload=payload,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model
