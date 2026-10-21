"""Asynchronous TCP port scanner."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

_COMMON_SERVICES = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    135: "msrpc",
    139: "netbios-ssn",
    143: "imap",
    443: "https",
    445: "microsoft-ds",
    587: "smtp",
    993: "imaps",
    995: "pop3s",
    1433: "mssql",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8080: "http-proxy",
    8443: "https-alt",
}


def service_name(port: int) -> str:
    """Best-effort service name for a port number."""
    return _COMMON_SERVICES.get(port, "")


async def _check_port(ip: str, port: int, timeout: float) -> bool:
    try:
        conn = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except (OSError, ConnectionError):
            pass
        del reader
        return True
    except (TimeoutError, OSError, ConnectionError):
        return False


async def scan_host_ports(
    ip: str,
    ports: Iterable[int],
    timeout: float = 0.5,
    concurrency: int = 256,
) -> list[int]:
    """Scan a list of ports on one host. Returns the open ones (sorted)."""
    port_list = list(ports)
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(port: int) -> tuple[int, bool]:
        async with semaphore:
            return port, await _check_port(ip, port, timeout)

    results = await asyncio.gather(*(bounded(p) for p in port_list))
    return sorted(port for port, open_ in results if open_)
