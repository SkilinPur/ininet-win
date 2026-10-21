from ininet_win.core.diff import diff_scans
from ininet_win.core.scan import HostResult, PortResult, ScanResult


def _scan(network: str, hosts: list[tuple[str, list[int]]]) -> ScanResult:
    return ScanResult(
        network=network,
        hosts=[
            HostResult(
                ip=ip,
                ports=[PortResult(p, "") for p in ports],
            )
            for ip, ports in hosts
        ],
    )


def test_diff_no_changes() -> None:
    old = _scan("a", [("1.1.1.1", [80])])
    new = _scan("b", [("1.1.1.1", [80])])
    d = diff_scans(old, new)
    assert not d.has_changes


def test_diff_added_host() -> None:
    old = _scan("a", [("1.1.1.1", [80])])
    new = _scan("b", [("1.1.1.1", [80]), ("1.1.1.2", [22])])
    d = diff_scans(old, new)
    assert d.added_hosts == ["1.1.1.2"]
    assert d.removed_hosts == []


def test_diff_removed_host() -> None:
    old = _scan("a", [("1.1.1.1", [80]), ("1.1.1.2", [22])])
    new = _scan("b", [("1.1.1.1", [80])])
    d = diff_scans(old, new)
    assert d.removed_hosts == ["1.1.1.2"]


def test_diff_changed_ports() -> None:
    old = _scan("a", [("1.1.1.1", [80, 443])])
    new = _scan("b", [("1.1.1.1", [443, 8080])])
    d = diff_scans(old, new)
    assert len(d.changed_hosts) == 1
    assert d.changed_hosts[0].ip == "1.1.1.1"
    assert d.changed_hosts[0].added_ports == [8080]
    assert d.changed_hosts[0].removed_ports == [80]


def test_diff_networks_recorded() -> None:
    d = diff_scans(_scan("old-net", []), _scan("new-net", []))
    assert d.old_network == "old-net"
    assert d.new_network == "new-net"
