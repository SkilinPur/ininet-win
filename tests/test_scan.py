from unittest import mock

import pytest

from ininet_win.core import scan as scan_mod


@pytest.mark.asyncio
async def test_scan_network_mocked() -> None:
    async def fake_sweep(hosts, concurrency=128, timeout=1.0):
        return ["192.168.0.1"]

    async def fake_scan(ip, ports, timeout=0.5, concurrency=256):
        return [80, 443]

    with (
        mock.patch.object(scan_mod, "ping_sweep", side_effect=fake_sweep),
        mock.patch.object(scan_mod, "scan_host_ports", side_effect=fake_scan),
        mock.patch.object(scan_mod, "get_neighbours", return_value=[]),
    ):
        result = await scan_mod.scan_network("192.168.0.0/30", "80,443")

    assert result.network == "192.168.0.0/30"
    assert [h.ip for h in result.hosts] == ["192.168.0.1"]
    assert [p.port for p in result.hosts[0].ports] == [80, 443]
    assert result.hosts[0].ports[0].service == "http"


@pytest.mark.asyncio
async def test_scan_network_grabs_banners() -> None:
    async def fake_sweep(hosts, concurrency=128, timeout=1.0):
        return ["192.168.0.1"]

    async def fake_scan(ip, ports, timeout=0.5, concurrency=256):
        return [22, 80]

    async def fake_banner(ip, port, timeout=1.0):
        return {22: "SSH-2.0-OpenSSH", 80: "HTTP/1.0 200 OK"}[port]

    with (
        mock.patch.object(scan_mod, "ping_sweep", side_effect=fake_sweep),
        mock.patch.object(scan_mod, "scan_host_ports", side_effect=fake_scan),
        mock.patch.object(scan_mod, "grab_banner", side_effect=fake_banner),
        mock.patch.object(scan_mod, "get_neighbours", return_value=[]),
    ):
        result = await scan_mod.scan_network(
            "192.168.0.0/30", "22,80", grab_banners=True
        )

    banners = {p.port: p.banner for p in result.hosts[0].ports}
    assert banners == {22: "SSH-2.0-OpenSSH", 80: "HTTP/1.0 200 OK"}


@pytest.mark.asyncio
async def test_scan_network_no_banners_by_default() -> None:
    async def fake_sweep(hosts, concurrency=128, timeout=1.0):
        return ["192.168.0.1"]

    async def fake_scan(ip, ports, timeout=0.5, concurrency=256):
        return [80]

    with (
        mock.patch.object(scan_mod, "ping_sweep", side_effect=fake_sweep),
        mock.patch.object(scan_mod, "scan_host_ports", side_effect=fake_scan),
        mock.patch.object(scan_mod, "get_neighbours", return_value=[]),
    ):
        result = await scan_mod.scan_network("192.168.0.0/30", "80")

    assert result.hosts[0].ports[0].banner == ""


@pytest.mark.asyncio
async def test_scan_network_no_ports() -> None:
    async def fake_sweep(hosts, concurrency=128, timeout=1.0):
        return ["192.168.0.1"]

    with (
        mock.patch.object(scan_mod, "ping_sweep", side_effect=fake_sweep),
        mock.patch.object(scan_mod, "get_neighbours", return_value=[]),
    ):
        result = await scan_mod.scan_network("192.168.0.0/30", "80", scan_ports=False)

    assert result.hosts[0].ports == []


@pytest.mark.asyncio
async def test_scan_network_invalid_cidr() -> None:
    with pytest.raises(ValueError):
        await scan_mod.scan_network("bad", "80")
