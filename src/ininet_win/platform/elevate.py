"""Administrator privilege checks and UAC elevation (Windows)."""

from __future__ import annotations

import ctypes
import sys


def is_admin() -> bool:
    """Return True if the current process runs with administrator rights.

    On non-Windows platforms this always returns False (no elevation concept
    handled here).
    """
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin(args: list[str] | None = None) -> bool:
    """Relaunch the current command with UAC elevation.

    Returns True if the elevated process was launched (the caller should then
    exit). Returns False if elevation was refused or unavailable.
    """
    if sys.platform != "win32":
        return False
    if args is None:
        args = sys.argv[1:]

    executable = sys.executable
    params = " ".join(_quote(a) for a in [*_module_args(), *args])

    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, params, None, 1
        )
    except (AttributeError, OSError):
        return False
    return int(result) > 32


def _module_args() -> list[str]:
    """Arguments to keep invoking the same entry point under a new process."""
    if getattr(sys, "frozen", False):
        return []
    return ["-m", "ininet_win"]


def _quote(value: str) -> str:
    if not value:
        return '""'
    if " " in value or "\t" in value:
        return f'"{value}"'
    return value


def can_see_other_processes() -> bool:
    """Whether the current privileges allow resolving processes owned by others."""
    return is_admin()
