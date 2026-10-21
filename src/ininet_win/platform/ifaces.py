"""Discover local networks and interfaces (Windows)."""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass

import psutil


@dataclass(frozen=True)
class Interface:
    """A local network interface with an IPv4 address."""

    name: str
    address: str
    netmask: str
    network: str

    def as_row(self) -> tuple[str, str, str, str]:
        return (self.name, self.address, self.netmask, self.network)


def _is_usable_ipv4(addr: str) -> bool:
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if ip.version != 4:
        return False
    return not (ip.is_loopback or ip.is_link_local)


def get_interfaces() -> list[Interface]:
    """Return local IPv4 interfaces with their networks, excluding loopback/link-local."""
    result: list[Interface] = []
    stats = psutil.net_if_stats()
    for name, addrs in psutil.net_if_addrs().items():
        iface_stats = stats.get(name)
        if iface_stats is not None and not iface_stats.isup:
            continue
        for addr in addrs:
            family = getattr(addr, "family", None)
            if family is None or int(family) != socket.AF_INET:
                continue
            if not addr.address or not addr.netmask:
                continue
            if not _is_usable_ipv4(addr.address):
                continue
            try:
                network = ipaddress.ip_network(
                    f"{addr.address}/{addr.netmask}", strict=False
                )
            except ValueError:
                continue
            result.append(
                Interface(
                    name=name,
                    address=addr.address,
                    netmask=addr.netmask,
                    network=str(network),
                )
            )
    return result


def get_local_ipv4() -> list[str]:
    """Return local non-loopback IPv4 addresses."""
    return [iface.address for iface in get_interfaces()]
