"""Textual TUI for ininet-win: Scan / Watch / Top / History tabs."""

from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)

from ininet_win.i18n.translator import current_language, t
from ininet_win.language import resolve_language

# Theme matching the project site palette (dark, red accent).
ININET_THEME = Theme(
    name="ininet",
    primary="#e63946",
    secondary="#56d4dd",
    accent="#d2a8ff",
    foreground="#e8e8e8",
    background="#0a0a0a",
    surface="#121212",
    panel="#101010",
    success="#7ee787",
    warning="#e3b341",
    error="#e63946",
    dark=True,
)


def _ports_spec(input_text: str) -> str:
    return input_text.strip() or "1-1024"


class ScanTab(Vertical):
    """Scan a network and show live hosts with open ports."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="scan-controls"):
            yield Label(t("tui.network"), classes="ctl-label")
            yield Input(placeholder="10.0.0.0/24", id="scan-network")
            yield Label(t("tui.ports"), classes="ctl-label")
            yield Input(placeholder="1-1024", id="scan-ports")
            yield Button(t("tui.scan_btn"), id="scan-run", variant="primary")
            yield Button(t("tui.save_btn"), id="scan-save", disabled=True)
        yield DataTable(id="scan-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#scan-table", DataTable)
        table.add_columns(
            t("table.ip"), t("table.mac"), t("table.ports"), t("table.services")
        )
        self._last_result = None

    def set_result(self, result) -> None:
        self._last_result = result
        table = self.query_one("#scan-table", DataTable)
        table.clear()
        for host in result.hosts:
            ports = ", ".join(str(p.port) for p in host.ports) or "-"
            services = ", ".join(
                f"{p.port}/{p.service}" if p.service else str(p.port)
                for p in host.ports
            ) or "-"
            table.add_row(host.ip, host.mac or "-", ports, services)
        self.query_one("#scan-save", Button).disabled = not result.hosts

    @property
    def last_result(self):
        return self._last_result


class WatchTab(Vertical):
    """Live connection monitor with an auto-refresh timer."""

    def compose(self) -> ComposeResult:
        yield Input(placeholder=t("tui.filter"), id="watch-filter")
        yield DataTable(id="watch-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#watch-table", DataTable)
        table.add_columns(
            t("table.proto"),
            t("table.local"),
            t("table.remote"),
            t("table.state"),
            t("table.pid"),
            t("table.process"),
        )

    def refresh_rows(self, conns) -> None:
        table = self.query_one("#watch-table", DataTable)
        table.clear()
        for conn in conns:
            table.add_row(
                conn.proto,
                conn.local or "-",
                conn.remote or "-",
                conn.status or "-",
                str(conn.pid) if conn.pid is not None else "-",
                conn.process or "-",
            )


class TopTab(Vertical):
    """Top processes by number of connections."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-controls"):
            yield Label(t("tui.refresh_btn"), classes="ctl-label")
            yield Button(t("tui.refresh_btn"), id="top-refresh", variant="primary")
        yield DataTable(id="top-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#top-table", DataTable)
        table.add_columns(
            t("table.count"),
            t("table.pid"),
            t("table.process"),
            t("table.remote_hosts"),
            t("table.remote_ports"),
        )

    def refresh_rows(self, groups, limit: int = 50) -> None:
        table = self.query_one("#top-table", DataTable)
        table.clear()
        for group in groups[:limit]:
            hosts = str(len(group.remote_hosts)) if group.remote_hosts else "0"
            ports = ", ".join(str(p) for p in sorted(group.remote_ports)) or "-"
            table.add_row(
                str(group.count),
                str(group.pid) if group.pid is not None else "-",
                group.process or "-",
                hosts,
                ports,
            )


