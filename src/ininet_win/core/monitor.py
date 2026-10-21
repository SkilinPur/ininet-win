"""Live connection monitoring: model, filters and aggregation.

Read-only. Never opens or closes connections.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ininet_win.platform.connections import list_connections


@dataclass
class Connection:
    proto: str
    laddr: str
    lport: int
    raddr: str
    rport: int
    status: str
    pid: int | None
    process: str

    @classmethod
    def from_raw(cls, raw: dict[str, object]) -> Connection:
        return cls(
            proto=str(raw.get("family", "")),
            laddr=str(raw.get("laddr", "")),
            lport=int(raw.get("lport", 0) or 0),
            raddr=str(raw.get("raddr", "")),
            rport=int(raw.get("rport", 0) or 0),
            status=str(raw.get("status", "")),
            pid=raw.get("pid") if isinstance(raw.get("pid"), int) else None,
            process=str(raw.get("process", "")),
        )

    @property
    def local(self) -> str:
        return f"{self.laddr}:{self.lport}" if self.laddr else ""

    @property
    def remote(self) -> str:
        return f"{self.raddr}:{self.rport}" if self.raddr else ""


@dataclass
class Filter:
    """Filter for connections. All fields optional; empty means no filtering."""

    process: str = ""
    port: int | None = None
    host: str = ""
    status: str = ""
    connected_only: bool = False

    def matches(self, conn: Connection) -> bool:
        if self.process and self.process.lower() not in conn.process.lower():
            return False
        if self.status and self.status.lower() != conn.status.lower():
            return False
        if self.port is not None and self.port not in (conn.lport, conn.rport):
            return False
        if self.host and self.host not in (conn.raddr, conn.laddr):
            return False
        if self.connected_only and not conn.raddr:
            return False
        return True


def get_connections(filt: Filter | None = None) -> list[Connection]:
    """Snapshot of current connections, optionally filtered."""
    conns = [Connection.from_raw(raw) for raw in list_connections()]
    if filt is not None:
        conns = [c for c in conns if filt.matches(c)]
    return conns


@dataclass
class ProcessGroup:
    pid: int | None
    process: str
    count: int = 0
    remote_hosts: set[str] = field(default_factory=set)
    remote_ports: set[int] = field(default_factory=set)


def unresolved_count(conns: list[Connection]) -> int:
    """Number of connections whose owning process could not be resolved.

    On Windows this usually means the process belongs to another user and the
    current shell lacks administrator rights.
    """
    return sum(1 for c in conns if c.process == "")


def group_by_process(conns: list[Connection]) -> list[ProcessGroup]:
    groups: dict[tuple[int | None, str], ProcessGroup] = {}
    for conn in conns:
        key = (conn.pid, conn.process)
        group = groups.get(key)
        if group is None:
            group = ProcessGroup(pid=conn.pid, process=conn.process)
            groups[key] = group
        group.count += 1
        if conn.raddr:
            group.remote_hosts.add(conn.raddr)
        if conn.rport:
            group.remote_ports.add(conn.rport)
    return sorted(groups.values(), key=lambda g: g.count, reverse=True)
