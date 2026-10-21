"""High-level scan orchestration: host discovery + port scanning."""

from __future__ import annotations

from dataclasses import dataclass, field

from ininet_win.core.netutil import iter_hosts, parse_network
from ininet_win.core.ports import parse_ports
from ininet_win.core.scanner import scan_host_ports, service_name
from ininet_win.platform.icmp import ping_sweep
from ininet_win.platform.neighbors import get_neighbours, mac_by_ip


@dataclass
class PortResult:
    port: int
    service: str


@dataclass
class HostResult:
    ip: str
    mac: str = ""
    ports: list[PortResult] = field(default_factory=list)


@dataclass
class ScanResult:
    network: str
    hosts: list[HostResult] = field(default_factory=list)

    @property
    def host_count(self) -> int:
        return len(self.hosts)

    @property
    def open_port_count(self) -> int:
        return sum(len(h.ports) for h in self.hosts)


async def scan_network(
    cidr: str,
    ports_spec: str = "1-1024",
    *,
    ping_timeout: float = 1.0,
    port_timeout: float = 0.5,
    concurrency: int = 128,
    scan_ports: bool = True,
) -> ScanResult:
    """Scan a network: discover live hosts, optionally scan their ports.

    Makes a single network object; ping-sweeps all hosts concurrently; for the
    live ones, scans the requested ports.
    """
    network = parse_network(cidr)
    host_list = list(iter_hosts(network))
    ports = parse_ports(ports_spec) if scan_ports else []

    alive = await ping_sweep(host_list, concurrency=concurrency, timeout=ping_timeout)
    macs = mac_by_ip(get_neighbours())

    result = ScanResult(network=str(network))
    for ip in alive:
        host = HostResult(ip=ip, mac=macs.get(ip, ""))
        if ports:
            open_ports = await scan_host_ports(
                ip, ports, timeout=port_timeout, concurrency=256
            )
            host.ports = [
                PortResult(port=p, service=service_name(p)) for p in open_ports
            ]
        result.hosts.append(host)
    return result
