"""Generate TUI preview SVGs (one per tab, EN and RU) with demo data.

Run from the repository root:
    .venv\\Scripts\\python.exe tools\\make_screenshots.py

Writes docs/tui-<lang>-<tab>.svg. Headless (uses Textual's test harness),
no real network access: all rows are injected sample data.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
from pathlib import Path

from ininet_win.core import topology as topology_mod
from ininet_win.core.monitor import Connection, group_by_process
from ininet_win.core.scan import HostResult, PortResult, ScanResult
from ininet_win.core.topology import build_topology
from ininet_win.core.traffic import InterfaceTraffic
from ininet_win.i18n import translator
from ininet_win.platform.ifaces import Interface
from ininet_win.storage.db import Snapshot
from ininet_win.tui.app import IninetTuiApp

# Demo local interface so topology uses fictional addresses (never the real host).
DEMO_INTERFACE = Interface(
    name="Ethernet", address="10.0.0.5", netmask="255.255.255.0", network="10.0.0.0/24"
)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs"

# Terminal size (columns x rows). The SVG keeps its viewBox and scales
# responsively to fill the container (README, browser, mobile).
TERM_SIZE = (220, 60)


def _make_responsive(svg: str) -> str:
    """Make the SVG scale to the container width instead of a fixed pixel size."""
    return svg.replace(
        "<svg ", '<svg width="100%" height="auto" ', 1
    )


# Allowed demo ranges (RFC 5737 / RFC 1918 demo subnet used in previews).
_ALLOWED_NETS = [
    ipaddress.ip_network("10.0.0.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("224.0.0.251/32"),
]


def _assert_no_leaks(svg: str, name: str) -> None:
    """Fail the build if any real-looking IP leaked into a screenshot."""
    for candidate in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", svg):
        try:
            addr = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if not addr.is_private and not addr.is_multicast:
            continue
        if any(addr in net for net in _ALLOWED_NETS):
            continue
        raise SystemExit(f"IP leak in {name}: {candidate}")

SCAN = ScanResult(
    network="10.0.0.0/24",
    hosts=[
        HostResult(ip="10.0.0.1", mac="02-00-00-00-00-01", ports=[
            PortResult(port=22, service="ssh", banner="SSH-2.0-OpenSSH_9.6"),
            PortResult(port=80, service="http"),
        ]),
        HostResult(ip="10.0.0.10", mac="02-00-00-00-00-0a", ports=[
            PortResult(port=445, service="microsoft-ds"),
        ]),
        HostResult(ip="10.0.0.22", mac="02-00-00-00-00-16", ports=[
            PortResult(port=443, service="https", banner="nginx/1.25.3"),
            PortResult(port=8080, service="http-alt"),
        ]),
    ],
)

CONNS = [
    Connection("tcp", "10.0.0.5", 50110, "203.0.113.10", 443, "ESTABLISHED", 4123, "chrome.exe"),
    Connection("tcp", "10.0.0.5", 50112, "203.0.113.10", 443, "ESTABLISHED", 4123, "chrome.exe"),
    Connection("tcp", "10.0.0.5", 50140, "198.51.100.7", 22, "ESTABLISHED", 8892, "ssh.exe"),
    Connection("tcp", "10.0.0.5", 50150, "198.51.100.20", 993, "ESTABLISHED", 2201, "outlook.exe"),
    Connection("udp", "10.0.0.5", 5353, "224.0.0.251", 5353, "", 3310, "svchost.exe"),
    Connection("tcp", "10.0.0.5", 0, "", 0, "LISTEN", 1044, "svc.exe"),
]

SNAPSHOTS = [
    Snapshot(id=12, created_at="2026-10-21 09:14:02", network="10.0.0.0/24",
             host_count=3, open_port_count=7),
    Snapshot(id=11, created_at="2026-10-20 18:40:11", network="10.0.0.0/24",
             host_count=4, open_port_count=9),
    Snapshot(id=10, created_at="2026-10-19 08:02:55", network="10.0.0.0/24",
             host_count=6, open_port_count=12),
]

TRAFFIC = [
    InterfaceTraffic(name="Ethernet", bytes_sent=712_800_000, bytes_recv=15_320_000_000,
                     recv_bps=1_640_000, send_bps=38_700),
    InterfaceTraffic(name="Wi-Fi", bytes_sent=41_200_000, bytes_recv=182_400_000,
                     recv_bps=96_300, send_bps=12_100),
    InterfaceTraffic(name="Radmin VPN", bytes_sent=1_200_000, bytes_recv=9_100,
                     recv_bps=0.0, send_bps=0.0),
]


async def _render(lang: str) -> None:
    translator.set_language(lang)
    # Never touch real interfaces: force the fictional demo interface.
    topology_mod.get_interfaces = lambda: [DEMO_INTERFACE]
    app = IninetTuiApp()
    # Fixed terminal size for consistent previews.
    async with app.run_test(size=TERM_SIZE) as pilot:
        app.query_one("ScanTab").set_result(SCAN)
        app.query_one("WatchTab").refresh_rows(CONNS)
        app.query_one("TopTab").refresh_rows(group_by_process(CONNS))
        app.query_one("TrafficTab").refresh_rows(TRAFFIC)
        app.query_one("MapTab").refresh_rows(build_topology(SCAN, CONNS))
        app.query_one("HistoryTab").refresh_rows(SNAPSHOTS)
        await pilot.pause()

        for tab, name in [
            ("scan", "scan"), ("watch", "watch"), ("top", "top"),
            ("traffic", "traffic"), ("map", "map"), ("history", "history"),
        ]:
            app.query_one("TabbedContent").active = tab
            await pilot.pause()
            svg = _make_responsive(app.export_screenshot())
            _assert_no_leaks(svg, f"tui-{lang}-{name}.svg")
            (OUT / f"tui-{lang}-{name}.svg").write_text(svg, encoding="utf-8")
            print(f"wrote docs/tui-{lang}-{name}.svg")


async def main() -> None:
    for lang in ("en", "ru"):
        await _render(lang)


if __name__ == "__main__":
    asyncio.run(main())
