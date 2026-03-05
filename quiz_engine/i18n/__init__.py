"""gettext helpers for quiz-engine."""

from __future__ import annotations

import ast
import gettext
from functools import lru_cache
from pathlib import Path

SUPPORTED_LOCALES = ("en", "fr")
DEFAULT_LOCALE = "en"
DOMAIN = "messages"
LOCALES_PATH = Path(__file__).resolve().parent / "locales"
MO_PATH = LOCALES_PATH / "{locale}" / "LC_MESSAGES" / f"{DOMAIN}.mo"
PO_PATH = LOCALES_PATH / "{locale}" / "LC_MESSAGES" / f"{DOMAIN}.po"


class DictTranslations(gettext.NullTranslations):
    def __init__(self, catalog: dict[str, str]) -> None:
        super().__init__()
        self._catalog = catalog

    def gettext(self, message: str) -> str:
        translated = self._catalog.get(message)
        if translated is not None:
            return translated
        if self._fallback is not None:
            return self._fallback.gettext(message)
        return message

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        if self._fallback is not None:
            return self._fallback.ngettext(singular, plural, n)
        return self.gettext(singular if n == 1 else plural)


def _parse_po_string(token: str) -> str:
    try:
        return ast.literal_eval(token)
    except (SyntaxError, ValueError):
        return token.strip('"')


def _load_po_catalog(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    catalog: dict[str, str] = {}
    msgid: str | None = None
    msgstr: str | None = None
    mode: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            if msgid is not None and msgstr is not None and msgid != "":
                catalog[msgid] = msgstr
            msgid = _parse_po_string(line[5:].strip())
            msgstr = ""
            mode = "msgid"
            continue
        if line.startswith("msgstr "):
            msgstr = _parse_po_string(line[6:].strip())
            mode = "msgstr"
            continue
        if line.startswith('"'):
            chunk = _parse_po_string(line)
            if mode == "msgid" and msgid is not None:
                msgid += chunk
            elif mode == "msgstr" and msgstr is not None:
                msgstr += chunk
            continue
    if msgid is not None and msgstr is not None and msgid != "":
        catalog[msgid] = msgstr
    return catalog


def _normalize_locale(value: str | None) -> str | None:
    if not value:
        return None
    locale = value.strip().lower().replace("_", "-")
    base = locale.split("-")[0]
    if base in SUPPORTED_LOCALES:
        return base
    return None


def select_locale(accept_language: str | None, preferred: str | None = None) -> str:
    preferred_locale = _normalize_locale(preferred)
    if preferred_locale:
        return preferred_locale
    if not accept_language:
        return DEFAULT_LOCALE
    for item in accept_language.split(","):
        token = item.split(";")[0]
        normalized = _normalize_locale(token)
        if normalized:
            return normalized
    return DEFAULT_LOCALE


@lru_cache
def _translation(locale: str) -> gettext.NullTranslations:
    po_path = Path(str(PO_PATH).format(locale=locale))
    catalog = _load_po_catalog(po_path)
    po_translator = DictTranslations(catalog) if catalog else None

    mo_path = Path(str(MO_PATH).format(locale=locale))
    if mo_path.exists():
        try:
            mo_translator = gettext.translation(
                DOMAIN, localedir=str(LOCALES_PATH), languages=[locale]
            )
            if po_translator is not None:
                po_translator.add_fallback(mo_translator)
                return po_translator
            return mo_translator
        except FileNotFoundError:
            pass

    if po_translator is not None:
        return po_translator
    return gettext.NullTranslations()


def get_translator(locale: str) -> gettext.NullTranslations:
    # Tests may monkeypatch locale paths; always refresh before serving a translator.
    _translation.cache_clear()
    return _translation(locale)


@lru_cache
def get_catalog(locale: str) -> dict[str, str]:
    normalized = _normalize_locale(locale) or DEFAULT_LOCALE
    po_path = Path(str(PO_PATH).format(locale=normalized))
    return _load_po_catalog(po_path)
