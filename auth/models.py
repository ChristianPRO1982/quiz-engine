from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    subject: str
    display_name: str
    auth_mode: str
    email: str | None = None
