"""Consent models (qe_* only)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from quiz_engine.db.base import Base


class Consent(Base):
    __tablename__ = "qe_consent"
    __table_args__ = (UniqueConstraint("user_id", "scope"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("qe_user.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(
        Enum("pseudo", "history", "email", name="qe_consent_scope"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum("granted", "revoked", name="qe_consent_status"), nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ConsentAudit(Base):
    __tablename__ = "qe_consent_audit"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("qe_user.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(
        Enum("pseudo", "history", "email", name="qe_consent_scope"), nullable=False
    )
    action: Mapped[str] = mapped_column(
        Enum(
            "granted",
            "revoked",
            "expired",
            "revalidated",
            name="qe_consent_action",
        ),
        nullable=False,
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
