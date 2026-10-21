from ininet_win.core.services import KNOWN_SERVICES, service_name


def test_known_services_lookup() -> None:
    assert service_name(22) == "ssh"
    assert service_name(80) == "http"
    assert service_name(3306) == "mysql"
    assert service_name(6379) == "redis"


def test_unknown_port_falls_back_to_osdb() -> None:
    # A valid port with no builtin entry: OS db or empty string, never raises.
    assert isinstance(service_name(65000), str)


def test_table_has_no_empty_names() -> None:
    assert all(name for name in KNOWN_SERVICES.values())
