"""Live session WebSocket gateway."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from quiz_engine.db.session import get_session
from quiz_engine.repositories.quiz_repository import QuizRepository
from quiz_engine.services.session_live_service import (
    LiveSessionState,
    SessionLiveService,
)
from quiz_engine.services.session_persist_service import SessionPersistService
from quiz_engine.services.stage_orchestrator_service import StageOrchestratorService
from quiz_engine.ws.messages import build_envelope

router = APIRouter()
quiz_repository = QuizRepository()
session_persist_service = SessionPersistService()
stage_orchestrator_service = StageOrchestratorService(session_persist_service)


async def _send_error(websocket: WebSocket, message: str) -> None:
    await websocket.send_json(build_envelope("ERROR", {"message": message}))


async def _hydrate_live_session(
    websocket: WebSocket,
    *,
    session_code: str,
) -> LiveSessionState | None:
    live_service: SessionLiveService = websocket.app.state.session_live_service
    live = await live_service.get_session(session_code)
    if live is not None:
        return live

    with get_session() as session:
        db_session = session_persist_service.get_session_by_code(
            session,
            session_code=session_code,
        )
        if db_session is None or db_session.quiz_id is None:
            return None

        quiz = quiz_repository.get_by_id(session, quiz_id=db_session.quiz_id)
        if quiz is None:
            return None

        stages = stage_orchestrator_service.build_stages_from_quiz_payload(quiz.payload)
        live = await live_service.create_or_replace_session(
            session_id=db_session.id,
            quiz_id=db_session.quiz_id,
            session_code=db_session.session_code,
            lifecycle_state=db_session.state,
            stages=stages,
        )

        for player in session_persist_service.list_active_players(
            session,
            session_id=db_session.id,
        ):
            await live_service.upsert_player(
                session_code,
                player_id=player.id,
                nickname=player.nickname,
            )

    return live


async def _broadcast_snapshot(
    session_code: str,
    live_service: SessionLiveService,
) -> None:
    snapshot = await live_service.lobby_snapshot(session_code)
    await live_service.broadcast(
        session_code,
        build_envelope("LOBBY_SNAPSHOT", snapshot),
        audience="ALL",
    )


async def _broadcast_stage_frames(
    session_code: str,
    live_service: SessionLiveService,
    frames,
) -> None:
    for frame in frames:
        await live_service.broadcast(
            session_code,
            build_envelope("PLUGIN_FRAME", frame.to_transport_dict()),
            audience="ALL",
        )


async def _end_session(
    session_code: str,
    live_service: SessionLiveService,
) -> None:
    live = await live_service.get_session(session_code)
    if live is None:
        return

    if live.lifecycle_state != "ENDED":
        await live_service.transition_state(session_code, new_state="ENDED")
        with get_session() as session:
            session_persist_service.set_session_state(
                session,
                session_id=live.session_id,
                state="ENDED",
            )

    await live_service.broadcast(
        session_code,
        build_envelope("SESSION_STATE_CHANGED", {"session_state": "ENDED"}),
        audience="ALL",
    )
    await _broadcast_snapshot(session_code, live_service)


@router.websocket("/ws/s/{session_code}")
async def session_gateway(websocket: WebSocket, session_code: str) -> None:
    role = str(websocket.query_params.get("role", "player")).strip().lower()

    await websocket.accept()

    if role not in {"host", "player"}:
        await _send_error(websocket, "Invalid role.")
        await websocket.close(code=1008)
        return

    live_service: SessionLiveService = websocket.app.state.session_live_service
    plugin_registry = websocket.app.state.plugin_registry

    live = await _hydrate_live_session(websocket, session_code=session_code)
    if live is None:
        await _send_error(websocket, "Session not found.")
        await websocket.close(code=1008)
        return

    joined_player_id: int | None = None

    if role == "host":
        await live_service.attach_host_socket(session_code, websocket)
        await websocket.send_json(
            build_envelope("SESSION_CREATED", {"session_code": session_code})
        )
    else:
        await live_service.attach_pending_player_socket(session_code, websocket)

    snapshot = await live_service.lobby_snapshot(session_code)
    await websocket.send_json(build_envelope("LOBBY_SNAPSHOT", snapshot))

    try:
        while True:
            message = await websocket.receive_json()
            if not isinstance(message, dict):
                await _send_error(websocket, "Invalid message envelope.")
                continue

            event_type = message.get("type")
            payload = message.get("payload", {})
            if not isinstance(event_type, str) or not isinstance(payload, dict):
                await _send_error(websocket, "Invalid message envelope.")
                continue

            if event_type == "CONNECT":
                await websocket.send_json(
                    build_envelope(
                        "SESSION_STATE_CHANGED",
                        {
                            "session_state": (
                                await live_service.lobby_snapshot(session_code)
                            ).get("session_state", "LOBBY")
                        },
                    )
                )
                continue

            if event_type == "JOIN_SESSION":
                if role != "player":
                    await _send_error(websocket, "Only players can join sessions.")
                    continue
                if joined_player_id is not None:
                    await _send_error(websocket, "Already joined.")
                    continue

                live = await live_service.get_session(session_code)
                if live is None:
                    await _send_error(websocket, "Session not found.")
                    continue
                if live.lifecycle_state == "ENDED":
                    await _send_error(websocket, "Session already ended.")
                    continue

                nickname = str(payload.get("nickname", "")).strip()
                if not nickname:
                    await _send_error(websocket, "Nickname is required.")
                    continue
                nickname = nickname[:32]

                with get_session() as session:
                    db_player = session_persist_service.add_player(
                        session,
                        session_id=live.session_id,
                        nickname=nickname,
                        user_id=None,
                        is_guest=True,
                    )

                joined_player_id = db_player.id
                await live_service.upsert_player(
                    session_code,
                    player_id=db_player.id,
                    nickname=db_player.nickname,
                )
                await live_service.promote_player_socket(
                    session_code,
                    websocket=websocket,
                    player_id=db_player.id,
                )
                await live_service.broadcast(
                    session_code,
                    build_envelope(
                        "PLAYER_JOINED",
                        {
                            "player_id": db_player.id,
                            "nickname": db_player.nickname,
                        },
                    ),
                    audience="ALL",
                )
                await _broadcast_snapshot(session_code, live_service)
                continue

            if event_type == "LEAVE_SESSION":
                if role != "player":
                    await _send_error(websocket, "Only players can leave sessions.")
                    continue
                if joined_player_id is None:
                    continue

                with get_session() as session:
                    session_persist_service.mark_player_left(
                        session,
                        player_id=joined_player_id,
                    )
                await live_service.remove_player(
                    session_code,
                    player_id=joined_player_id,
                )
                await live_service.attach_pending_player_socket(session_code, websocket)
                await live_service.broadcast(
                    session_code,
                    build_envelope("PLAYER_LEFT", {"player_id": joined_player_id}),
                    audience="ALL",
                )
                joined_player_id = None
                await _broadcast_snapshot(session_code, live_service)
                continue

            if event_type == "HOST_START":
                if role != "host":
                    await _send_error(websocket, "Only host can start the session.")
                    continue

                live = await live_service.get_session(session_code)
                if live is None:
                    await _send_error(websocket, "Session not found.")
                    continue

                if live.lifecycle_state == "LOBBY":
                    await live_service.transition_state(
                        session_code,
                        new_state="RUNNING",
                    )
                    with get_session() as session:
                        session_persist_service.set_session_state(
                            session,
                            session_id=live.session_id,
                            state="RUNNING",
                        )
                    await live_service.broadcast(
                        session_code,
                        build_envelope(
                            "SESSION_STATE_CHANGED",
                            {"session_state": "RUNNING"},
                        ),
                        audience="ALL",
                    )

                if live.stage_runner is not None:
                    continue

                with get_session() as session:
                    opened = stage_orchestrator_service.open_stage(
                        session,
                        live_session=live,
                        stage_index=0,
                        plugin_registry=plugin_registry,
                    )

                if opened is None:
                    await _end_session(session_code, live_service)
                    continue

                stage, frames = opened
                await live_service.broadcast(
                    session_code,
                    build_envelope(
                        "STAGE_CHANGED",
                        {
                            "stage_id": stage.stage_id,
                            "stage_index": stage.stage_index,
                        },
                    ),
                    audience="ALL",
                )
                await _broadcast_stage_frames(session_code, live_service, frames)
                continue

            if event_type == "HOST_NEXT_STAGE":
                if role != "host":
                    await _send_error(websocket, "Only host can advance stage.")
                    continue

                live = await live_service.get_session(session_code)
                if live is None:
                    await _send_error(websocket, "Session not found.")
                    continue
                if live.lifecycle_state != "RUNNING":
                    await _send_error(websocket, "Session is not running.")
                    continue

                with get_session() as session:
                    stage_orchestrator_service.close_current_stage(
                        session,
                        live_session=live,
                    )
                    next_index = (
                        live.stage_index if live.stage_index is not None else -1
                    ) + 1
                    opened = stage_orchestrator_service.open_stage(
                        session,
                        live_session=live,
                        stage_index=next_index,
                        plugin_registry=plugin_registry,
                    )

                if opened is None:
                    await _end_session(session_code, live_service)
                    continue

                stage, frames = opened
                await live_service.broadcast(
                    session_code,
                    build_envelope(
                        "STAGE_CHANGED",
                        {
                            "stage_id": stage.stage_id,
                            "stage_index": stage.stage_index,
                        },
                    ),
                    audience="ALL",
                )
                await _broadcast_stage_frames(session_code, live_service, frames)
                continue

            if event_type == "HOST_END":
                if role != "host":
                    await _send_error(websocket, "Only host can end the session.")
                    continue

                live = await live_service.get_session(session_code)
                if live is None:
                    await _send_error(websocket, "Session not found.")
                    continue

                with get_session() as session:
                    stage_orchestrator_service.close_current_stage(
                        session,
                        live_session=live,
                    )

                await _end_session(session_code, live_service)
                continue

            await _send_error(websocket, f"Unsupported event: {event_type}")

    except WebSocketDisconnect:
        pass
    finally:
        if joined_player_id is not None:
            with get_session() as session:
                session_persist_service.mark_player_left(
                    session,
                    player_id=joined_player_id,
                )
            await live_service.remove_player(session_code, player_id=joined_player_id)
            await live_service.broadcast(
                session_code,
                build_envelope("PLAYER_LEFT", {"player_id": joined_player_id}),
                audience="ALL",
            )
            await _broadcast_snapshot(session_code, live_service)

        await live_service.detach_socket(session_code, websocket)
