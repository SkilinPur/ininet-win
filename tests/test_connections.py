from unittest import mock

from ininet_win.platform import connections


class _FakeConn:
    def __init__(self, laddr, raddr, status, pid, sock_type_name="SOCK_STREAM"):
        self.laddr = laddr
        self.raddr = raddr
        self.status = status
        self.pid = pid
        self.type = mock.Mock(name=sock_type_name)
        self.type.name = sock_type_name


def test_list_connections_maps_fields() -> None:
    fake = [
        _FakeConn(("0.0.0.0", 135), (), "LISTEN", 4),
        _FakeConn(("127.0.0.1", 50000), ("1.1.1.1", 443), "ESTABLISHED", 100),
    ]
    with (
        mock.patch.object(connections.psutil, "net_connections", return_value=fake),
        mock.patch.object(connections.psutil, "Process") as proc,
    ):
        proc.return_value.name.return_value = "svchost.exe"
        result = connections.list_connections()

    assert len(result) == 2
    assert result[0]["lport"] == 135
    assert result[0]["raddr"] == ""
    assert result[0]["status"] == "LISTEN"
    assert result[1]["raddr"] == "1.1.1.1"
    assert result[1]["rport"] == 443
    assert result[1]["process"] == "svchost.exe"


def test_list_connections_access_denied() -> None:
    with mock.patch.object(
        connections.psutil,
        "net_connections",
        side_effect=connections.psutil.AccessDenied,
    ):
        assert connections.list_connections() == []


def test_list_connections_no_pid() -> None:
    fake = [_FakeConn(("0.0.0.0", 80), (), "LISTEN", None)]
    with mock.patch.object(connections.psutil, "net_connections", return_value=fake):
        result = connections.list_connections()
    assert result[0]["pid"] is None
    assert result[0]["process"] == ""


def test_udp_detection() -> None:
    fake = [_FakeConn(("0.0.0.0", 5353), (), "", 5, sock_type_name="SOCK_DGRAM")]
    with (
        mock.patch.object(connections.psutil, "net_connections", return_value=fake),
        mock.patch.object(connections.psutil, "Process") as proc,
    ):
        proc.return_value.name.return_value = "svc.exe"
        result = connections.list_connections()
    assert result[0]["family"] == "udp"
