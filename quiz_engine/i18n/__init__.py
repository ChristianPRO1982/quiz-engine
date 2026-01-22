"""gettext helpers for quiz-engine."""

from __future__ import annotations

import gettext
from functools import lru_cache
from pathlib import Path

SUPPORTED_LOCALES = ("en", "fr")
DEFAULT_LOCALE = "en"
DOMAIN = "messages"
LOCALES_PATH = Path(__file__).resolve().parent / "locales"


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
    try:
        return gettext.translation(
            DOMAIN, localedir=str(LOCALES_PATH), languages=[locale]
        )
    except FileNotFoundError:
        return gettext.NullTranslations()


def get_translator(locale: str) -> gettext.NullTranslations:
    return _translation(locale)
