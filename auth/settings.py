from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthSettings:
    mode: str

    @staticmethod
    def from_env() -> "AuthSettings":
        """Load authentication settings from environment variables."""
        return AuthSettings(mode=os.environ.get("AUTH_MODE", "oidc").lower())
