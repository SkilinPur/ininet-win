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
