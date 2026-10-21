"""Parse port specifications like ``22,80,443`` or ``1-1024``."""

from __future__ import annotations

MAX_PORT = 65535


def parse_ports(spec: str) -> list[int]:
    """Parse a port spec into a sorted list of unique ports.

    Accepts comma-separated items, each either a single port (``80``) or a range
    (``1-1024``).
    """
    ports: set[int] = set()
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            parts = chunk.split("-", 1)
            try:
                start, end = int(parts[0]), int(parts[1])
            except ValueError as exc:
                raise ValueError(f"invalid port range {chunk!r}") from exc
            if start > end:
                start, end = end, start
            _validate(start)
            _validate(end)
            ports.update(range(start, end + 1))
        else:
            try:
                port = int(chunk)
            except ValueError as exc:
                raise ValueError(f"invalid port {chunk!r}") from exc
            _validate(port)
            ports.add(port)
    if not ports:
        raise ValueError("no ports specified")
    return sorted(ports)


def _validate(port: int) -> None:
    if not (1 <= port <= MAX_PORT):
        raise ValueError(f"port out of range: {port}")
