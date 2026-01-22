"""FastAPI application for Sprint 0 realtime lobby."""

from collections.abc import Callable
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

import qrcode
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from .i18n import get_translator, select_locale
from .protocol import (
    ROLE_HOST,
    ROLE_PLAYER,
    EventEnvelope,
    ProtocolError,
    build_event,
    parse_event,
)
from .sessions import Session, SessionState, SessionStore

STATE_KEYS = ["state.LOBBY", "state.RUNNING", "state.ENDED"]

HOST_JS_KEYS = [
    "host.js.no_players",
    "host.js.no_pending",
    "host.js.kick",
    "host.js.approve",
    "host.js.reject",
    "host.js.ws_not_connected",
    "host.js.connected",
    "host.js.join_request_from",
    "host.js.player_joined",
    "host.js.player_left",
    "host.js.session_state",
    "host.js.error",
    "host.js.ws_disconnected",
    "host.js.creating_session",
    "host.js.create_failed",
    "host.js.session_ready",
    *STATE_KEYS,
]

PLAYER_JS_KEYS = [
    "player.js.ws_not_connected",
    "player.js.connected",
    "player.js.join_request_sent",
    "player.js.waiting_approval",
    "player.js.session_is",
    "player.js.joined_lobby",
    "player.js.join_rejected",
    "player.js.in_lobby",
    "player.js.left_lobby",
    "player.js.player_kicked",
    "player.js.error",
    "player.js.disconnected",
    "player.js.enter_nickname",
    *STATE_KEYS,
]


@dataclass
class ConnectionContext:
    websocket: WebSocket
    role: str
    session_code: str | None = None
    player_id: str | None = None
    translator: Callable[[str], str] = field(default=lambda text: text)


def _select_translator(
    accept_language: str | None, preferred: str | None = None
) -> Callable[[str], str]:
    locale = select_locale(accept_language, preferred)
    return get_translator(locale).gettext


def _template_context(
    request: Request, keys: list[str] | None = None
) -> dict[str, Any]:
    accept_language = request.headers.get("accept-language")
    preferred = request.query_params.get("lang")
    locale = select_locale(accept_language, preferred)
    translator = get_translator(locale).gettext
    context: dict[str, Any] = {"_": translator}
    if keys:
        context["translations"] = {key: translator(key) for key in keys}
    context["locale"] = locale
    return context


def _translator_for_websocket(websocket: WebSocket) -> Callable[[str], str]:
    return _select_translator(
        websocket.headers.get("accept-language"),
        websocket.query_params.get("lang"),
    )


def create_app() -> FastAPI:
    app = FastAPI()
    app.state.store = SessionStore()

    templates_dir = Path(__file__).resolve().parent / "templates"
    static_dir = Path(__file__).resolve().parent / "static"
    templates = Jinja2Templates(directory=str(templates_dir))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def host_page(request: Request) -> HTMLResponse:
        context = _template_context(request, HOST_JS_KEYS)
        return templates.TemplateResponse(request, "host.html", context)

    @app.get("/join/{session_code}", response_class=HTMLResponse, name="join_page")
    async def join_page(request: Request, session_code: str) -> HTMLResponse:
        context = _template_context(request, PLAYER_JS_KEYS)
        context["session_code"] = session_code
        return templates.TemplateResponse(request, "player.html", context)

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

        translator = _select_translator(
            websocket.headers.get("accept-language"),
            websocket.query_params.get("lang"),
        )
        context = ConnectionContext(
            websocket=websocket,
            role=role,
            translator=translator,
        )
        await _register_connection(store, context, websocket)

        try:
            while True:
                raw = await websocket.receive_json()
                try:
                    event = parse_event(raw)
                except ProtocolError as exc:
                    await websocket.send_json(
                        _error_event(exc, context.session_code, context.translator)
                    )
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
            _error_payload(session_code, "invalid_session", context.translator)
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
                context.translator,
            )
        )
        return

    session = store.get_session(event.session_code)
    if not session:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session",
                context.translator,
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
            translate=context.translator,
        )
        return

    if event.type == "host_end":
        await _transition_state(
            session,
            context.websocket,
            from_state=SessionState.RUNNING,
            to_state=SessionState.ENDED,
            translate=context.translator,
        )
        return

    if event.type == "host_approve_join":
        await _approve_join(
            store,
            session,
            context.websocket,
            event,
            context.translator,
        )
        return

    if event.type == "host_reject_join":
        await _reject_join(store, session, context.websocket, event, context.translator)
        return

    await _kick_player(store, session, context.websocket, event, context.translator)


async def _handle_player_event(
    store: SessionStore, context: ConnectionContext, event: EventEnvelope
) -> None:
    if event.type not in {"join_session", "leave_session"}:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_role",
                context.translator,
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
                context.translator,
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
                context.translator,
            )
        )
        return

    if context.websocket in session.pending_connections:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "join_pending",
                context.translator,
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
            context.translator,
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
                context.translator,
            )
        )
        return

    if session.state != SessionState.LOBBY:
        await context.websocket.send_json(
            _error_payload(
                event.session_code,
                "invalid_session_state",
                context.translator,
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
    translate: Callable[[str], str],
) -> None:
    if session.state != from_state:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                translate,
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
    translate: Callable[[str], str],
) -> None:
    if session.state != SessionState.RUNNING:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                translate,
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
                translate,
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
    translate: Callable[[str], str],
) -> None:
    if session.state != SessionState.RUNNING:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                translate,
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
                translate,
            )
        )
        return

    pending_translator = _translator_for_websocket(pending.websocket)
    await pending.websocket.send_json(
        build_event(
            session.session_code,
            "join_rejected",
            {
                "request_id": request_id,
                "reason": pending_translator("join_rejected.host_rejected"),
            },
        )
    )


async def _kick_player(
    store: SessionStore,
    session: Session,
    websocket: WebSocket,
    event: EventEnvelope,
    translate: Callable[[str], str],
) -> None:
    if session.state not in {SessionState.LOBBY, SessionState.RUNNING}:
        await websocket.send_json(
            _error_payload(
                session.session_code,
                "invalid_session_state",
                translate,
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
                translate,
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
    translate: Callable[[str], str],
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "code": code,
        "message": translate(f"error.{code}"),
    }
    if details:
        payload["details"] = details
    return build_event(session_code, "error", payload)


def _error_event(
    error: ProtocolError,
    fallback_session_code: str | None,
    translate: Callable[[str], str],
) -> dict[str, Any]:
    session_code = error.session_code or fallback_session_code or ""
    return _error_payload(session_code, error.code, translate, error.details)


app = create_app()
