import json

from ininet_win.core.scan import HostResult, PortResult, ScanResult
from ininet_win.render import to_json


def test_to_json() -> None:
    result = ScanResult(
        network="192.168.0.0/24",
        hosts=[
            HostResult(
                ip="192.168.0.1",
                mac="AA-BB-CC-DD-EE-FF",
                ports=[PortResult(port=80, service="http")],
            )
        ],
    )
    payload = json.loads(to_json(result))
    assert payload["network"] == "192.168.0.0/24"
    assert payload["hosts"][0]["ip"] == "192.168.0.1"
    assert payload["hosts"][0]["ports"][0] == {"port": 80, "service": "http"}


def test_to_json_empty() -> None:
    result = ScanResult(network="10.0.0.0/30")
    payload = json.loads(to_json(result))
    assert payload == {"network": "10.0.0.0/30", "hosts": []}
