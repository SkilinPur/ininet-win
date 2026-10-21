import pytest

from ininet_win.i18n import translator
from ininet_win.tui.app import IninetTuiApp


@pytest.fixture(autouse=True)
def _lang_en():
    translator.set_language("en")
    yield
    translator.set_language("en")


async def test_app_mounts_with_five_tabs() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tabs = [pane.id for pane in app.query("TabPane")]
        assert tabs == ["scan", "watch", "top", "map", "history"]
        await pilot.press("q")


async def test_tab_switch_by_digit() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        await pilot.press("3")
        assert app.query_one("TabbedContent").active == "top"
        await pilot.press("4")
        assert app.query_one("TabbedContent").active == "map"
        await pilot.press("5")
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


def _scan_rows():
    return [
        ("10.0.0.9", "-", "80", "80/http"),
        ("10.0.0.1", "-", "22", "22/ssh"),
        ("10.0.0.22", "-", "443", "443/https"),
    ]


async def test_scan_search_filters_rows() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tab = app.query_one("ScanTab")
        tab.set_rows(_scan_rows())
        await pilot.pause()
        tab._search = "443"
        tab._redraw()
        await pilot.pause()
        assert app.query_one("#scan-table").row_count == 1
        await pilot.press("q")


async def test_scan_search_via_input() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tab = app.query_one("ScanTab")
        tab.set_rows(_scan_rows())
        search = app.query_one("#scan-table-search")
        search.value = "10.0.0.9"
        await pilot.pause()
        assert app.query_one("#scan-table").row_count == 1
        await pilot.press("q")


async def test_scan_sort_by_ip_numeric() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tab = app.query_one("ScanTab")
        tab.set_rows(_scan_rows())
        await pilot.pause()
        tab._sort_col = 0
        tab._sort_desc = False
        tab._redraw()
        await pilot.pause()
        table = app.query_one("#scan-table")
        ips = [table.get_row_at(i)[0] for i in range(table.row_count)]
        assert ips == ["10.0.0.1", "10.0.0.9", "10.0.0.22"]
        tab._sort_desc = True
        tab._redraw()
        await pilot.pause()
        ips = [table.get_row_at(i)[0] for i in range(table.row_count)]
        assert ips == ["10.0.0.22", "10.0.0.9", "10.0.0.1"]
        await pilot.press("q")


async def test_scan_sort_by_port_column() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        tab = app.query_one("ScanTab")
        tab.set_rows(_scan_rows())
        await pilot.pause()
        tab._sort_col = 3
        tab._redraw()
        await pilot.pause()
        table = app.query_one("#scan-table")
        services = [table.get_row_at(i)[3] for i in range(table.row_count)]
        assert services == ["22/ssh", "443/https", "80/http"]
        await pilot.press("q")


async def test_slash_focuses_search() -> None:
    app = IninetTuiApp()
    async with app.run_test() as pilot:
        await pilot.press("/")
        focused = app.focused
        assert focused is not None and focused.id == "scan-table-search"
        await pilot.press("q")
