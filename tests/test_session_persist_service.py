"""Unit tests for SessionPersistService edge paths."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import quiz_engine.models  # noqa: F401
from quiz_engine.contracts.runtime_models import StageOutcome
from quiz_engine.db.base import Base
from quiz_engine.db.engine import get_engine
from quiz_engine.db.session import _sessionmaker, get_session
from quiz_engine.models.quiz import Quiz
from quiz_engine.models.session import Session as SessionModel
from quiz_engine.models.user import User
from quiz_engine.services.session_persist_service import SessionPersistService


def _setup_db(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "persist.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    get_engine.cache_clear()
    _sessionmaker.cache_clear()
    Base.metadata.create_all(get_engine())


def _seed_user_and_quiz(session: Session) -> tuple[User, Quiz]:
    user = User(subject="owner")
    quiz = Quiz(
        schema_version="v1",
        payload={"schema_version": "v1", "title": "Persist", "questions": []},
        created_by_user_id=None,
    )
    session.add_all([user, quiz])
    session.commit()
    session.refresh(user)
    session.refresh(quiz)
    quiz.created_by_user_id = user.id
    session.add(quiz)
    session.commit()
    return user, quiz


def test_create_session_retries_when_candidate_already_exists(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = SessionPersistService()

    with get_session() as session:
        user, quiz = _seed_user_and_quiz(session)

        session.add(
            SessionModel(
                session_code="AAAAAA",
                quiz_id=quiz.id,
                host_user_id=user.id,
                state="LOBBY",
            )
        )
        session.commit()

        candidates = iter(["AAAAAA", "BBBBBB"])
        monkeypatch.setattr(
            service,
            "build_session_code_candidate",
            lambda: next(candidates),
        )

        created = service.create_session(
            session,
            quiz_id=quiz.id,
            host_user_id=user.id,
            max_attempts=2,
        )

    assert created.session_code == "BBBBBB"


def test_create_session_retries_after_integrity_error(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = SessionPersistService()

    with get_session() as session:
        user, quiz = _seed_user_and_quiz(session)

        candidates = iter(["CCCCCC", "DDDDDD"])
        monkeypatch.setattr(
            service,
            "build_session_code_candidate",
            lambda: next(candidates),
        )

        original_commit = session.commit
        state = {"count": 0}

        def flaky_commit() -> None:
            state["count"] += 1
            if state["count"] == 1:
                raise IntegrityError("insert", {}, Exception("boom"))
            original_commit()

        monkeypatch.setattr(session, "commit", flaky_commit)

        created = service.create_session(
            session,
            quiz_id=quiz.id,
            host_user_id=user.id,
            max_attempts=2,
        )

    assert created.session_code == "DDDDDD"


def test_create_session_raises_when_generation_is_exhausted(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = SessionPersistService()

    with get_session() as session:
        user, quiz = _seed_user_and_quiz(session)

        session.add(
            SessionModel(
                session_code="EEEEEE",
                quiz_id=quiz.id,
                host_user_id=user.id,
                state="LOBBY",
            )
        )
        session.commit()

        monkeypatch.setattr(service, "build_session_code_candidate", lambda: "EEEEEE")

        with pytest.raises(RuntimeError):
            service.create_session(
                session,
                quiz_id=quiz.id,
                host_user_id=user.id,
                max_attempts=1,
            )


def test_get_session_set_state_and_player_lifecycle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = SessionPersistService()

    with get_session() as session:
        user, quiz = _seed_user_and_quiz(session)
        created = service.create_session(session, quiz_id=quiz.id, host_user_id=user.id)

        assert service.get_session_by_code(session, session_code="NOPE") is None
        by_code = service.get_session_by_code(
            session,
            session_code=created.session_code,
        )
        assert by_code is not None

        with pytest.raises(ValueError):
            service.set_session_state(session, session_id=999999, state="ENDED")

        running = service.set_session_state(
            session,
            session_id=created.id,
            state="RUNNING",
        )
        assert running.state == "RUNNING"

        ended = service.set_session_state(session, session_id=created.id, state="ENDED")
        assert ended.state == "ENDED"
        assert ended.ended_at is not None

        player = service.add_player(session, session_id=created.id, nickname="Alice")
        players = service.list_active_players(session, session_id=created.id)
        assert [item.nickname for item in players] == ["Alice"]

        service.mark_player_left(session, player_id=player.id)
        service.mark_player_left(session, player_id=999999)
        players_after_leave = service.list_active_players(
            session,
            session_id=created.id,
        )
        assert players_after_leave == []


def test_record_stage_event_and_outcome(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _setup_db(tmp_path, monkeypatch)
    service = SessionPersistService()

    with get_session() as session:
        user, quiz = _seed_user_and_quiz(session)
        created = service.create_session(session, quiz_id=quiz.id, host_user_id=user.id)

        event = service.record_stage_event(
            session,
            session_id=created.id,
            stage_id="stage-1",
            stage_index=0,
            payload={"event": "opened"},
        )
        assert event.payload["event"] == "opened"

        outcome = StageOutcome(
            session_id=str(created.id),
            stage_id="stage-1",
            stage_index=0,
            plugin_id="slide",
            completed_at=datetime.now(UTC),
        )
        stored = service.record_stage_outcome(
            session,
            session_id=created.id,
            outcome=outcome,
        )

    assert stored.stage_id == "stage-1"
