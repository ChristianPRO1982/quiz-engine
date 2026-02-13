"""In-memory live session state and websocket fan-out."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from quiz_engine.contracts.runtime_models import StageDefinition
from quiz_engine.runtime.stage_runner import StageRunner


@dataclass
class LivePlayerState:
    player_id: int
    nickname: str


@dataclass
class LiveSessionState:
    session_id: int
    quiz_id: int
    session_code: str
    lifecycle_state: str = "LOBBY"
    stage_index: int | None = None
    current_stage_id: str | None = None
    stage_runner: StageRunner | None = None
    stages: list[StageDefinition] = field(default_factory=list)
    players: dict[int, LivePlayerState] = field(default_factory=dict)
    host_sockets: list[WebSocket] = field(default_factory=list)
    waiting_player_sockets: list[WebSocket] = field(default_factory=list)
    player_sockets: dict[int, list[WebSocket]] = field(default_factory=dict)


class SessionLiveService:
    _ALLOWED_TRANSITIONS = {
        "LOBBY": {"RUNNING", "ENDED"},
        "RUNNING": {"ENDED"},
        "ENDED": set(),
    }

    def __init__(self) -> None:
        self._sessions: dict[str, LiveSessionState] = {}
        self._lock = asyncio.Lock()

    async def create_or_replace_session(
        self,
        *,
        session_id: int,
        quiz_id: int,
        session_code: str,
        lifecycle_state: str = "LOBBY",
        stages: list[StageDefinition] | None = None,
    ) -> LiveSessionState:
        live = LiveSessionState(
            session_id=session_id,
            quiz_id=quiz_id,
            session_code=session_code,
            lifecycle_state=lifecycle_state,
            stages=stages or [],
        )
        async with self._lock:
            self._sessions[session_code] = live
        return live

    async def get_session(self, session_code: str) -> LiveSessionState | None:
        async with self._lock:
            return self._sessions.get(session_code)

    async def attach_host_socket(self, session_code: str, websocket: WebSocket) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            if websocket not in live.host_sockets:
                live.host_sockets.append(websocket)

    async def attach_pending_player_socket(
        self, session_code: str, websocket: WebSocket
    ) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            if websocket not in live.waiting_player_sockets:
                live.waiting_player_sockets.append(websocket)

    async def promote_player_socket(
        self,
        session_code: str,
        *,
        websocket: WebSocket,
        player_id: int,
    ) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.waiting_player_sockets = [
                item for item in live.waiting_player_sockets if item is not websocket
            ]
            sockets = live.player_sockets.setdefault(player_id, [])
            if websocket not in sockets:
                sockets.append(websocket)

    async def detach_socket(self, session_code: str, websocket: WebSocket) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.host_sockets = [
                item for item in live.host_sockets if item is not websocket
            ]
            live.waiting_player_sockets = [
                item for item in live.waiting_player_sockets if item is not websocket
            ]
            for player_id, sockets in list(live.player_sockets.items()):
                kept = [item for item in sockets if item is not websocket]
                if kept:
                    live.player_sockets[player_id] = kept
                else:
                    live.player_sockets.pop(player_id, None)

    async def upsert_player(
        self,
        session_code: str,
        *,
        player_id: int,
        nickname: str,
    ) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.players[player_id] = LivePlayerState(
                player_id=player_id,
                nickname=nickname,
            )

    async def remove_player(self, session_code: str, *, player_id: int) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.players.pop(player_id, None)
            live.player_sockets.pop(player_id, None)

    async def transition_state(
        self,
        session_code: str,
        *,
        new_state: str,
    ) -> LiveSessionState:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                raise ValueError("Live session not found.")

            if live.lifecycle_state == new_state:
                return live

            allowed = self._ALLOWED_TRANSITIONS.get(live.lifecycle_state, set())
            if new_state not in allowed:
                raise ValueError(
                    f"Invalid transition {live.lifecycle_state} -> {new_state}."
                )

            live.lifecycle_state = new_state
            return live

    async def set_active_stage(
        self,
        session_code: str,
        *,
        stage_index: int,
        stage_id: str,
        stage_runner: StageRunner,
    ) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.stage_index = stage_index
            live.current_stage_id = stage_id
            live.stage_runner = stage_runner

    async def clear_active_stage(self, session_code: str) -> None:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return
            live.current_stage_id = None
            live.stage_runner = None

    async def lobby_snapshot(self, session_code: str) -> dict[str, Any]:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return {"session_state": "ENDED", "players": []}
            players = [
                {
                    "player_id": player.player_id,
                    "nickname": player.nickname,
                }
                for player in sorted(
                    live.players.values(),
                    key=lambda value: (value.nickname.lower(), value.player_id),
                )
            ]
            return {
                "session_state": live.lifecycle_state,
                "players": players,
                "stage_index": live.stage_index,
                "stage_id": live.current_stage_id,
            }

    async def broadcast(
        self,
        session_code: str,
        message: dict[str, Any],
        *,
        audience: str = "ALL",
        player_id: int | None = None,
    ) -> None:
        sockets = await self._collect_sockets(
            session_code,
            audience=audience,
            player_id=player_id,
        )
        stale: list[WebSocket] = []
        for websocket in sockets:
            try:
                await asyncio.wait_for(websocket.send_json(message), timeout=0.25)
            except Exception:
                stale.append(websocket)
        if stale:
            for websocket in stale:
                await self.detach_socket(session_code, websocket)

    async def _collect_sockets(
        self,
        session_code: str,
        *,
        audience: str,
        player_id: int | None,
    ) -> list[WebSocket]:
        async with self._lock:
            live = self._sessions.get(session_code)
            if live is None:
                return []

            if audience == "HOST":
                return list(live.host_sockets)

            if audience == "PLAYERS":
                sockets: list[WebSocket] = list(live.waiting_player_sockets)
                for bucket in live.player_sockets.values():
                    sockets.extend(bucket)
                return sockets

            if audience == "PLAYER":
                if player_id is None:
                    return []
                return list(live.player_sockets.get(player_id, []))

            sockets = list(live.host_sockets)
            sockets.extend(live.waiting_player_sockets)
            for bucket in live.player_sockets.values():
                sockets.extend(bucket)
            return sockets
