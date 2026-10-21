from ininet_win.core import traffic as traffic_mod
from ininet_win.core.traffic import (
    InterfaceTraffic,
    TrafficSnapshot,
    format_bytes,
    format_rate,
    is_noise,
)


def test_format_bytes() -> None:
    assert format_bytes(0) == "0 B"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1024) == "1.0 KB"
    assert format_bytes(1024 * 1024 * 3) == "3.0 MB"


def test_format_rate() -> None:
    assert format_rate(2048) == "2.0 KB/s"


def test_is_noise() -> None:
    assert is_noise("Loopback Pseudo-Interface 1")
    assert is_noise("isatap.example.com")
    assert not is_noise("Ethernet")


def test_rates_between_snapshots() -> None:
    prev = TrafficSnapshot(
        timestamp=100.0,
        interfaces={"Ethernet": {"bytes_sent": 0, "bytes_recv": 0}},
    )
    curr = TrafficSnapshot(
        timestamp=102.0,
        interfaces={
            "Ethernet": {"bytes_sent": 200, "bytes_recv": 400},
        },
    )
    item = curr.rates(prev)["Ethernet"]
    assert item.send_bps == 100.0
    assert item.recv_bps == 200.0
    assert item.total == 600


def test_rates_without_previous() -> None:
    snap = TrafficSnapshot(
        timestamp=5.0, interfaces={"Ethernet": {"bytes_sent": 10, "bytes_recv": 20}}
    )
    item = snap.rates(None)["Ethernet"]
    assert item.recv_bps == 0.0
    assert item.send_bps == 0.0


def test_rates_handle_counter_reset() -> None:
    prev = TrafficSnapshot(
        timestamp=10.0, interfaces={"eth": {"bytes_sent": 1000, "bytes_recv": 1000}}
    )
    curr = TrafficSnapshot(
        timestamp=11.0, interfaces={"eth": {"bytes_sent": 100, "bytes_recv": 100}}
    )
    item = curr.rates(prev)["eth"]
    assert item.recv_bps == 0.0
    assert item.send_bps == 0.0


def test_interface_traffic_total_bps() -> None:
    item = InterfaceTraffic(name="eth", send_bps=100, recv_bps=50)
    assert item.total_bps == 150


def test_capture_uses_platform(monkeypatch) -> None:
    monkeypatch.setattr(
        traffic_mod,
        "interface_counters",
        lambda: {"Ethernet": {"bytes_sent": 1, "bytes_recv": 2}},
    )
    snap = TrafficSnapshot.capture()
    assert "Ethernet" in snap.interfaces
