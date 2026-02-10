from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuthSettings:
    mode: str
    session_secret_key: str
    database_url: str | None

    @staticmethod
    def from_env() -> AuthSettings:
        """Load authentication settings from environment variables."""
        mode_env = os.environ.get("AUTH_MODE")
        dev_file = os.environ.get("AUTH_DEV_FILE", "local.conf")

        if mode_env is None and Path(dev_file).is_file():
            mode = "dev"
        else:
            mode = (mode_env or "oidc").lower()

        session_secret_key = os.environ.get("SESSION_SECRET_KEY")
        if mode == "dev" and not session_secret_key:
            session_secret_key = "dev-insecure-session-secret"
        if not session_secret_key:
            raise RuntimeError("SESSION_SECRET_KEY must be set when not in dev mode.")

        return AuthSettings(
            mode=mode,
            session_secret_key=session_secret_key,
            database_url=os.environ.get("DATABASE_URL"),
        )
