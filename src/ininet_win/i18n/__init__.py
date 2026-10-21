"""Internationalization: JSON-based translations for ininet-win."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "ru")
_LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def locales_dir() -> Path:
    return _LOCALES_DIR


def available_langs() -> list[str]:
    """Languages that have a locale file available."""
    return [lang for lang in SUPPORTED_LANGS if (_LOCALES_DIR / f"{lang}.json").is_file()]


def load_catalog(lang: str) -> dict[str, str]:
    """Load a translation catalog for a language, falling back to empty dict."""
    path = _LOCALES_DIR / f"{lang}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def normalize_lang(lang: str | None) -> str | None:
    """Normalize a language code (``ru-RU`` -> ``ru``). Returns None if unknown."""
    if not lang:
        return None
    base = lang.replace("_", "-").split("-")[0].strip().lower()
    if base in SUPPORTED_LANGS:
        return base
    return None
