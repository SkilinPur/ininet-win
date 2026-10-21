"""Network address helpers (CIDR parsing, host enumeration)."""

from __future__ import annotations

import ipaddress
from collections.abc import Iterator


def parse_network(cidr: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    """Parse a CIDR string into a network object.

    Accepts ``192.168.1.0/24`` or a bare address (treated as /32 or /128).
    """
    try:
        return ipaddress.ip_network(cidr, strict=False)
    except ValueError as exc:
        raise ValueError(f"invalid network {cidr!r}: {exc}") from exc


def iter_hosts(network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> Iterator[str]:
    """Yield usable host addresses of a network as strings.

    Excludes the network and broadcast addresses for IPv4. For a /32 or a single
    host, yields that address.
    """
    if network.num_addresses <= 2:
        yield str(network.network_address)
        return
    for host in network.hosts():
        yield str(host)


def count_hosts(network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> int:
    """Number of usable host addresses in a network."""
    return sum(1 for _ in iter_hosts(network))
