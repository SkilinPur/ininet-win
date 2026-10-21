import pytest

from ininet_win.core.ports import parse_ports


def test_parse_ports_single() -> None:
    assert parse_ports("80") == [80]


def test_parse_ports_list() -> None:
    assert parse_ports("443,22,80") == [22, 80, 443]


def test_parse_ports_range() -> None:
    assert parse_ports("1-4") == [1, 2, 3, 4]


def test_parse_ports_mixed() -> None:
    assert parse_ports("22,80-82,443") == [22, 80, 81, 82, 443]


def test_parse_ports_dedup() -> None:
    assert parse_ports("80,80,80") == [80]


def test_parse_ports_reversed_range() -> None:
    assert parse_ports("5-3") == [3, 4, 5]


def test_parse_ports_empty() -> None:
    with pytest.raises(ValueError):
        parse_ports("")


def test_parse_ports_out_of_range() -> None:
    with pytest.raises(ValueError):
        parse_ports("0")
    with pytest.raises(ValueError):
        parse_ports("70000")


def test_parse_ports_invalid() -> None:
    with pytest.raises(ValueError):
        parse_ports("abc")
    with pytest.raises(ValueError):
        parse_ports("1-x")
