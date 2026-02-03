from __future__ import annotations

from pathlib import Path

from auth.settings import AuthSettings


def test_auth_settings_dev_mode_when_dev_file_exists(
    tmp_path: Path, monkeypatch
) -> None:
    dev_file = tmp_path / "local.conf"
    dev_file.write_text("dev\n", encoding="utf-8")

    monkeypatch.delenv("AUTH_MODE", raising=False)
    monkeypatch.setenv("AUTH_DEV_FILE", str(dev_file))

    settings = AuthSettings.from_env()

    assert settings.mode == "dev"


def test_auth_settings_respects_explicit_auth_mode(tmp_path: Path, monkeypatch) -> None:
    dev_file = tmp_path / "local.conf"
    dev_file.write_text("dev\n", encoding="utf-8")

    monkeypatch.setenv("AUTH_MODE", "oidc")
    monkeypatch.setenv("AUTH_DEV_FILE", str(dev_file))

    settings = AuthSettings.from_env()

    assert settings.mode == "oidc"
