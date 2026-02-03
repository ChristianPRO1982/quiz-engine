from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuthSettings:
    mode: str

    @staticmethod
    def from_env() -> AuthSettings:
        """Load authentication settings from environment variables."""
        mode_env = os.environ.get("AUTH_MODE")
        dev_file = os.environ.get("AUTH_DEV_FILE", "local.conf")

        if mode_env is None and Path(dev_file).is_file():
            mode = "dev"
        else:
            mode = (mode_env or "oidc").lower()

        return AuthSettings(mode=mode)
