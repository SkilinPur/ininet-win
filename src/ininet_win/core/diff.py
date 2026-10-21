"""Compare two scan snapshots: what appeared and what disappeared."""

from __future__ import annotations

from dataclasses import dataclass, field

from ininet_win.core.scan import ScanResult


@dataclass
class HostChange:
    ip: str
    added_ports: list[int] = field(default_factory=list)
    removed_ports: list[int] = field(default_factory=list)


@dataclass
class DiffResult:
    old_network: str
    new_network: str
    added_hosts: list[str] = field(default_factory=list)
    removed_hosts: list[str] = field(default_factory=list)
    changed_hosts: list[HostChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added_hosts or self.removed_hosts or self.changed_hosts)


def _host_port_map(result: ScanResult) -> dict[str, set[int]]:
    return {host.ip: {p.port for p in host.ports} for host in result.hosts}


def diff_scans(old: ScanResult, new: ScanResult) -> DiffResult:
    """Compute the difference between an older and a newer scan."""
    old_map = _host_port_map(old)
    new_map = _host_port_map(new)

    old_ips = set(old_map)
    new_ips = set(new_map)

    diff = DiffResult(old_network=old.network, new_network=new.network)
    diff.added_hosts = sorted(new_ips - old_ips)
    diff.removed_hosts = sorted(old_ips - new_ips)

    for ip in sorted(old_ips & new_ips):
        added = sorted(new_map[ip] - old_map[ip])
        removed = sorted(old_map[ip] - new_map[ip])
        if added or removed:
            diff.changed_hosts.append(
                HostChange(ip=ip, added_ports=added, removed_ports=removed)
            )
    return diff
