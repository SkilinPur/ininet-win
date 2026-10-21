import pytest

from ininet_win.core.scan import HostResult, PortResult, ScanResult
from ininet_win.storage.db import Database


def _scan(network: str = "192.168.0.0/24") -> ScanResult:
    return ScanResult(
        network=network,
        hosts=[
            HostResult(
                ip="192.168.0.1",
                mac="AA-BB-CC-DD-EE-FF",
                ports=[PortResult(80, "http"), PortResult(443, "https")],
            ),
            HostResult(ip="192.168.0.2", mac="", ports=[]),
        ],
    )


@pytest.fixture
def db(tmp_path) -> Database:
    database = Database(tmp_path / "test.db")
    yield database
    database.close()


def test_save_and_load(db: Database) -> None:
    snapshot_id = db.save_scan(_scan())
    assert snapshot_id == 1
    loaded = db.get_snapshot(snapshot_id)
    assert loaded is not None
    assert loaded.network == "192.168.0.0/24"
    assert [h.ip for h in loaded.hosts] == ["192.168.0.1", "192.168.0.2"]
    assert [p.port for p in loaded.hosts[0].ports] == [80, 443]
    assert loaded.hosts[0].ports[0].service == "http"


def test_get_missing_snapshot(db: Database) -> None:
    assert db.get_snapshot(999) is None


def test_list_snapshots(db: Database) -> None:
    db.save_scan(_scan("10.0.0.0/30"))
    db.save_scan(_scan("192.168.1.0/24"))
    snaps = db.list_snapshots()
    assert len(snaps) == 2
    assert snaps[0].network == "192.168.1.0/24"  # newest first
    assert snaps[0].host_count == 2
    assert snaps[0].open_port_count == 2


def test_list_snapshots_limit(db: Database) -> None:
    for _ in range(5):
        db.save_scan(_scan())
    assert len(db.list_snapshots(limit=3)) == 3


def test_delete_snapshot(db: Database) -> None:
    snapshot_id = db.save_scan(_scan())
    assert db.delete_snapshot(snapshot_id) is True
    assert db.get_snapshot(snapshot_id) is None
    assert db.delete_snapshot(snapshot_id) is False


def test_prune(db: Database) -> None:
    for _ in range(5):
        db.save_scan(_scan())
    removed = db.prune(keep=2)
    assert removed == 3
    assert len(db.list_snapshots()) == 2


def test_cascade_delete(db: Database) -> None:
    snapshot_id = db.save_scan(_scan())
    db.delete_snapshot(snapshot_id)
    hosts = db.conn.execute("SELECT COUNT(*) AS c FROM hosts").fetchone()["c"]
    ports = db.conn.execute("SELECT COUNT(*) AS c FROM ports").fetchone()["c"]
    assert hosts == 0
    assert ports == 0


def test_persist_across_reopen(tmp_path) -> None:
    path = tmp_path / "persist.db"
    first = Database(path)
    first.save_scan(_scan())
    first.close()

    second = Database(path)
    assert len(second.list_snapshots()) == 1
    second.close()
