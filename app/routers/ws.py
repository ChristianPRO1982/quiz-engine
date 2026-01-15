from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.models import Answer, Player, Session as DbSession
from app.db.session import SessionLocal
from app.routers.sessions import live_sessions
from app.services.live_state import (
    PHASE_ENDED,
    PHASE_LOBBY,
    PHASE_QUESTION,
    PHASE_REVEAL,
    PHASE_TRANSITION,
)
from app.services.ws_manager import ConnectionManager


router = APIRouter()
manager = ConnectionManager()


def build_session_state_event(session_code: str, state) -> dict:
    return {
        "type": "SESSION_STATE",
        "payload": {
            "session_code": session_code,
            "phase": state.phase,
            "current_question_index": state.current_question_index,
            "locked": state.locked,
            "players_count": state.players_count,
        },
    }


def build_question_event(session_code: str, state) -> dict | None:
    question = state.current_question()
    if not question:
        return None
    return {
        "type": "QUESTION",
        "payload": {
            "session_code": session_code,
            "question": {
                "id": question.id,
                "index": question.index,
                "kind": question.kind,
                "prompt": question.prompt,
                "media": question.media,
                "choices": question.choices,
                "config": question.config,
            },
            "state": {
                "phase": state.phase,
                "locked": state.locked,
                "ends_at": None,
            },
        },
    }


def build_stats_event(session_code: str, state) -> dict | None:
    question = state.current_question()
    if not question:
        return None
    stats = state.answers_by_question.get(question.id, {})
    return {
        "type": "STATS",
        "payload": {
            "session_code": session_code,
            "question_id": question.id,
            "total_answers": sum(stats.values()),
            "by_choice": [
                {"choice_id": key, "count": value} for key, value in stats.items()
            ],
        },
    }


def error_event(code: str, message: str) -> dict:
    return {"type": "ERROR", "payload": {"code": code, "message": message}}


async def send_state(session_code: str, state) -> None:
    await manager.broadcast(session_code, build_session_state_event(session_code, state))
    question_event = build_question_event(session_code, state)
    if question_event:
        await manager.broadcast(session_code, question_event)
    stats_event = build_stats_event(session_code, state)
    if stats_event:
        await manager.broadcast(session_code, stats_event)


@router.websocket("/ws/host/{session_code}")
async def host_ws(websocket: WebSocket, session_code: str, token: str):
    db: Session = SessionLocal()
    try:
        session = db.query(DbSession).filter(DbSession.session_code == session_code).first()
        if not session or not verify_token(token, session.host_token_hash):
            await websocket.accept()
            await websocket.send_json(error_event("HOST_TOKEN_INVALID", "Invalid host token."))
            await websocket.close(code=1008)
            return

        await manager.connect_host(session_code, websocket)
        state = live_sessions.get(session_code)
        if state:
            await send_state(session_code, state)

        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            state = live_sessions.get(session_code)
            if not state:
                await websocket.send_json(error_event("SESSION_NOT_FOUND", "Session not found."))
                continue

            if event_type == "HOST_NEXT":
                if state.phase == PHASE_ENDED:
                    await websocket.send_json(error_event("SESSION_ENDED", "Session already ended."))
                    continue
                next_index = state.current_question_index + 1
                if next_index >= len(state.questions):
                    state.phase = PHASE_ENDED
                    state.locked = True
                    session.status = PHASE_ENDED
                    session.ended_at = datetime.utcnow()
                    db.commit()
                else:
                    state.current_question_index = next_index
                    state.phase = PHASE_QUESTION
                    state.locked = False
                    session.status = PHASE_QUESTION
                    db.commit()
                await send_state(session_code, state)

            elif event_type == "HOST_REVEAL":
                if state.phase != PHASE_QUESTION:
                    await websocket.send_json(error_event("INVALID_PHASE", "Not in question phase."))
                    continue
                state.phase = PHASE_REVEAL
                state.locked = True
                session.status = PHASE_REVEAL
                db.commit()
                await send_state(session_code, state)

            elif event_type == "HOST_END":
                state.phase = PHASE_ENDED
                state.locked = True
                session.status = PHASE_ENDED
                session.ended_at = datetime.utcnow()
                db.commit()
                await send_state(session_code, state)

            else:
                await websocket.send_json(error_event("UNKNOWN_EVENT", "Unknown host event."))
    except WebSocketDisconnect:
        manager.disconnect_host(session_code)
    finally:
        db.close()


@router.websocket("/ws/player/{session_code}")
async def player_ws(websocket: WebSocket, session_code: str, player_id: int):
    db: Session = SessionLocal()
    try:
        player = (
            db.query(Player)
            .filter(Player.id == player_id)
            .join(DbSession, Player.session_id == DbSession.id)
            .filter(DbSession.session_code == session_code)
            .first()
        )
        if not player:
            await websocket.accept()
            await websocket.send_json(error_event("PLAYER_INVALID", "Invalid player."))
            await websocket.close(code=1008)
            return

        await manager.connect_player(session_code, websocket)
        state = live_sessions.get(session_code)
        if state:
            await send_state(session_code, state)

        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            payload = data.get("payload") or {}
            state = live_sessions.get(session_code)
            if not state:
                await websocket.send_json(error_event("SESSION_NOT_FOUND", "Session not found."))
                continue

            if event_type == "PLAYER_ANSWER":
                if state.phase != PHASE_QUESTION or state.locked:
                    await websocket.send_json(error_event("ANSWER_LOCKED", "Answers are locked."))
                    continue

                question = state.current_question()
                if not question:
                    await websocket.send_json(error_event("NO_QUESTION", "No active question."))
                    continue

                answer_payload = payload.get("answer") or {}
                choice_id = answer_payload.get("choice_id")
                if not choice_id:
                    await websocket.send_json(error_event("INVALID_ANSWER", "Missing choice."))
                    continue

                existing = (
                    db.query(Answer)
                    .filter(
                        Answer.session_id == state.session_id,
                        Answer.question_id == question.id,
                        Answer.player_id == player_id,
                    )
                    .first()
                )
                if existing:
                    await websocket.send_json(error_event("ALREADY_ANSWERED", "Already answered."))
                    continue

                answer = Answer(
                    session_id=state.session_id,
                    question_id=question.id,
                    player_id=player_id,
                    choice_id=choice_id,
                )
                db.add(answer)
                db.commit()

                stats = state.answers_by_question.setdefault(question.id, {})
                stats[choice_id] = stats.get(choice_id, 0) + 1
                stats_event = build_stats_event(session_code, state)
                if stats_event:
                    await manager.broadcast(session_code, stats_event)
            else:
                await websocket.send_json(error_event("UNKNOWN_EVENT", "Unknown player event."))
    except WebSocketDisconnect:
        manager.disconnect_player(session_code, websocket)
    finally:
        db.close()
