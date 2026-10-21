"""Asynchronous TCP port scanner."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

from ininet_win.core.services import service_name

__all__ = ["service_name", "scan_host_ports"]


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
