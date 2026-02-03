"""Tests for i18n helpers."""

from __future__ import annotations

import gettext
from pathlib import Path

import quiz_engine.i18n as i18n


def _configure_locales(tmp_path: Path, monkeypatch) -> Path:
    locales_path = tmp_path / "locales"
    po_dir = locales_path / "en" / "LC_MESSAGES"
    po_dir.mkdir(parents=True)
    po_path = po_dir / "messages.po"
    monkeypatch.setattr(i18n, "LOCALES_PATH", locales_path)
    monkeypatch.setattr(
        i18n, "MO_PATH", locales_path / "{locale}" / "LC_MESSAGES" / "messages.mo"
    )
    monkeypatch.setattr(
        i18n, "PO_PATH", locales_path / "{locale}" / "LC_MESSAGES" / "messages.po"
    )
    i18n._translation.cache_clear()
    return po_path


def test_parse_po_string_handles_literal_and_fallback() -> None:
    assert i18n._parse_po_string('"hello"') == "hello"
    assert i18n._parse_po_string('"unterminated') == "unterminated"


def test_load_po_catalog_parses_entries(tmp_path: Path) -> None:
    po_path = tmp_path / "messages.po"
    po_path.write_text(
        '\n'.join(
            [
                "# comment",
                'msgid "home.title"',
                'msgstr "Bienvenue"',
                'msgid ""',
                '"multi"',
                '"line"',
                'msgstr ""',
                '"multi"',
                '"line fr"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    catalog = i18n._load_po_catalog(po_path)

    assert catalog["home.title"] == "Bienvenue"
    assert catalog["multiline"] == "multiline fr"


def test_normalize_and_select_locale() -> None:
    assert i18n._normalize_locale("EN_us") == "en"
    assert i18n._normalize_locale("zz") is None
    assert i18n.select_locale(None) == i18n.DEFAULT_LOCALE
    assert i18n.select_locale("fr-CA,fr;q=0.9") == "fr"
    assert i18n.select_locale("zz", preferred="fr") == "fr"


def test_translation_uses_po_catalog(tmp_path: Path, monkeypatch) -> None:
    po_path = _configure_locales(tmp_path, monkeypatch)
    po_path.write_text(
        '\n'.join(
            [
                'msgid "home.badge.dev"',
                'msgstr "Dev"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    translator = i18n.get_translator("en")

    assert translator.gettext("home.badge.dev") == "Dev"
    assert translator.gettext("unknown.key") == "unknown.key"


def test_translation_handles_missing_mo(tmp_path: Path, monkeypatch) -> None:
    _configure_locales(tmp_path, monkeypatch)
    mo_path = i18n.LOCALES_PATH / "en" / "LC_MESSAGES" / "messages.mo"
    mo_path.parent.mkdir(parents=True, exist_ok=True)
    mo_path.write_bytes(b"")

    def _raise_file_not_found(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr(i18n.gettext, "translation", _raise_file_not_found)
    i18n._translation.cache_clear()

    translator = i18n.get_translator("en")

    assert isinstance(translator, gettext.NullTranslations)
