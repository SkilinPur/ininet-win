import pytest

from ininet_win.i18n import translator
from ininet_win.tui.app import IninetTuiApp


@pytest.fixture(autouse=True)
def _lang_en():
    translator.set_language("en")
    yield
    translator.set_language("en")


async def test_app_mounts_with_four_tabs() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tabs = [pane.id for pane in app.query("TabPane")]
        assert tabs == ["scan", "watch", "top", "history"]
        await pilot.press("q")


async def test_tab_switch_by_digit() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert app.query_one("TabbedContent").active == "top"
        await pilot.press("4")
        assert app.query_one("TabbedContent").active == "history"
        await pilot.press("q")


async def test_scan_without_network_shows_hint() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        app.run_scan()
        await pilot.pause()
        status = app.query_one("#status").content
        assert str(status) == "Enter a network in CIDR, e.g. 10.0.0.0/24."
        await pilot.press("q")


async def test_watch_tick_updates_rows(monkeypatch) -> None:
    from ininet_win.core.monitor import Connection

    conns = [
        Connection(
            proto="tcp",
            laddr="10.0.0.5",
            lport=5000,
            raddr="203.0.113.10",
            rport=443,
            status="ESTABLISHED",
            pid=42,
            process="app.exe",
        )
    ]
    monkeypatch.setattr(
        "ininet_win.core.monitor.get_connections", lambda filt=None: conns
    )
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        app._tick_watch()
        await pilot.pause()
        table = app.query_one("#watch-table")
        assert table.row_count == 1
        await pilot.press("q")


async def test_top_refresh(monkeypatch) -> None:
    from ininet_win.core.monitor import Connection

    conns = [
        Connection("tcp", "10.0.0.5", 5000, "203.0.113.10", 443, "ESTABLISHED", 7, "svc.exe"),
        Connection("tcp", "10.0.0.5", 5001, "203.0.113.10", 443, "ESTABLISHED", 7, "svc.exe"),
    ]
    monkeypatch.setattr(
        "ininet_win.core.monitor.get_connections", lambda filt=None: conns
    )
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        app.refresh_top()
        await pilot.pause()
        table = app.query_one("#top-table")
        assert table.row_count == 1
        await pilot.press("q")


async def test_history_refresh(monkeypatch, tmp_path) -> None:
    from ininet_win.core.scan import HostResult, ScanResult
    from ininet_win.storage.db import Database

    db = tmp_path / "t.db"
    database = Database(db)
    try:
        database.save_scan(ScanResult(network="10.0.0.0/24", hosts=[HostResult(ip="10.0.0.1")]))
    finally:
        database.close()

    monkeypatch.setattr("ininet_win.storage.db.default_db_path", lambda: db)
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        app.refresh_history()
        await pilot.pause()
        table = app.query_one("#history-table")
        assert table.row_count == 1
        await pilot.press("q")
