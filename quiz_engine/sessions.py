"""In-memory session storage and state."""

from dataclasses import dataclass, field
from enum import Enum
import secrets
import string
from typing import Optional
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
class Session:
    session_code: str
    state: SessionState = SessionState.LOBBY
    players: dict[str, Player] = field(default_factory=dict)
    host_connections: set[WebSocket] = field(default_factory=set)
    player_connections: dict[WebSocket, str] = field(default_factory=dict)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        session_code = self._generate_code()
        session = Session(session_code=session_code)
        self._sessions[session_code] = session
        return session

    def get_session(self, session_code: str) -> Optional[Session]:
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

    def _generate_code(self) -> str:
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if code not in self._sessions:
                return code
