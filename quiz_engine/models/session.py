"""Session and player models (qe_* only)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from quiz_engine.db.base import Base


class Session(Base):
    __tablename__ = "qe_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    quiz_id: Mapped[int | None] = mapped_column(ForeignKey("qe_quiz.id"), nullable=True)
    host_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("qe_user.id"), nullable=True
    )
    state: Mapped[str] = mapped_column(
        Enum("LOBBY", "RUNNING", "ENDED", name="qe_session_state"),
        nullable=False,
        server_default="LOBBY",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Player(Base):
    __tablename__ = "qe_player"
    __table_args__ = (Index("ix_qe_player_session_id", "session_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("qe_session.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("qe_user.id"), nullable=True)
    player_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    is_guest: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
