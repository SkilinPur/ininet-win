"""Live connection listing (Windows).

Reads the OS connection table via psutil. This is read-only: it never opens,
modifies or closes connections - it just inspects what already exists.
"""

from __future__ import annotations

import psutil


def _fmt_addr(sock_addr: object) -> tuple[str, int]:
    """Extract (ip, port) from a psutil socket address."""
    if not sock_addr:
        return ("", 0)
    if isinstance(sock_addr, tuple) and len(sock_addr) >= 2:
        ip, port = sock_addr[0], sock_addr[1]
        return (str(ip), int(port) if isinstance(port, int) else 0)
    return ("", 0)


def list_connections(kind: str = "inet") -> list[dict[str, object]]:
    """Return current connections as plain dicts.

    Requires administrative rights to resolve the owning process of connections
    that belong to other users; without them ``pid`` is ``None`` and ``process``
    is empty. This function performs no blocking operations beyond the query.
    """
    result: list[dict[str, object]] = []
    try:
        conns = psutil.net_connections(kind=kind)
    except (psutil.AccessDenied, PermissionError):
        return []

    for conn in conns:
        laddr_ip, laddr_port = _fmt_addr(conn.laddr)
        raddr_ip, raddr_port = _fmt_addr(conn.raddr)
        process = ""
        if conn.pid:
            try:
                process = psutil.Process(conn.pid).name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                process = ""
        result.append(
            {
                "family": "tcp" if conn.type.name.startswith("SOCK_STREAM") else "udp",
                "laddr": laddr_ip,
                "lport": laddr_port,
                "raddr": raddr_ip,
                "rport": raddr_port,
                "status": conn.status or "",
                "pid": conn.pid,
                "process": process,
            }
        )
    return result
