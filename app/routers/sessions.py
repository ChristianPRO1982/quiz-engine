from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import generate_host_token, hash_token
from app.db.models import Answer, Player, Quiz, Session as DbSession
from app.db.session import get_db
from app.schemas import (
    SessionJoinRequest,
    SessionJoinResponse,
    SessionReviewAnswer,
    SessionReviewResponse,
    SessionStartRequest,
    SessionStartResponse,
)
from app.services.live_state import LiveSessionState, generate_session_code, quiz_to_live_questions


router = APIRouter(prefix="/sessions", tags=["sessions"])


live_sessions: Dict[str, LiveSessionState] = {}


@router.post("/start", response_model=SessionStartResponse)
def start_session(payload: SessionStartRequest, db: Session = Depends(get_db)):
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="QUIZ_NOT_FOUND")

    session_code = generate_session_code()
    while db.query(DbSession).filter(DbSession.session_code == session_code).first():
        session_code = generate_session_code()

    host_token = generate_host_token()
    session = DbSession(
        quiz_id=quiz.id,
        session_code=session_code,
        host_token_hash=hash_token(host_token),
        status="LOBBY",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    live_sessions[session_code] = LiveSessionState(
        session_id=session.id,
        session_code=session_code,
        quiz_id=quiz.id,
        questions=quiz_to_live_questions(quiz),
    )

    join_url = f"{settings.base_url}/join/{session_code}"
    return SessionStartResponse(session_code=session_code, host_token=host_token, join_url=join_url)


@router.post("/{session_code}/join", response_model=SessionJoinResponse)
def join_session(
    session_code: str, payload: SessionJoinRequest, db: Session = Depends(get_db)
):
    session = db.query(DbSession).filter(DbSession.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    if session.status == "ENDED":
        raise HTTPException(status_code=409, detail="SESSION_ALREADY_ENDED")

    player = Player(session_id=session.id, nickname=payload.nickname)
    db.add(player)
    db.commit()
    db.refresh(player)

    live_state = live_sessions.get(session_code)
    if live_state:
        live_state.players_count += 1

    return SessionJoinResponse(player_id=player.id)


@router.get("/{session_code}/review", response_model=SessionReviewResponse)
def review_session(session_code: str, db: Session = Depends(get_db)):
    session = db.query(DbSession).filter(DbSession.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    quiz = session.quiz
    answers = db.query(Answer).filter(Answer.session_id == session.id).all()
    stats_map: Dict[int, Dict[int, int]] = {}
    for answer in answers:
        if answer.question_id not in stats_map:
            stats_map[answer.question_id] = {}
        if answer.choice_id:
            stats_map[answer.question_id][answer.choice_id] = (
                stats_map[answer.question_id].get(answer.choice_id, 0) + 1
            )

    answer_payload = []
    for question in quiz.questions:
        counts = stats_map.get(question.id, {})
        by_choice = [{"choice_id": key, "count": value} for key, value in counts.items()]
        answer_payload.append(
            SessionReviewAnswer(
                question_id=question.id,
                total_answers=sum(counts.values()),
                by_choice=by_choice,
            )
        )

    return SessionReviewResponse(
        session_code=session_code,
        quiz=quiz,
        players_count=len(session.players),
        answers=answer_payload,
    )
