from ininet_win.core.monitor import (
    Connection,
    Filter,
    group_by_process,
)


def _conn(**kw) -> Connection:
    base = dict(
        proto="tcp",
        laddr="127.0.0.1",
        lport=50000,
        raddr="93.184.216.34",
        rport=443,
        status="ESTABLISHED",
        pid=1234,
        process="chrome.exe",
    )
    base.update(kw)
    return Connection(**base)


def test_local_remote_format() -> None:
    c = _conn()
    assert c.local == "127.0.0.1:50000"
    assert c.remote == "93.184.216.34:443"


def test_local_remote_empty() -> None:
    c = _conn(laddr="", lport=0, raddr="", rport=0)
    assert c.local == ""
    assert c.remote == ""


def test_filter_process() -> None:
    f = Filter(process="chrome")
    assert f.matches(_conn(process="chrome.exe"))
    assert not f.matches(_conn(process="firefox.exe"))


def test_filter_port() -> None:
    f = Filter(port=443)
    assert f.matches(_conn(rport=443))
    assert f.matches(_conn(lport=443))
    assert not f.matches(_conn(lport=80, rport=80))


def test_filter_host() -> None:
    f = Filter(host="93.184.216.34")
    assert f.matches(_conn())
    assert not f.matches(_conn(raddr="1.1.1.1"))


def test_filter_status() -> None:
    f = Filter(status="LISTEN")
    assert f.matches(_conn(status="LISTEN"))
    assert not f.matches(_conn(status="ESTABLISHED"))


def test_filter_connected_only() -> None:
    f = Filter(connected_only=True)
    assert f.matches(_conn())
    assert not f.matches(_conn(raddr="", rport=0))


def test_filter_combined() -> None:
    f = Filter(process="chrome", port=443, connected_only=True)
    assert f.matches(_conn())
    assert not f.matches(_conn(process="firefox.exe"))


def test_group_by_process() -> None:
    conns = [
        _conn(process="chrome.exe", pid=1, raddr="1.1.1.1", rport=443),
        _conn(process="chrome.exe", pid=1, raddr="2.2.2.2", rport=80),
        _conn(process="svchost.exe", pid=2, raddr="3.3.3.3", rport=53),
    ]
    groups = group_by_process(conns)
    assert groups[0].process == "chrome.exe"
    assert groups[0].count == 2
    assert groups[0].remote_hosts == {"1.1.1.1", "2.2.2.2"}
    assert groups[0].remote_ports == {443, 80}
    assert groups[1].process == "svchost.exe"
    assert groups[1].count == 1
