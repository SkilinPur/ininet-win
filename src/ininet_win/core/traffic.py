"""Traffic model: per-interface volume and rates from OS counters.

This is the "light" monitoring mode: it uses interface byte counters from the
OS (no packet capture, no driver, no admin rights). It answers "how much and how
fast is this interface transferring", not "which connection transferred what".
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ininet_win.platform.traffic import interface_counters

# Interfaces whose counters are virtual/noise; hidden unless explicitly kept.
_IGNORED_PREFIXES = ("Loopback", "isatap", "Teredo", "6to4", "vEthernet (Default")


@dataclass
class InterfaceTraffic:
    name: str
    bytes_sent: int = 0
    bytes_recv: int = 0
    packets_sent: int = 0
    packets_recv: int = 0
    send_bps: float = 0.0
    recv_bps: float = 0.0

    @property
    def total(self) -> int:
        return self.bytes_sent + self.bytes_recv

    @property
    def total_bps(self) -> float:
        return self.send_bps + self.recv_bps


@dataclass
class TrafficSnapshot:
    timestamp: float
    interfaces: dict[str, dict[str, int]] = field(default_factory=dict)

    @classmethod
    def capture(cls) -> TrafficSnapshot:
        return cls(timestamp=time.monotonic(), interfaces=interface_counters())

    def rates(self, previous: TrafficSnapshot | None) -> dict[str, InterfaceTraffic]:
        """Compute per-interface traffic with rates relative to ``previous``."""
        elapsed = 1.0
        if previous is not None:
            elapsed = max(self.timestamp - previous.timestamp, 1e-6)
        result: dict[str, InterfaceTraffic] = {}
        for name, counters in self.interfaces.items():
            item = InterfaceTraffic(
                name=name,
                bytes_sent=counters.get("bytes_sent", 0),
                bytes_recv=counters.get("bytes_recv", 0),
                packets_sent=counters.get("packets_sent", 0),
                packets_recv=counters.get("packets_recv", 0),
            )
            if previous is not None and name in previous.interfaces:
                prev = previous.interfaces[name]
                item.send_bps = max(
                    0.0, (item.bytes_sent - prev.get("bytes_sent", 0)) / elapsed
                )
                item.recv_bps = max(
                    0.0, (item.bytes_recv - prev.get("bytes_recv", 0)) / elapsed
                )
            result[name] = item
        return result


def is_noise(name: str) -> bool:
    """Heuristic: hidden/virtual interfaces that only add clutter."""
    return any(name.startswith(prefix) for prefix in _IGNORED_PREFIXES)


def format_bytes(value: float) -> str:
    """Human-readable byte size (1024-based)."""
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def format_rate(value: float) -> str:
    """Human-readable transfer rate (bytes/second)."""
    return f"{format_bytes(value)}/s"
