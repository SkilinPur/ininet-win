"""SQLite storage for scan snapshots (Windows)."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from ininet_win.core.scan import HostResult, PortResult, ScanResult

SCHEMA_VERSION = 1


def default_db_path() -> Path:
    """Default database path: ``%LOCALAPPDATA%\\ininet\\ininet.db``."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".ininet"
    return root / "ininet" / "ininet.db"


@dataclass
class Snapshot:
    id: int
    network: str
    created_at: str
    host_count: int
    open_port_count: int


class Database:
    """Thin wrapper around a SQLite file holding scan snapshots."""

    def __init__(self, path: str | os.PathLike[str] | None = None) -> None:
        self.path = Path(path) if path is not None else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS hosts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
                    ip TEXT NOT NULL,
                    mac TEXT NOT NULL DEFAULT ''
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    host_id INTEGER NOT NULL REFERENCES hosts(id) ON DELETE CASCADE,
                    port INTEGER NOT NULL,
                    service TEXT NOT NULL DEFAULT ''
                )
                """
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hosts_snapshot ON hosts(snapshot_id)"
            )
            self.conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ports_host ON ports(host_id)"
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def save_scan(self, result: ScanResult) -> int:
        """Persist a scan result, returning the snapshot id."""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO snapshots(network) VALUES (?)", (result.network,)
            )
            snapshot_id = int(cursor.lastrowid)
            for host in result.hosts:
                host_cursor = self.conn.execute(
                    "INSERT INTO hosts(snapshot_id, ip, mac) VALUES (?, ?, ?)",
                    (snapshot_id, host.ip, host.mac),
                )
                host_id = int(host_cursor.lastrowid)
                for port in host.ports:
                    self.conn.execute(
                        "INSERT INTO ports(host_id, port, service) VALUES (?, ?, ?)",
                        (host_id, port.port, port.service),
                    )
        return snapshot_id

    def list_snapshots(self, limit: int = 50) -> list[Snapshot]:
        """Return recent snapshots, newest first."""
        rows = self.conn.execute(
            """
            SELECT s.id, s.network, s.created_at,
                   (SELECT COUNT(*) FROM hosts h WHERE h.snapshot_id = s.id) AS host_count,
                   (SELECT COUNT(*) FROM ports p
                      JOIN hosts h ON h.id = p.host_id
                     WHERE h.snapshot_id = s.id) AS open_port_count
            FROM snapshots s
            ORDER BY s.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            Snapshot(
                id=row["id"],
                network=row["network"],
                created_at=row["created_at"],
                host_count=row["host_count"],
                open_port_count=row["open_port_count"],
            )
            for row in rows
        ]

    def get_snapshot(self, snapshot_id: int) -> ScanResult | None:
        """Load a scan result by snapshot id."""
        snap = self.conn.execute(
            "SELECT network FROM snapshots WHERE id = ?", (snapshot_id,)
        ).fetchone()
        if snap is None:
            return None
        host_rows = self.conn.execute(
            "SELECT id, ip, mac FROM hosts WHERE snapshot_id = ? ORDER BY ip",
            (snapshot_id,),
        ).fetchall()
        result = ScanResult(network=snap["network"])
        for host_row in host_rows:
            port_rows = self.conn.execute(
                "SELECT port, service FROM ports WHERE host_id = ? ORDER BY port",
                (host_row["id"],),
            ).fetchall()
            result.hosts.append(
                HostResult(
                    ip=host_row["ip"],
                    mac=host_row["mac"],
                    ports=[
                        PortResult(port=p["port"], service=p["service"])
                        for p in port_rows
                    ],
                )
            )
        return result

    def delete_snapshot(self, snapshot_id: int) -> bool:
        with self.conn:
            cursor = self.conn.execute(
                "DELETE FROM snapshots WHERE id = ?", (snapshot_id,)
            )
        return cursor.rowcount > 0

    def prune(self, keep: int = 100) -> int:
        """Delete oldest snapshots, keeping the ``keep`` most recent ones."""
        rows = self.conn.execute(
            "SELECT id FROM snapshots ORDER BY id DESC LIMIT -1 OFFSET ?", (keep,)
        ).fetchall()
        ids = [row["id"] for row in rows]
        for snapshot_id in ids:
            self.delete_snapshot(snapshot_id)
        return len(ids)

    def close(self) -> None:
        self.conn.close()
