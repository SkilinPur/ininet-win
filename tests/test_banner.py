import asyncio
import socket

import pytest

from ininet_win.core.banner import _clean, grab_banner


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_clean_strips_and_truncates() -> None:
    assert _clean(b"\x00\x01SSH-2.0-OpenSSH_9.0\r\n") == "SSH-2.0-OpenSSH_9.0"
    assert _clean(b"") == ""
    assert _clean(b"line\n\n\n") == "line"
    assert len(_clean(b"x" * 500)) == 120


@pytest.mark.asyncio
async def test_grab_banner_greeting_port() -> None:
    port = _free_port()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        writer.write(b"SSH-2.0-TestServer\r\n")
        await writer.drain()
        writer.close()

    server = await asyncio.start_server(handler, "127.0.0.1", port)
    try:
        # 22 is a greeting port; patch the port set membership via monkeypatch-free trick:
        from ininet_win.core import banner as banner_mod

        banner_mod._GREETING_PORTS.add(port)
        try:
            result = await grab_banner("127.0.0.1", port, timeout=1.0)
        finally:
            banner_mod._GREETING_PORTS.discard(port)
        assert result == "SSH-2.0-TestServer"
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_grab_banner_closed_port() -> None:
    port = _free_port()
    result = await grab_banner("127.0.0.1", port, timeout=0.5)
    assert result == ""
