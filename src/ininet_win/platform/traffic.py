"""Per-interface traffic counters (Windows).

Reads byte counters from the OS via psutil. Read-only and dependency-light:
no packet capture, no driver, no administrator rights required.

Note: Windows exposes byte counters per network interface, not per connection.
Per-connection volume would need ETW or a packet-capture driver.
"""

from __future__ import annotations

import psutil


def interface_counters() -> dict[str, dict[str, int]]:
    """Return ``{interface: {bytes_sent, bytes_recv, ...}}`` for all interfaces."""
    try:
        raw = psutil.net_io_counters(pernic=True)
    except (psutil.AccessDenied, PermissionError):  # pragma: no cover
        return {}
    result: dict[str, dict[str, int]] = {}
    for name, counters in raw.items():
        result[name] = {
            "bytes_sent": int(counters.bytes_sent),
            "bytes_recv": int(counters.bytes_recv),
            "packets_sent": int(counters.packets_sent),
            "packets_recv": int(counters.packets_recv),
            "dropin": int(getattr(counters, "dropin", 0)),
            "dropout": int(getattr(counters, "dropout", 0)),
            "errin": int(getattr(counters, "errin", 0)),
            "errout": int(getattr(counters, "errout", 0)),
        }
    return result
