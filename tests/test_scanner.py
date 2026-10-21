import asyncio
import socket

import pytest

from ininet_win.core.scanner import scan_host_ports, service_name


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def _serve_once(port: int, ready: asyncio.Event) -> asyncio.AbstractServer:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        writer.close()

    server = await asyncio.start_server(handler, "127.0.0.1", port)
    ready.set()
    return server


@pytest.mark.asyncio
async def test_scan_finds_open_port() -> None:
    port = _free_port()
    ready = asyncio.Event()
    server = await _serve_once(port, ready)
    await ready.wait()
    try:
        open_ports = await scan_host_ports("127.0.0.1", [port], timeout=1.0)
        assert open_ports == [port]
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_scan_closed_port() -> None:
    port = _free_port()
    open_ports = await scan_host_ports("127.0.0.1", [port], timeout=0.5)
    assert open_ports == []


def test_service_name() -> None:
    assert service_name(80) == "http"
    assert service_name(22) == "ssh"
    assert service_name(65000) == ""
