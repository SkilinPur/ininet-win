"""Textual TUI for ininet-win: Scan / Watch / Top / History tabs."""

from __future__ import annotations

import asyncio
import ipaddress

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.theme import Theme
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets.data_table import CellDoesNotExist

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


def _sort_key(value: str):
    """Sort IPs numerically, then numbers, then everything else case-insensitively."""
    text = value.strip()
    host = text.split(":")[0].split("/")[0]
    try:
        return (0, int(ipaddress.ip_address(host)))
    except ValueError:
        pass
    if text.isdigit():
        return (0, int(text))
    try:
        return (0, float(text))
    except ValueError:
        return (1, text.lower())


class TableTab(Vertical):
    """Base tab: a searchable, sortable DataTable.

    Subclasses add columns and supply rows; this class handles filtering
    (substring over the whole row) and sorting (click a column header).
    """

    table_id: str = "table"

    def compose_search(self) -> ComposeResult:
        yield Input(placeholder=t("tui.search"), id=f"{self.table_id}-search")

    def compose_data(self) -> ComposeResult:
        yield DataTable(id=self.table_id, zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        self._rows: list[tuple[str, ...]] = []
        self._search = ""
        self._sort_col: int | None = None
        self._sort_desc = False
        table = self.query_one(f"#{self.table_id}", DataTable)
        table.add_columns(*self.column_labels())

    def column_labels(self) -> tuple[str, ...]:
        raise NotImplementedError

    def set_rows(self, rows: list[tuple[str, ...]]) -> None:
        self._rows = rows
        self._redraw()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == f"{self.table_id}-search":
            self._search = event.value.strip().lower()
            self._redraw()

    def on_data_table_header_selected(
        self, event: DataTable.HeaderSelected
    ) -> None:
        col = event.column_index
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        self._redraw()

    def _view_rows(self) -> list[tuple[str, ...]]:
        rows = self._rows
        if self._search:
            rows = [
                row
                for row in rows
                if any(self._search in cell.lower() for cell in row)
            ]
        if self._sort_col is not None and 0 <= self._sort_col < len(
            self.column_labels()
        ):
            rows = sorted(
                rows,
                key=lambda r: _sort_key(r[self._sort_col]),
                reverse=self._sort_desc,
            )
        return rows

    def _redraw(self) -> None:
        table = self.query_one(f"#{self.table_id}", DataTable)
        try:
            table.clear()
        except CellDoesNotExist:  # pragma: no cover - defensive
            pass
        for row in self._view_rows():
            table.add_row(*row)


class ScanTab(TableTab):
    """Scan a network and show live hosts with open ports."""

    table_id = "scan-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.ip"),
            t("table.mac"),
            t("table.ports"),
            t("table.services"),
            t("table.banner"),
        )

    def compose(self) -> ComposeResult:
        with Horizontal(id="scan-controls"):
            yield Label(t("tui.network"), classes="ctl-label")
            yield Input(placeholder="10.0.0.0/24", id="scan-network")
            yield Label(t("tui.ports"), classes="ctl-label")
            yield Input(placeholder="1-1024", id="scan-ports")
            yield Button(t("tui.scan_btn"), id="scan-run", variant="primary")
            yield Checkbox(t("tui.banners"), id="scan-banners")
            yield Button(t("tui.save_btn"), id="scan-save", disabled=True)
        yield from self.compose_search()
        yield from self.compose_data()

    def on_mount(self) -> None:
        super().on_mount()
        self._last_result = None

    def set_result(self, result) -> None:
        self._last_result = result
        rows: list[tuple[str, ...]] = []
        for host in result.hosts:
            ports = ", ".join(str(p.port) for p in host.ports) or "-"
            services = ", ".join(
                f"{p.port}/{p.service}" if p.service else str(p.port)
                for p in host.ports
            ) or "-"
            banner = "; ".join(p.banner for p in host.ports if p.banner) or "-"
            rows.append((host.ip, host.mac or "-", ports, services, banner))
        self.set_rows(rows)
        self.query_one("#scan-save", Button).disabled = not result.hosts

    @property
    def last_result(self):
        return self._last_result