class HistoryTab(Vertical):
    """Saved scan snapshots."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="history-controls"):
            yield Button(t("tui.refresh_btn"), id="history-refresh", variant="primary")
        yield DataTable(id="history-table", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one("#history-table", DataTable)
        table.add_columns(
            t("table.id"),
            t("table.created"),
            t("table.network"),
            t("table.hosts"),
            t("table.open_ports"),
        )

    def refresh_rows(self, snapshots) -> None:
        table = self.query_one("#history-table", DataTable)
        table.clear()
        for snap in snapshots:
            table.add_row(
                str(snap.id),
                snap.created_at,
                snap.network,
                str(snap.host_count),
                str(snap.open_port_count),
            )


class IninetTuiApp(App):
    """The ininet-win terminal user interface."""

    CSS = """
    Screen { layout: vertical; }
    #scan-controls, #top-controls, #history-controls { height: auto; padding: 1 1 0 1; }
    .ctl-label { padding: 1 1 0 0; }
    #scan-network { width: 24; }
    #scan-ports { width: 16; }
    #scan-run, #scan-save, #top-refresh, #history-refresh { margin: 0 1; }
    #watch-filter { margin: 1 1 0 1; }
    DataTable { height: 1fr; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "show_tab('scan')", "Scan"),
        ("2", "show_tab('watch')", "Watch"),
        ("3", "show_tab('top')", "Top"),
        ("4", "show_tab('history')", "History"),
        ("r", "refresh_current", "Refresh"),
    ]

    def __init__(self, *, watch_interval: float = 2.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.watch_interval = watch_interval
        self._watch_timer = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(initial="scan"):
            with TabPane(t("tui.scan"), id="scan"):
                yield ScanTab()
            with TabPane(t("tui.watch"), id="watch"):
                yield WatchTab()
            with TabPane(t("tui.top"), id="top"):
                yield TopTab()
            with TabPane(t("tui.history"), id="history"):
                yield HistoryTab()
        yield Static(t("tui.status_idle"), id="status")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(ININET_THEME)
        self.theme = "ininet"
        self.title = "ininet-win"
        self.sub_title = f"lang: {current_language()}"
        self._watch_timer = self.set_interval(
            self.watch_interval, self._tick_watch, pause=True
        )
        self._tick_watch()

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        tab_id = event.pane.id if event.pane is not None else ""
        if self._watch_timer is None:
            return
        if tab_id == "watch":
            self._watch_timer.resume()
        else:
            self._watch_timer.pause()

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)

    def _tick_watch(self) -> None:
        from ininet_win.core.monitor import Filter, get_connections, unresolved_count

        watch_tab = self.query_one(WatchTab)
        try:
            text = watch_tab.query_one("#watch-filter", Input).value
        except Exception:
            text = ""
        conns = get_connections(Filter(process=text))
        watch_tab.refresh_rows(conns)
        unresolved = unresolved_count(conns)
        if unresolved:
            self._set_status(t("unresolved.warning", count=unresolved))
        else:
            self._set_status(t("tui.status_watching"))

    def refresh_top(self) -> None:
        from ininet_win.core.monitor import (
            Filter,
            get_connections,
            group_by_process,
        )

        conns = get_connections(Filter())
        self.query_one(TopTab).refresh_rows(group_by_process(conns))

    def refresh_history(self) -> None:
        from ininet_win.storage.db import Database

        database = Database()
        try:
            snapshots = database.list_snapshots(200)
        finally:
            database.close()
        self.query_one(HistoryTab).refresh_rows(snapshots)

    def action_show_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id
        if tab_id == "top":
            self.refresh_top()
        elif tab_id == "history":
            self.refresh_history()

    def action_refresh_current(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "watch":
            self._tick_watch()
        elif active == "top":
            self.refresh_top()
        elif active == "history":
            self.refresh_history()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-run":
            self.run_scan()
        elif event.button.id == "scan-save":
            self.save_scan()
        elif event.button.id == "top-refresh":
            self.refresh_top()
        elif event.button.id == "history-refresh":
            self.refresh_history()

    def run_scan(self) -> None:
        from ininet_win.core.scan import scan_network

        scan_tab = self.query_one(ScanTab)
        network = scan_tab.query_one("#scan-network", Input).value.strip()
        ports = _ports_spec(scan_tab.query_one("#scan-ports", Input).value)
        if not network:
            self._set_status(t("tui.status_no_network"))
            return
        self._set_status(t("tui.status_scanning", network=network))

        def worker() -> None:
            try:
                result = asyncio.run(scan_network(network, ports))
            except Exception as exc:  # noqa: BLE001 - surface any error to the UI
                self.call_from_thread(self._set_status, t("tui.status_error", message=str(exc)))
                return
            self.call_from_thread(self._scan_done, result)

        self.run_worker(worker, thread=True)

    def _scan_done(self, result) -> None:
        self.query_one(ScanTab).set_result(result)
        self._set_status(
            t(
                "tui.status_scanned",
                hosts=result.host_count,
                ports=result.open_port_count,
            )
        )

    def save_scan(self) -> None:
        from ininet_win.storage.db import Database

        result = self.query_one(ScanTab).last_result
        if result is None:
            return
        database = Database()
        try:
            snapshot_id = database.save_scan(result)
        finally:
            database.close()
        self._set_status(t("tui.status_saved", id=snapshot_id))


def run_tui(watch_interval: float = 2.0) -> None:
    """Resolve the language and launch the TUI."""
    lang, _ = resolve_language()
    from ininet_win.i18n import translator

    translator.set_language(lang)
    IninetTuiApp(watch_interval=watch_interval).run()
