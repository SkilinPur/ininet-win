"""Language resolution: flag > env > config > system > interactive prompt."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ininet_win import config as cfg
from ininet_win.i18n import DEFAULT_LANG, available_langs, normalize_lang

ENV_VAR = "ININET_LANG"


def _system_lang() -> str | None:
    """Detect the OS language hint (very conservative)."""
    for var in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        normalized = normalize_lang(value)
        if normalized:
            return normalized
    if sys.platform == "win32":
        try:
            import locale

            code, _ = locale.getdefaultlocale()
            return normalize_lang(code)
        except (ValueError, TypeError):
            return None
    return None


def _is_interactive() -> bool:
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except (ValueError, AttributeError):
        return False


def resolve_language(
    flag: str | None = None,
    *,
    config_path: str | Path | None = None,
    prompt: bool = True,
) -> tuple[str, bool]:
    """Resolve the effective language.

    Returns ``(lang, was_prompted)``. Order of precedence:
    ``--lang`` flag, ``ININET_LANG`` env var, saved config, system locale,
    then - if interactive and still unknown - an interactive prompt.
    """
    from ininet_win.i18n import translator

    # 1. explicit flag
    normalized = normalize_lang(flag)
    if normalized:
        return normalized, False

    # 2. environment variable
    normalized = normalize_lang(os.environ.get(ENV_VAR))
    if normalized:
        return normalized, False

    # 3. saved config
    normalized = normalize_lang(cfg.get_language(config_path))
    if normalized:
        return normalized, False

    # 4. system locale
    normalized = _system_lang()
    if normalized:
        cfg.set_language(normalized, config_path)
        return normalized, False

    # 5. interactive prompt on first run
    if prompt and _is_interactive():
        chosen = _prompt_language()
        cfg.set_language(chosen, config_path)
        translator.set_language(chosen)
        return chosen, True

    return DEFAULT_LANG, False


def _prompt_language() -> str:
    """Ask the user to choose a language on first run."""
    langs = available_langs()
    labels = {
        "en": "English",
        "ru": "Русский",
    }
    print("Select language / Выберите язык:")
    for i, lang in enumerate(langs, 1):
        print(f"  {i}) {labels.get(lang, lang)}")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            return DEFAULT_LANG
        if not raw:
            return DEFAULT_LANG
        if raw.isdigit() and 1 <= int(raw) <= len(langs):
            return langs[int(raw) - 1]
        normalized = normalize_lang(raw)
        if normalized:
            return normalized
        print("  ? Try again / Попробуйте снова")