class WatchTab(TableTab):
    """Live connection monitor with an auto-refresh timer."""

    table_id = "watch-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.proto"),
            t("table.local"),
            t("table.remote"),
            t("table.state"),
            t("table.pid"),
            t("table.process"),
        )

    def compose(self) -> ComposeResult:
        yield from self.compose_search()
        yield from self.compose_data()

    def refresh_rows(self, conns) -> None:
        rows = [
            (
                conn.proto,
                conn.local or "-",
                conn.remote or "-",
                conn.status or "-",
                str(conn.pid) if conn.pid is not None else "-",
                conn.process or "-",
            )
            for conn in conns
        ]
        self.set_rows(rows)


class TopTab(TableTab):
    """Top processes by number of connections."""

    table_id = "top-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.count"),
            t("table.pid"),
            t("table.process"),
            t("table.remote_hosts"),
            t("table.remote_ports"),
        )

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-controls"):
            yield Button(t("tui.refresh_btn"), id="top-refresh", variant="primary")
        yield from self.compose_search()
        yield from self.compose_data()

    def refresh_rows(self, groups, limit: int = 50) -> None:
        rows: list[tuple[str, ...]] = []
        for group in groups[:limit]:
            hosts = str(len(group.remote_hosts)) if group.remote_hosts else "0"
            ports = ", ".join(str(p) for p in sorted(group.remote_ports)) or "-"
            rows.append(
                (
                    str(group.count),
                    str(group.pid) if group.pid is not None else "-",
                    group.process or "-",
                    hosts,
                    ports,
                )
            )
        self.set_rows(rows)


class HistoryTab(TableTab):
    """Saved scan snapshots."""

    table_id = "history-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.id"),
            t("table.created"),
            t("table.network"),
            t("table.hosts"),
            t("table.open_ports"),
        )

    def compose(self) -> ComposeResult:
        with Horizontal(id="history-controls"):
            yield Button(t("tui.refresh_btn"), id="history-refresh", variant="primary")
        yield from self.compose_search()
        yield from self.compose_data()

    def refresh_rows(self, snapshots) -> None:
        rows = [
            (
                str(snap.id),
                snap.created_at,
                snap.network,
                str(snap.host_count),
                str(snap.open_port_count),
            )
            for snap in snapshots
        ]
        self.set_rows(rows)


class TrafficTab(TableTab):
    """Per-interface traffic volume and rate."""

    table_id = "traffic-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.interface"),
            t("table.recv"),
            t("table.sent"),
            t("table.recv_rate"),
            t("table.send_rate"),
        )

    def compose(self) -> ComposeResult:
        with Horizontal(id="traffic-controls"):
            yield Button(t("tui.refresh_btn"), id="traffic-refresh", variant="primary")
        yield from self.compose_search()
        yield from self.compose_data()

    def refresh_rows(self, items) -> None:
        from ininet_win.core.traffic import format_bytes, format_rate

        rows = [
            (
                item.name,
                format_bytes(item.bytes_recv),
                format_bytes(item.bytes_sent),
                format_rate(item.recv_bps),
                format_rate(item.send_bps),
            )
            for item in items
        ]
        self.set_rows(rows)


class MapTab(TableTab):
    """Network topology: nodes and their links (scan + live connections)."""
    table_id = "map-table"

    def column_labels(self) -> tuple[str, ...]:
        return (
            t("table.node"),
            t("table.kind"),
            t("table.mac"),
            t("table.ports"),
            t("table.links"),
        )

    def compose(self) -> ComposeResult:
        with Horizontal(id="map-controls"):
            yield Button(t("tui.refresh_btn"), id="map-refresh", variant="primary")
        yield from self.compose_search()
        yield from self.compose_data()

    def refresh_rows(self, topo) -> None:
        rows: list[tuple[str, ...]] = []
        for node in topo.nodes.values():
            neighbors = topo.neighbors(node.id)
            ports = ", ".join(str(p) for p in node.ports) or "-"
            links = ", ".join(
                f"{other} ({edge.kind})" for other, edge in neighbors[:5]
            ) or "-"
            rows.append((node.id, node.kind, node.mac or "-", ports, links))
        self.set_rows(rows)


