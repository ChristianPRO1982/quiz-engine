"""Unit tests for SessionLiveService state and socket routing."""

from __future__ import annotations

import asyncio

import pytest

from quiz_engine.services.session_live_service import SessionLiveService


class _FakeSocket:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        if self.should_fail:
            raise RuntimeError("send failed")
        self.sent.append(payload)


def test_session_live_service_handles_state_and_socket_lifecycle() -> None:
    async def _run() -> None:
        service = SessionLiveService()

        # No-op paths on unknown session.
        ghost = _FakeSocket()
        await service.attach_host_socket("MISSING", ghost)
        await service.attach_pending_player_socket("MISSING", ghost)
        await service.promote_player_socket("MISSING", websocket=ghost, player_id=1)
        await service.detach_socket("MISSING", ghost)
        await service.upsert_player("MISSING", player_id=1, nickname="x")
        await service.remove_player("MISSING", player_id=1)
        await service.set_active_stage(
            "MISSING",
            stage_index=0,
            stage_id="s1",
            stage_runner=object(),
        )
        await service.clear_active_stage("MISSING")

        missing_snapshot = await service.lobby_snapshot("MISSING")
        assert missing_snapshot == {"session_state": "ENDED", "players": []}

        with pytest.raises(ValueError):
            await service.transition_state("MISSING", new_state="RUNNING")

        live = await service.create_or_replace_session(
            session_id=1,
            quiz_id=42,
            session_code="ABC123",
            lifecycle_state="LOBBY",
            stages=[],
        )
        assert live.lifecycle_state == "LOBBY"

        host = _FakeSocket()
        pending = _FakeSocket()
        player_socket = _FakeSocket()

        await service.attach_host_socket("ABC123", host)
        await service.attach_host_socket("ABC123", host)
        await service.attach_pending_player_socket("ABC123", pending)
        await service.attach_pending_player_socket("ABC123", pending)

        await service.promote_player_socket(
            "ABC123",
            websocket=pending,
            player_id=10,
        )
        await service.promote_player_socket(
            "ABC123",
            websocket=player_socket,
            player_id=10,
        )

        await service.upsert_player("ABC123", player_id=10, nickname="bob")
        await service.upsert_player("ABC123", player_id=11, nickname="Alice")

        snapshot = await service.lobby_snapshot("ABC123")
        assert [player["nickname"] for player in snapshot["players"]] == [
            "Alice",
            "bob",
        ]

        same_state = await service.transition_state("ABC123", new_state="LOBBY")
        assert same_state.lifecycle_state == "LOBBY"

        running = await service.transition_state("ABC123", new_state="RUNNING")
        assert running.lifecycle_state == "RUNNING"

        with pytest.raises(ValueError):
            await service.transition_state("ABC123", new_state="LOBBY")

        await service.set_active_stage(
            "ABC123",
            stage_index=2,
            stage_id="stage-2",
            stage_runner=object(),
        )
        after_active = await service.lobby_snapshot("ABC123")
        assert after_active["stage_index"] == 2
        assert after_active["stage_id"] == "stage-2"

        await service.clear_active_stage("ABC123")
        after_clear = await service.lobby_snapshot("ABC123")
        assert after_clear["stage_id"] is None

        # Audience routing.
        host_sockets = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="HOST",
            player_id=None,
        )
        assert host_sockets == [host]

        player_sockets = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="PLAYERS",
            player_id=None,
        )
        assert pending in player_sockets
        assert player_socket in player_sockets

        direct_player = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="PLAYER",
            player_id=10,
        )
        assert player_socket in direct_player

        empty_player = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="PLAYER",
            player_id=None,
        )
        assert empty_player == []

        all_sockets = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="ALL",
            player_id=None,
        )
        assert host in all_sockets
        assert player_socket in all_sockets

        await service.broadcast("ABC123", {"kind": "host"}, audience="HOST")
        assert host.sent[-1] == {"kind": "host"}

        await service.broadcast("ABC123", {"kind": "all"}, audience="ALL")
        assert player_socket.sent[-1] == {"kind": "all"}

        # Stale socket cleanup.
        failing = _FakeSocket(should_fail=True)
        await service.attach_host_socket("ABC123", failing)
        await service.broadcast("ABC123", {"kind": "cleanup"}, audience="HOST")
        sockets_after_cleanup = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="HOST",
            player_id=None,
        )
        assert failing not in sockets_after_cleanup

        await service.remove_player("ABC123", player_id=10)
        remaining_players = await service.lobby_snapshot("ABC123")
        assert [player["player_id"] for player in remaining_players["players"]] == [11]

        await service.detach_socket("ABC123", host)
        remaining_hosts = await service._collect_sockets(  # noqa: SLF001
            "ABC123",
            audience="HOST",
            player_id=None,
        )
        assert host not in remaining_hosts

    asyncio.run(_run())
