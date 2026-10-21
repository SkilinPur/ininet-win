"""Network topology: a host graph built from scans and live connections.

Two edge sources are combined:

* ``scan``  - the local subnet(s) link to every host discovered by a scan.
* ``live``  - currently established connections (local or discovered host to a
  remote peer), aggregated by endpoint pair.

The model is deliberately dependency-free so it can be rendered as ASCII in the
CLI or as a table in the TUI.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field

from ininet_win.core.monitor import Connection
from ininet_win.core.scan import ScanResult
from ininet_win.platform.ifaces import get_interfaces

LOCAL = "local"
SUBNET = "subnet"
HOST = "host"
REMOTE = "remote"

SCAN_EDGE = "scan"
LIVE_EDGE = "live"


@dataclass
class Node:
    id: str
    kind: str
    mac: str = ""
    ports: list[int] = field(default_factory=list)

    @property
    def label(self) -> str:
        if self.kind == LOCAL:
            return f"{self.id} (local)"
        if self.kind == SUBNET:
            return f"{self.id} (subnet)"
        return self.id


@dataclass
class Edge:
    src: str
    dst: str
    kind: str
    count: int = 1
    ports: list[int] = field(default_factory=list)


@dataclass
class Topology:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        existing = self.nodes.get(node.id)
        if existing is None:
            self.nodes[node.id] = node
            return
        if not existing.mac and node.mac:
            existing.mac = node.mac
        if node.kind == HOST and existing.kind == REMOTE:
            existing.kind = HOST
        for port in node.ports:
            if port not in existing.ports:
                existing.ports.append(port)
        existing.ports.sort()

    def add_edge(self, src: str, dst: str, kind: str, ports: list[int]) -> None:
        for edge in self.edges:
            if {edge.src, edge.dst} == {src, dst} and edge.kind == kind:
                edge.count += 1
                for port in ports:
                    if port not in edge.ports:
                        edge.ports.append(port)
                edge.ports.sort()
                return
        self.edges.append(Edge(src=src, dst=dst, kind=kind, ports=sorted(ports)))

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    def neighbors(self, node_id: str) -> list[tuple[str, Edge]]:
        """Return (other_node_id, edge) pairs incident to ``node_id``."""
        out: list[tuple[str, Edge]] = []
        for edge in self.edges:
            if edge.src == node_id:
                out.append((edge.dst, edge))
            elif edge.dst == node_id:
                out.append((edge.src, edge))
        return out

    def roots(self) -> list[str]:
        """Local and subnet nodes, for use as tree roots."""
        return [
            nid for nid, node in self.nodes.items() if node.kind in (LOCAL, SUBNET)
        ]


def _networks_of(
    interfaces: list, seed_ip: str | None = None
) -> list[ipaddress.IPv4Network]:
    networks: list[ipaddress.IPv4Network] = []
    for iface in interfaces:
        if seed_ip is not None and iface.address != seed_ip:
            continue
        try:
            net = ipaddress.ip_network(iface.network, strict=False)
        except ValueError:
            continue
        if net not in networks:
            networks.append(net)
    return networks


def _network_of(ip: str, networks: list[ipaddress.IPv4Network]) -> str | None:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    for net in networks:
        if addr in net:
            return str(net)
    return None


def build_topology(
    scan: ScanResult | None = None,
    connections: list[Connection] | None = None,
    *,
    include_live: bool = True,
) -> Topology:
    """Combine scan results and live connections into a single topology graph.

    A synthetic ``local`` node represents this machine; each local subnet
    becomes a ``subnet`` node. Discovered hosts attach to their subnet via
    ``scan`` edges. Live connections add ``live`` edges between the local (or
    discovered) endpoint and the remote peer.
    """
    topo = Topology()
    interfaces = get_interfaces()
    local_ips = [iface.address for iface in interfaces]
    networks = _networks_of(interfaces)

    for ip in local_ips:
        topo.add_node(Node(id=ip, kind=LOCAL))

    if scan is not None:
        try:
            net = ipaddress.ip_network(scan.network, strict=False)
            if net not in networks:
                networks.append(net)
        except ValueError:
            pass
        for host in scan.hosts:
            topo.add_node(
                Node(
                    id=host.ip,
                    kind=HOST,
                    mac=host.mac,
                    ports=[p.port for p in host.ports],
                )
            )
            subnet = _network_of(host.ip, networks)
            root = subnet or (local_ips[0] if local_ips else scan.network)
            if subnet:
                topo.add_node(Node(id=subnet, kind=SUBNET))
            topo.add_edge(root, host.ip, SCAN_EDGE, [p.port for p in host.ports])

    if include_live and connections:
        for conn in connections:
            if not conn.raddr:
                continue
            endpoint = conn.laddr if conn.laddr in topo.nodes else _owner_of(conn, topo)
            if endpoint is None:
                continue
            topo.add_node(Node(id=conn.raddr, kind=REMOTE))
            topo.add_edge(endpoint, conn.raddr, LIVE_EDGE, [conn.rport])

    return topo


def _owner_of(conn: Connection, topo: Topology) -> str | None:
    """Pick the node that owns a live connection's local endpoint."""
    if conn.laddr:
        if conn.laddr not in topo.nodes:
            topo.add_node(Node(id=conn.laddr, kind=LOCAL))
        return conn.laddr
    local = topo.roots()
    return local[0] if local else None