class IninetTuiApp(App):
    """The ininet-win terminal user interface."""

    CSS = """
    Screen { layout: vertical; }
    #scan-controls, #top-controls, #traffic-controls, #map-controls, #history-controls {
        height: auto; padding: 1 1 0 1;
    }
    .ctl-label { padding: 1 1 0 0; }
    #scan-network { width: 24; }
    #scan-ports { width: 16; }
    #scan-run, #scan-save, #top-refresh, #traffic-refresh, #map-refresh,
    #history-refresh { margin: 0 1; }
    Input { margin: 1 1 0 1; }
    DataTable { height: 1fr; }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "show_tab('scan')", "Scan"),
        ("2", "show_tab('watch')", "Watch"),
        ("3", "show_tab('top')", "Top"),
        ("4", "show_tab('traffic')", "Traffic"),
        ("5", "show_tab('map')", "Map"),
        ("6", "show_tab('history')", "History"),
        ("r", "refresh_current", "Refresh"),
        ("/", "focus_search", "Search"),
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
            with TabPane(t("tui.traffic"), id="traffic"):
                yield TrafficTab()
            with TabPane(t("tui.map"), id="map"):
                yield MapTab()
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

    def _current_tab(self):
        tab_id = self.query_one(TabbedContent).active
        return self.query_one(f"#{tab_id}").query_one(TableTab)

    def action_focus_search(self) -> None:
        tab = self._current_tab()
        tab.query_one(Input).focus()

    def _tick_watch(self) -> None:
        from ininet_win.core.monitor import Filter, get_connections, unresolved_count

        watch_tab = self.query_one(WatchTab)
        conns = get_connections(Filter())
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

    def refresh_map(self) -> None:
        from ininet_win.core.monitor import get_connections
        from ininet_win.core.topology import build_topology

        scan = self.query_one(ScanTab).last_result
        conns = get_connections()
        topo = build_topology(scan, conns)
        self.query_one(MapTab).refresh_rows(topo)

    def refresh_traffic(self) -> None:
        from ininet_win.core.traffic import TrafficSnapshot, is_noise

        previous = getattr(self, "_traffic_snapshot", None)
        snap = TrafficSnapshot.capture()
        items = [
            item
            for name, item in snap.rates(previous).items()
            if not is_noise(name)
        ]
        items.sort(key=lambda i: i.total, reverse=True)
        self._traffic_snapshot = snap
        self.query_one(TrafficTab).refresh_rows(items)

    def action_show_tab(self, tab_id: str) -> None:
        self.query_one(TabbedContent).active = tab_id
        if tab_id == "top":
            self.refresh_top()
        elif tab_id == "traffic":
            self.refresh_traffic()
        elif tab_id == "map":
            self.refresh_map()
        elif tab_id == "history":
            self.refresh_history()

    def action_refresh_current(self) -> None:
        active = self.query_one(TabbedContent).active
        if active == "watch":
            self._tick_watch()
        elif active == "top":
            self.refresh_top()
        elif active == "traffic":
            self.refresh_traffic()
        elif active == "map":
            self.refresh_map()
        elif active == "history":
            self.refresh_history()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-run":
            self.run_scan()
        elif event.button.id == "scan-save":
            self.save_scan()
        elif event.button.id == "top-refresh":
            self.refresh_top()
        elif event.button.id == "traffic-refresh":
            self.refresh_traffic()
        elif event.button.id == "map-refresh":
            self.refresh_map()
        elif event.button.id == "history-refresh":
            self.refresh_history()

    def run_scan(self) -> None:
        from ininet_win.core.scan import scan_network

        scan_tab = self.query_one(ScanTab)
        network = scan_tab.query_one("#scan-network", Input).value.strip()
        ports = _ports_spec(scan_tab.query_one("#scan-ports", Input).value)
        banners = scan_tab.query_one("#scan-banners", Checkbox).value
        if not network:
            self._set_status(t("tui.status_no_network"))
            return
        self._set_status(t("tui.status_scanning", network=network))

        def worker() -> None:
            try:
                result = asyncio.run(
                    scan_network(network, ports, grab_banners=banners)
                )
            except Exception as exc:  # noqa: BLE001 - surface any error to the UI
                self.call_from_thread(
                    self._set_status, t("tui.status_error", message=str(exc))
                )
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
