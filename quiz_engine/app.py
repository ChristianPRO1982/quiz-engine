"""FastAPI application for Sprint 0 realtime lobby."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import qrcode
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from .protocol import (
    ROLE_HOST,
    ROLE_PLAYER,
    EventEnvelope,
    ProtocolError,
    build_event,
    parse_event,
)
from .sessions import Session, SessionState, SessionStore


@dataclass
class ConnectionContext:
    websocket: WebSocket
    role: str
    session_code: str | None = None
    player_id: str | None = None


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.store = SessionStore()

    templates_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def host_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "host.html")

    @app.get("/join/{session_code}", response_class=HTMLResponse, name="join_page")
    async def join_page(request: Request, session_code: str) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "player.html",
            {"session_code": session_code},
        )

    @app.post("/api/sessions")
    async def create_session(request: Request) -> dict[str, Any]:
        store: SessionStore = request.app.state.store
        session = store.create_session()
        join_url = str(request.url_for("join_page", session_code=session.session_code))
        return {
            "schema_version": "1",
            "session_code": session.session_code,
            "join_url": join_url,
        }

    @app.get("/qr/{session_code}.png")
    async def qr_code(session_code: str, request: Request) -> StreamingResponse:
        join_url = str(request.url_for("join_page", session_code=session_code))
        image = qrcode.make(join_url)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="image/png")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        store: SessionStore = websocket.app.state.store
        role = websocket.query_params.get("role", ROLE_PLAYER)
        if role not in {ROLE_HOST, ROLE_PLAYER}:
            role = ROLE_PLAYER

        context = ConnectionContext(websocket=websocket, role=role)
        await _register_connection(store, context, websocket)

        try:
            while True:
                raw = await websocket.receive_json()
                try:
                    event = parse_event(raw)
                except ProtocolError as exc:
                    await websocket.send_json(_error_event(exc, context.session_code))
                    continue

                await _handle_event(store, context, event)
        except WebSocketDisconnect:
            await _handle_disconnect(store, context)

    return app


async def _register_connection(
    store: SessionStore, context: ConnectionContext, websocket: WebSocket
) -> None:
    session_code = websocket.query_params.get("session_code")
    if not session_code:
        return

    session = store.get_session(session_code)
    if not session:
        await websocket.send_json(
            _error_payload(session_code, "invalid_session", "Session not found.")
        )
        return

    context.session_code = session_code
    if context.role == ROLE_HOST:
        session.host_connections.add(websocket)
        await websocket.send_json(_session_status_event(session))
        await websocket.send_json(_lobby_snapshot_event(session))
        return

    await websocket.send_json(_session_status_event(session))


async def _handle_event(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    if context.role == ROLE_HOST:
        await _handle_host_event(store, context, event)
        return

    await _handle_player_event(store, context, event)


async def _handle_host_event(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    if event.type == "create_session":
        session = store.create_session()
        context.session_code = session.session_code
        session.host_connections.add(context.websocket)
        await context.websocket.send_json(
            build_event(
                session.session_code,
                "session_created",
                {"session_code": session.session_code},
            )
        )
        await context.websocket.send_json(_session_status_event(session))
        await context.websocket.send_json(_lobby_snapshot_event(session))
        return

    if event.type not in {
        "host_start",
        "host_end",
        "host_approve_join",
        "host_reject_join",
        "host_kick",
    }:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_role",
                "Host connection cannot send this event.",
            )
        )
        return

    session = store.get_session(event.session_code)
    if not session:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session",
                "Session not found.",
            )
        )
        return

    context.session_code = event.session_code
    session.host_connections.add(context.websocket)

    if event.type == "host_start":
        await _transition_state(
            session,
            context.websocket,
            from_state=SessionState.LOBBY,
            to_state=SessionState.RUNNING,
        )
        return

    if event.type == "host_end":
        await _transition_state(
            session,
            context.websocket,
            from_state=SessionState.RUNNING,
            to_state=SessionState.ENDED,
        )
        return

    if event.type == "host_approve_join":
        await _approve_join(store, session, context.websocket, event)
        return

    if event.type == "host_reject_join":
        await _reject_join(store, session, context.websocket, event)
        return

    await _kick_player(store, session, context.websocket, event)


async def _handle_player_event(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    if event.type not in {"join_session", "leave_session"}:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_role",
                "Player connection cannot send this event.",
            )
        )
        return

    if event.type == "join_session":
        await _join_session(store, context, event)
        return

    await _leave_session(store, context, event)


async def _join_session(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    session = store.get_session(event.session_code)
    if not session:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session",
                "Session not found.",
            )
        )
        return

    if context.player_id and context.player_id not in session.players:
        context.player_id = None
    if context.websocket in session.player_connections:
        stored_id = session.player_connections.get(context.websocket)
        if stored_id not in session.players:
            session.player_connections.pop(context.websocket, None)

    if context.player_id or context.websocket in session.player_connections:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "already_joined",
                "Player already joined.",
            )
        )
        return

    if context.websocket in session.pending_connections:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "join_pending",
                "Join request is already pending.",
            )
        )
        return

    nickname = event.payload["nickname"].strip()
    context.session_code = session.session_code

    if session.state == SessionState.LOBBY:
        player = store.register_player(session, nickname)
        session.player_connections[context.websocket] = player.player_id
        context.player_id = player.player_id
        await context.websocket.send_json(_session_status_event(session))
        await _broadcast(
            session,
            build_event(
                session.session_code,
                "player_joined",
                {"player_id": player.player_id, "nickname": player.nickname},
            ),
        )
        await _broadcast(session, _lobby_snapshot_event(session))
        return

    if session.state == SessionState.RUNNING:
        pending = store.register_pending(session, context.websocket, nickname)
        await context.websocket.send_json(_session_status_event(session))
        await _broadcast_to_hosts(
            session,
            build_event(
                session.session_code,
                "join_requested",
                {"request_id": pending.request_id, "nickname": pending.nickname},
            ),
        )
        return

    await context.websocket.send_json(
        _error_payload(
            event.session_code,
            "invalid_session_state",
            "Session is not accepting joins.",
        )
    )


async def _leave_session(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    session = store.get_session(event.session_code)
    if not session:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session",
                "Session not found.",
            )
        )
        return

    if session.state != SessionState.LOBBY:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session_state",
                "Session is not accepting leaves.",
            )
        )
        return

    player_id = context.player_id or session.player_connections.get(context.websocket)
    if not player_id or player_id not in session.players:
        return

    store.remove_player(session, player_id)
    context.player_id = None

    await _broadcast(
        session,
        build_event(
            session.session_code,
            "player_left",
            {"player_id": player_id},
        ),
    )
    await _broadcast(session, _lobby_snapshot_event(session))


async def _transition_state(
    session: Session,
    websocket: WebSocket,
    from_state: SessionState,
    to_state: SessionState,
) -> None:
    if session.state != from_state:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                "Invalid session state transition.",
                details={
                    "current_state": session.state.value,
                    "expected_state": from_state.value,
                },
            )
        )
        return

    previous_state = session.state
    session.state = to_state

    await _broadcast(
        session,
        build_event(
            session.session_code,
            "session_state_changed",
            {
                "previous_state": previous_state.value,
                "current_state": session.state.value,
            },
        ),
    )
    await _broadcast(session, _lobby_snapshot_event(session))


async def _approve_join(
    store: SessionStore,
    session: Session,
    websocket: WebSocket,
    event: EventEnvelope,
) -> None:
    if session.state != SessionState.RUNNING:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                "Session is not accepting approvals.",
                details={"current_state": session.state.value},
            )
        )
        return

    request_id = event.payload["request_id"]
    pending = store.pop_pending(session, request_id)
    if not pending:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_request",
                "Join request not found.",
            )
        )
        return

    player = store.register_player(session, pending.nickname)
    session.player_connections[pending.websocket] = player.player_id

    await pending.websocket.send_json(
        build_event(
            session.session_code,
            "join_approved",
            {
                "request_id": request_id,
                "player_id": player.player_id,
                "nickname": player.nickname,
            },
        )
    )
    await _broadcast(
        session,
        build_event(
            session.session_code,
            "player_joined",
            {"player_id": player.player_id, "nickname": player.nickname},
        ),
    )
    await _broadcast(session, _lobby_snapshot_event(session))


async def _reject_join(
    store: SessionStore,
    session: Session,
    websocket: WebSocket,
    event: EventEnvelope,
) -> None:
    if session.state != SessionState.RUNNING:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                "Session is not accepting approvals.",
                details={"current_state": session.state.value},
            )
        )
        return

    request_id = event.payload["request_id"]
    pending = store.pop_pending(session, request_id)
    if not pending:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_request",
                "Join request not found.",
            )
        )
        return

    await pending.websocket.send_json(
        build_event(
            session.session_code,
            "join_rejected",
            {
                "request_id": request_id,
                "reason": "Host rejected the request.",
            },
        )
    )


async def _kick_player(
    store: SessionStore,
    session: Session,
    websocket: WebSocket,
    event: EventEnvelope,
) -> None:
    if session.state not in {SessionState.LOBBY, SessionState.RUNNING}:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                "Session does not allow kicking.",
                details={"current_state": session.state.value},
            )
        )
        return

    player_id = event.payload["player_id"]
    if player_id not in session.players:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_player",
                "Player not found.",
            )
        )
        return

    player_socket = _find_player_socket(session, player_id)
    store.remove_player(session, player_id)

    if player_socket:
        await player_socket.send_json(
            build_event(
                session.session_code,
                "player_kicked",
                {"player_id": player_id},
            )
        )

    await _broadcast(
        session,
        build_event(
            session.session_code,
            "player_left",
            {"player_id": player_id},
        ),
    )
    await _broadcast(session, _lobby_snapshot_event(session))


async def _handle_disconnect(store: SessionStore, context: ConnectionContext) -> None:
    if context.role == ROLE_HOST and context.session_code:
        session = store.get_session(context.session_code)
        if session:
            session.host_connections.discard(context.websocket)
        return

    if context.role != ROLE_PLAYER:
        return

    if not context.session_code:
        return

    session = store.get_session(context.session_code)
    if not session:
        return

    pending = store.pop_pending_by_socket(session, context.websocket)
    if pending:
        return

    player_id = context.player_id or session.player_connections.get(context.websocket)
    if not player_id:
        return
    if player_id not in session.players:
        session.player_connections.pop(context.websocket, None)
        return

    if session.state != SessionState.LOBBY:
        session.player_connections.pop(context.websocket, None)
        return

    store.remove_player(session, player_id)

    await _broadcast(
        session,
        build_event(
            session.session_code,
            "player_left",
            {"player_id": player_id},
        ),
    )
    await _broadcast(session, _lobby_snapshot_event(session))


async def _broadcast(session: Session, event: dict[str, Any]) -> None:
    connections = set(session.host_connections) | set(session.player_connections.keys())
    for connection in connections:
        try:
            await connection.send_json(event)
        except RuntimeError:
            continue


async def _broadcast_to_hosts(session: Session, event: dict[str, Any]) -> None:
    for connection in set(session.host_connections):
        try:
            await connection.send_json(event)
        except RuntimeError:
            continue


def _lobby_snapshot_event(session: Session) -> dict[str, Any]:
    players = [
        {"player_id": player.player_id, "nickname": player.nickname}
        for player in sorted(session.players.values(), key=lambda p: p.player_id)
    ]
    return build_event(session.session_code, "lobby_snapshot", {"players": players})


def _session_status_event(session: Session) -> dict[str, Any]:
    return build_event(
        session.session_code,
        "session_status",
        {"current_state": session.state.value},
    )


def _find_player_socket(session: Session, player_id: str) -> WebSocket | None:
    for websocket, stored_id in session.player_connections.items():
        if stored_id == player_id:
            return websocket
    return None


def _error_payload(
    session_code: str,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return build_event(session_code, "error", payload)


def _error_event(
    error: ProtocolError, fallback_session_code: str | None
) -> dict[str, Any]:
    session_code = error.session_code or fallback_session_code or ""
    return _error_payload(session_code, error.code, error.message, error.details)


app = create_app()
