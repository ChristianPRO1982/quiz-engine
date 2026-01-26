"""Stage outcome model (qe_* only)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from quiz_engine.db.base import Base


class StageOutcomeRecord(Base):
    __tablename__ = "qe_stage_outcome"
    __table_args__ = (Index("ix_qe_stage_outcome_session_id", "session_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("qe_session.id", ondelete="CASCADE"), nullable=False
    )
    stage_id: Mapped[str] = mapped_column(String(64), nullable=False)
    stage_index: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
