"""Translator: resolves keys against a catalog with fallback."""

from __future__ import annotations

from ininet_win.i18n import DEFAULT_LANG, load_catalog, normalize_lang

_catalog: dict[str, str] = {}
_fallback: dict[str, str] = {}
_lang: str = DEFAULT_LANG


def set_language(lang: str) -> str:
    """Set the active language. Returns the language actually applied."""
    global _catalog, _fallback, _lang
    resolved = normalize_lang(lang) or DEFAULT_LANG
    _lang = resolved
    _fallback = load_catalog(DEFAULT_LANG)
    _catalog = _fallback if resolved == DEFAULT_LANG else load_catalog(resolved)
    return resolved


def current_language() -> str:
    return _lang


def t(key: str, **kwargs: object) -> str:
    """Translate a key, formatting ``{placeholders}`` when provided.

    Falls back to the English catalog, then to the key itself.
    """
    template = _catalog.get(key)
    if template is None:
        template = _fallback.get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
    return template
