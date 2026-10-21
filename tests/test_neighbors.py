from unittest import mock

from ininet_win.platform.neighbors import Neighbour, mac_by_ip

SAMPLE = """
Interface: 192.168.0.100 --- 0x5
  Internet Address      Physical Address      Type
  192.168.0.1           aa-bb-cc-dd-ee-01     dynamic
  192.168.0.55          00-11-22-33-44-55     dynamic
  192.168.0.255         ff-ff-ff-ff-ff-ff     static
"""


def _run_arp(sample: str) -> list[Neighbour]:
    from ininet_win.platform import neighbors

    completed = mock.Mock()
    completed.stdout = sample
    with mock.patch.object(neighbors.subprocess, "run", return_value=completed):
        return neighbors.get_neighbours()


def test_parse_arp() -> None:
    result = _run_arp(SAMPLE)
    assert len(result) == 3
    assert result[0].ip == "192.168.0.1"
    assert result[0].mac == "AA-BB-CC-DD-EE-01"
    assert result[0].kind == "dynamic"


def test_parse_arp_empty() -> None:
    assert _run_arp("") == []


def test_mac_by_ip() -> None:
    ns = [Neighbour("1.1.1.1", "AA-AA-AA-AA-AA-AA", "dynamic")]
    assert mac_by_ip(ns) == {"1.1.1.1": "AA-AA-AA-AA-AA-AA"}
