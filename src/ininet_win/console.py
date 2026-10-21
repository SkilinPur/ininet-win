"""Ensure UTF-8 output on Windows so Cyrillic renders correctly."""

from __future__ import annotations

import sys


def enable_utf8() -> None:
    """Force UTF-8 stdout/stderr on Windows. Safe no-op elsewhere."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
