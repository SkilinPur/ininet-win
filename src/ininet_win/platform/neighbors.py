"""Neighbour (ARP) table lookup (Windows)."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

_ARP_LINE = re.compile(
    r"^\s*(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"(?P<mac>[0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})\s+"
    r"(?P<type>\S+)"
)


@dataclass(frozen=True)
class Neighbour:
    ip: str
    mac: str
    kind: str


def get_neighbours() -> list[Neighbour]:
    """Parse ``arp -a`` output into a list of neighbours."""
    try:
        output = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding="utf-8",
            errors="replace",
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return []

    result: list[Neighbour] = []
    seen: set[str] = set()
    for line in output.splitlines():
        match = _ARP_LINE.match(line)
        if not match:
            continue
        ip = match.group("ip")
        if ip in seen:
            continue
        seen.add(ip)
        result.append(
            Neighbour(ip=ip, mac=match.group("mac").upper(), kind=match.group("type"))
        )
    return result


def mac_by_ip(neighbours: list[Neighbour]) -> dict[str, str]:
    return {n.ip: n.mac for n in neighbours}
