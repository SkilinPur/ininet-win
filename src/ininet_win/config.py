"""User configuration (language preference) for ininet-win."""

from __future__ import annotations

import json
from pathlib import Path

from ininet_win.storage.db import default_db_path

DEFAULT_CONFIG_NAME = "config.json"


def default_config_path() -> Path:
    """Config path next to the database: ``%LOCALAPPDATA%\\ininet\\config.json``."""
    return default_db_path().parent / DEFAULT_CONFIG_NAME


def load_config(path: str | Path | None = None) -> dict[str, object]:
    """Load the config file. Returns an empty dict if missing or invalid."""
    config_path = Path(path) if path is not None else default_config_path()
    if not config_path.is_file():
        return {}
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(config: dict[str, object], path: str | Path | None = None) -> Path:
    """Persist the config file, returning its path."""
    config_path = Path(path) if path is not None else default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return config_path


def get_language(path: str | Path | None = None) -> str | None:
    """Return the stored language preference, if any."""
    value = load_config(path).get("language")
    return str(value) if value else None


def set_language(lang: str, path: str | Path | None = None) -> Path:
    """Store the language preference in the config file."""
    config = load_config(path)
    config["language"] = lang
    return save_config(config, path)
