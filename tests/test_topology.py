from unittest import mock

from ininet_win.core import topology as topo_mod
from ininet_win.core.monitor import Connection
from ininet_win.core.scan import HostResult, PortResult, ScanResult
from ininet_win.core.topology import (
    HOST,
    LIVE_EDGE,
    LOCAL,
    REMOTE,
    SCAN_EDGE,
    build_topology,
)


def _scan() -> ScanResult:
    return ScanResult(
        network="10.0.0.0/24",
        hosts=[
            HostResult(
                ip="10.0.0.1",
                mac="02-00-00-00-00-01",
                ports=[PortResult(80, "http")],
            ),
            HostResult(ip="10.0.0.5", mac="02-00-00-00-00-05"),
        ],
    )


def _conn(laddr: str, raddr: str, rport: int = 443) -> Connection:
    return Connection(
        proto="AF_INET",
        laddr=laddr,
        lport=50000,
        raddr=raddr,
        rport=rport,
        status="ESTABLISHED",
        pid=1,
        process="app.exe",
    )


def test_build_from_scan_only(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    topo = build_topology(_scan(), None)
    assert topo.nodes["10.0.0.1"].kind == HOST
    assert topo.nodes["10.0.0.1"].mac == "02-00-00-00-00-01"
    assert topo.nodes["10.0.0.1"].ports == [80]
    scan_edges = [e for e in topo.edges if e.kind == SCAN_EDGE]
    assert len(scan_edges) == 2
    assert all({e.src, e.dst} <= {"10.0.0.0/24", "10.0.0.1", "10.0.0.5"} for e in scan_edges)


def test_build_from_live_only(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    conns = [
        _conn("192.168.1.10", "8.8.8.8", 53),
        _conn("192.168.1.10", "8.8.8.8", 53),
        _conn("192.168.1.10", "1.1.1.1", 443),
    ]
    topo = build_topology(None, conns)
    assert topo.nodes["8.8.8.8"].kind == REMOTE
    live = [e for e in topo.edges if e.kind == LIVE_EDGE]
    assert len(live) == 2
    dns = next(e for e in live if e.dst == "8.8.8.8")
    assert dns.count == 2
    assert dns.ports == [53]


def test_scan_and_live_merge(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    topo = build_topology(_scan(), [_conn("10.0.0.1", "9.9.9.9", 443)])
    assert topo.nodes["10.0.0.1"].kind == HOST
    kinds = {e.kind for e in topo.edges}
    assert kinds == {SCAN_EDGE, LIVE_EDGE}


def test_include_live_flag(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    topo = build_topology(None, [_conn("10.0.0.2", "9.9.9.9")], include_live=False)
    assert topo.edges == []


def test_roots_and_neighbors(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    topo = build_topology(None, [_conn("10.0.0.2", "9.9.9.9")])
    assert "10.0.0.2" in topo.roots()
    assert topo.nodes["10.0.0.2"].kind == LOCAL
    neighbors = [n for n, _ in topo.neighbors("10.0.0.2")]
    assert "9.9.9.9" in neighbors


def test_real_interfaces_are_local(monkeypatch) -> None:
    class FakeIface:
        def __init__(self, address, network):
            self.address = address
            self.network = network

    monkeypatch.setattr(
        topo_mod,
        "get_interfaces",
        lambda: [FakeIface("10.0.0.2", "10.0.0.0/24")],
    )
    topo = build_topology(_scan(), [_conn("10.0.0.2", "9.9.9.9")])
    assert topo.nodes["10.0.0.2"].kind == LOCAL
    assert any(n.kind == "subnet" for n in topo.nodes.values())


def test_empty_topology(monkeypatch) -> None:
    monkeypatch.setattr(topo_mod, "get_interfaces", lambda: [])
    with mock.patch.object(topo_mod, "get_interfaces", return_value=[]):
        topo = build_topology(None, None)
    assert topo.node_count == 0
    assert topo.edge_count == 0
