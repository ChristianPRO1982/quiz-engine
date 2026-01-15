from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.hosts: Dict[str, WebSocket] = {}
        self.players: Dict[str, Set[WebSocket]] = {}

    async def connect_host(self, session_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.hosts[session_code] = websocket

    async def connect_player(self, session_code: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.players.setdefault(session_code, set()).add(websocket)

    def disconnect_host(self, session_code: str) -> None:
        self.hosts.pop(session_code, None)

    def disconnect_player(self, session_code: str, websocket: WebSocket) -> None:
        if session_code in self.players:
            self.players[session_code].discard(websocket)
            if not self.players[session_code]:
                self.players.pop(session_code, None)

    async def send_to_host(self, session_code: str, message: dict) -> None:
        websocket = self.hosts.get(session_code)
        if websocket:
            await websocket.send_json(message)

    async def broadcast(self, session_code: str, message: dict) -> None:
        if session_code in self.players:
            for websocket in list(self.players[session_code]):
                await websocket.send_json(message)
        await self.send_to_host(session_code, message)
