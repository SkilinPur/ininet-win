import pytest

from ininet_win.core.netutil import count_hosts, iter_hosts, parse_network


def test_parse_network_cidr() -> None:
    net = parse_network("192.168.1.0/24")
    assert str(net) == "192.168.1.0/24"
    assert net.num_addresses == 256


def test_parse_network_bare_address() -> None:
    net = parse_network("192.168.1.5")
    assert str(net) == "192.168.1.5/32"


def test_parse_network_invalid() -> None:
    with pytest.raises(ValueError):
        parse_network("not-a-network")


def test_iter_hosts_slash24() -> None:
    hosts = list(iter_hosts(parse_network("192.168.1.0/24")))
    assert hosts[0] == "192.168.1.1"
    assert hosts[-1] == "192.168.1.254"
    assert len(hosts) == 254


def test_iter_hosts_single() -> None:
    hosts = list(iter_hosts(parse_network("10.0.0.1/32")))
    assert hosts == ["10.0.0.1"]


def test_iter_hosts_slash30() -> None:
    hosts = list(iter_hosts(parse_network("10.0.0.0/30")))
    assert hosts == ["10.0.0.1", "10.0.0.2"]


def test_count_hosts() -> None:
    assert count_hosts(parse_network("10.0.0.0/29")) == 6
