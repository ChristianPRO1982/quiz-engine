from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    sub: str
    email: str
    name: str
    groups: list[str]

    @property
    def is_admin(self) -> bool:
        """Return True if user belongs to admin group."""
        return "admins" in self.groups
