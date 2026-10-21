"""Best-effort service banner grabbing for open TCP ports."""

from __future__ import annotations

import asyncio

# Ports whose services usually greet the client immediately.
_GREETING_PORTS = {
    21, 22, 23, 25, 110, 143, 220, 587, 993, 995, 3306, 5432, 6379, 11211, 27017
}
# Ports we probe with a lightweight HTTP request.
_HTTP_PORTS = {80, 3000, 5000, 8000, 8008, 8080, 8081, 8088, 8443, 8888, 9000, 9090}
_HTTP_PORTS |= {443, 4443, 8443}  # TLS ports: raw HEAD is junk but harmless


def _clean(raw: bytes, limit: int = 120) -> str:
    """Turn a raw banner into a single printable, trimmed line."""
    text = raw.decode("utf-8", errors="replace")
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        printable = "".join(ch if ch.isprintable() else " " for ch in line)
        printable = " ".join(printable.split())
        if printable:
            return printable[:limit]
    return ""


async def _read_banner(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: float
) -> str:
    try:
        data = await asyncio.wait_for(reader.read(512), timeout=timeout)
    except (TimeoutError, OSError, ConnectionError):
        return ""
    return _clean(data)


async def grab_banner(ip: str, port: int, timeout: float = 1.0) -> str:
    """Try to read a service banner from ``ip:port``.

    Strategy: connect, read any immediate greeting; if nothing arrives and the
    port looks HTTP-like, send a minimal ``HEAD`` request and read the response.
    Returns an empty string when nothing useful was obtained.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip, port), timeout=timeout
        )
    except (TimeoutError, OSError, ConnectionError):
        return ""

    try:
        banner = ""
        if port in _GREETING_PORTS:
            banner = await _read_banner(reader, writer, timeout)
        if not banner and port in _HTTP_PORTS:
            try:
                writer.write(b"HEAD / HTTP/1.0\r\nHost: ininet\r\n\r\n")
                await writer.drain()
            except (OSError, ConnectionError):
                return ""
            banner = await _read_banner(reader, writer, timeout)
        return banner
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except (OSError, ConnectionError):
            pass
