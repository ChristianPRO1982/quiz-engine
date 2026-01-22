"""In-memory session storage and state."""

import secrets
import string
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from starlette.websockets import WebSocket


class SessionState(str, Enum):
    LOBBY = "LOBBY"
    RUNNING = "RUNNING"
    ENDED = "ENDED"


@dataclass
class Player:
    player_id: str
    nickname: str


@dataclass
class PendingJoin:
    request_id: str
    nickname: str
    websocket: WebSocket


@dataclass
class Session:
    session_code: str
    state: SessionState = SessionState.LOBBY
    players: dict[str, Player] = field(default_factory=dict)
    host_connections: set[WebSocket] = field(default_factory=set)
    player_connections: dict[WebSocket, str] = field(default_factory=dict)
    pending_requests: dict[str, PendingJoin] = field(default_factory=dict)
    pending_connections: dict[WebSocket, str] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        session_code = self._generate_code()
        session = Session(session_code=session_code)
        self._sessions[session_code] = session
        return session

    def get_session(self, session_code: str) -> Session | None:
        return self._sessions.get(session_code)

    def remove_player(self, session: Session, player_id: str) -> None:
        session.players.pop(player_id, None)
        for websocket, stored_id in list(session.player_connections.items()):
            if stored_id == player_id:
                session.player_connections.pop(websocket, None)

    def register_player(self, session: Session, nickname: str) -> Player:
        player_id = f"player_{uuid4().hex}"
        player = Player(player_id=player_id, nickname=nickname)
        session.players[player_id] = player
        return player

    def register_pending(
        self, session: Session, websocket: WebSocket, nickname: str
    ) -> PendingJoin:
        request_id = f"join_{uuid4().hex}"
        pending = PendingJoin(
            request_id=request_id,
            nickname=nickname,
            websocket=websocket,
        )
        session.pending_requests[request_id] = pending
        session.pending_connections[websocket] = request_id
        return pending

    def pop_pending(self, session: Session, request_id: str) -> PendingJoin | None:
        pending = session.pending_requests.pop(request_id, None)
        if pending:
            session.pending_connections.pop(pending.websocket, None)
        return pending

    def pop_pending_by_socket(
        self, session: Session, websocket: WebSocket
    ) -> PendingJoin | None:
        request_id = session.pending_connections.pop(websocket, None)
        if not request_id:
            return None
        return session.pending_requests.pop(request_id, None)

    def _generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if code not in self._sessions:
                return code
