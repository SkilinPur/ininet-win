"""Command-line interface for ininet-win."""

from __future__ import annotations

import asyncio
import json
import time

import typer
from rich.console import Console

from ininet_win import __version__
from ininet_win.console import enable_utf8
from ininet_win.i18n import translator
from ininet_win.i18n.translator import t
from ininet_win.language import resolve_language

enable_utf8()

console = Console()


def _help(key: str) -> str:
    """Return a translated help string."""
    return t(key)


def _default_network() -> str:
    """Best-effort default target network (first local subnet)."""
    try:
        from ininet_win.platform.ifaces import get_interfaces
    except ImportError:  # pragma: no cover - platform layer always present
        return ""
    interfaces = get_interfaces()
    return interfaces[0].network if interfaces else ""


def _build_app() -> typer.Typer:
    app = typer.Typer(
        name="ininet-win",
        help=_help("app.help"),
        no_args_is_help=True,
        add_completion=False,
    )

    @app.callback(invoke_without_command=True)
    def _main(
        ctx: typer.Context,
        lang: str = typer.Option(
            None, "--lang", "-L", help=_help("opt.lang.help"), is_eager=True
        ),
    ) -> None:
        """Resolve language before running any subcommand."""
        resolved, _ = resolve_language(lang)
        translator.set_language(resolved)

    _register_commands(app)
    return app


def _register_commands(app: typer.Typer) -> None:
    @app.command()
    def version() -> None:
        """Show the ininet-win version."""
        console.print(f"ininet-win [bold cyan]{__version__}[/bold cyan]")

    @app.command()
    def lang(
        set_to: str = typer.Argument(None, help=_help("opt.lang.help")),
    ) -> None:
        """Show or change the interface language."""
        from ininet_win import config as cfg
        from ininet_win.i18n import available_langs

        if set_to:
            from ininet_win.i18n import normalize_lang

            normalized = normalize_lang(set_to)
            if not normalized:
                console.print(f"[red]{t('lang.invalid', lang=set_to)}[/red]")
                raise typer.Exit(code=2)
            cfg.set_language(normalized)
            translator.set_language(normalized)
            console.print(t("lang.changed", lang=normalized))
            return
        console.print(t("lang.set", lang=translator.current_language()))
        console.print(t("lang.available", langs=", ".join(available_langs())))

    @app.command()
    def admin(
        elevate: bool = typer.Option(False, "--elevate", help=_help("opt.elevate.help")),
    ) -> None:
        """Show privilege status (administrator or not)."""
        from ininet_win.platform.elevate import is_admin, relaunch_as_admin

        if is_admin():
            console.print(f"[green]{t('admin.yes')}[/green]")
            return

        console.print(f"[yellow]{t('admin.no')}[/yellow]")
        console.print(f"[dim]{t('admin.hint')}[/dim]")
        if elevate:
            if relaunch_as_admin(["admin"]):
                console.print(f"[green]{t('admin.relaunching')}[/green]")
                raise typer.Exit(code=0)
            console.print(f"[red]{t('admin.refused')}[/red]")

    @app.command()
    def interfaces() -> None:
        """List local network interfaces and their networks."""
        from rich.table import Table

        from ininet_win.platform.ifaces import get_interfaces

        ifaces = get_interfaces()
        if not ifaces:
            console.print(f"[yellow]{t('common.no_live_hosts')}[/yellow]")
            return
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(t("table.interface"), style="green")
        table.add_column(t("table.address"), style="cyan")
        table.add_column(t("table.netmask"), style="dim")
        table.add_column(t("table.network"), style="white")
        for iface in ifaces:
            table.add_row(*iface.as_row())
        console.print(table)

    @app.command()
    def scan(
        network: str = typer.Argument(..., help=_help("opt.network.help")),
        ports: str = typer.Option("1-1024", "--ports", "-p", help=_help("opt.ports.help")),
        timeout: float = typer.Option(1.0, "--timeout", "-t", help=_help("opt.timeout.help")),
        port_timeout: float = typer.Option(
            0.5, "--port-timeout", help=_help("opt.port_timeout.help")
        ),
        concurrency: int = typer.Option(128, "--jobs", "-j", help=_help("opt.jobs.help")),
        no_ports: bool = typer.Option(False, "--no-ports", help=_help("opt.no_ports.help")),
        banners: bool = typer.Option(
            False, "--banners", help=_help("opt.banners.help")
        ),
        banner_timeout: float = typer.Option(
            1.0, "--banner-timeout", help=_help("opt.banner_timeout.help")
        ),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json.help")),
        save: bool = typer.Option(False, "--save", help=_help("opt.save.help")),
        db: str = typer.Option("", "--db", help=_help("opt.db.help")),
    ) -> None:
        """Scan a network for live hosts and open ports."""
        from ininet_win.core.scan import scan_network
        from ininet_win.render import render_table, to_json

        async def _run():
            return await scan_network(
                network,
                ports,
                ping_timeout=timeout,
                port_timeout=port_timeout,
                concurrency=concurrency,
                scan_ports=not no_ports,
                grab_banners=banners,
                banner_timeout=banner_timeout,
            )

        try:
            result = asyncio.run(_run())
        except ValueError as exc:
            console.print(f"[red]{t('common.error')}:[/red] {exc}")
            raise typer.Exit(code=2) from exc

        if json_out:
            console.print_json(to_json(result))
        else:
            render_table(result, console)

        if save:
            from ininet_win.storage.db import Database

            database = Database(db or None)
            try:
                snapshot_id = database.save_scan(result)
            finally:
                database.close()
            console.print(f"[dim]{t('common.saved_as', id=snapshot_id)}[/dim]")

    @app.command()
    def history(
        limit: int = typer.Option(50, "--limit", "-l", help=_help("opt.limit.help")),
        prune: int = typer.Option(0, "--prune", help=_help("opt.prune.help")),
        db: str = typer.Option("", "--db", help=_help("opt.db.help")),
    ) -> None:
        """List saved scan snapshots."""
        from ininet_win.render import render_history
        from ininet_win.storage.db import Database

        database = Database(db or None)
        try:
            if prune > 0:
                removed = database.prune(keep=prune)
                console.print(f"[dim]{t('common.pruned', count=removed)}[/dim]")
            render_history(database.list_snapshots(limit), console)
        finally:
            database.close()

    @app.command()
    def diff(
        old_id: int = typer.Argument(..., help=_help("opt.old_id.help")),
        new_id: int = typer.Argument(..., help=_help("opt.new_id.help")),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json.help")),
        db: str = typer.Option("", "--db", help=_help("opt.db.help")),
    ) -> None:
        """Compare two saved scans: what changed between them."""
        from ininet_win.core.diff import diff_scans
        from ininet_win.render import render_diff
        from ininet_win.storage.db import Database

        database = Database(db or None)
        try:
            old = database.get_snapshot(old_id)
            new = database.get_snapshot(new_id)
        finally:
            database.close()

        if old is None:
            console.print(
                f"[red]{t('common.error')}:[/red] {t('error.snapshot_not_found', id=old_id)}"
            )
            raise typer.Exit(code=2)
        if new is None:
            console.print(
                f"[red]{t('common.error')}:[/red] {t('error.snapshot_not_found', id=new_id)}"
            )
            raise typer.Exit(code=2)

        result = diff_scans(old, new)
        if json_out:
            console.print_json(json.dumps(_diff_payload(result), ensure_ascii=False))
        else:
            render_diff(result, console)

    @app.command()
    def watch(
        interval: float = typer.Option(1.0, "--interval", "-i", help=_help("opt.interval.help")),
        count: int = typer.Option(0, "--count", "-n", help=_help("opt.count.help")),
        process: str = typer.Option("", "--process", help=_help("opt.process.help")),
        port: int = typer.Option(None, "--port", help=_help("opt.port.help")),
        host: str = typer.Option("", "--host", help=_help("opt.host.help")),
        status: str = typer.Option("", "--status", help=_help("opt.status.help")),
        connected: bool = typer.Option(False, "--connected", help=_help("opt.connected.help")),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json_snapshot.help")),
        elevate: bool = typer.Option(False, "--elevate", help=_help("opt.elevate.help")),
    ) -> None:
        """Watch live network connections (read-only)."""
        from rich.live import Live

        from ininet_win.core.monitor import Filter, get_connections, unresolved_count
        from ininet_win.platform.elevate import is_admin, relaunch_as_admin
        from ininet_win.render import connections_to_json, render_connections

        if elevate and not is_admin():
            if relaunch_as_admin(["watch"]):
                console.print(f"[green]{t('admin.relaunching')}[/green]")
                raise typer.Exit(code=0)
            console.print(f"[red]{t('admin.refused')}[/red]")

        filt = Filter(
            process=process,
            port=port,
            host=host,
            status=status,
            connected_only=connected,
        )

        def warn_unresolved(conns) -> None:
            unresolved = unresolved_count(conns)
            if unresolved and not is_admin():
                console.print(
                    f"[dim]{t('unresolved.warning', count=unresolved)}[/dim]"
                )

        if json_out:
            console.print_json(connections_to_json(get_connections(filt)))
            return

        def snapshot() -> None:
            conns = get_connections(filt)
            render_connections(conns, console)
            warn_unresolved(conns)

        if count > 0:
            for _ in range(count):
                console.clear()
                snapshot()
                time.sleep(interval)
            return

        try:
            with Live(console=console, refresh_per_second=max(1, int(1 / interval))) as live:
                while True:
                    conns = get_connections(filt)
                    with console.capture() as capture:
                        render_connections(conns, console)
                        warn_unresolved(conns)
                    live.update(capture.get())
                    time.sleep(interval)
        except KeyboardInterrupt:
            console.print(f"[dim]{t('common.stopped')}[/dim]")

    @app.command()
    def top(
        limit: int = typer.Option(20, "--limit", "-l", help=_help("opt.top_limit.help")),
        connected: bool = typer.Option(False, "--connected", help=_help("opt.connected.help")),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json.help")),
        elevate: bool = typer.Option(False, "--elevate", help=_help("opt.elevate.help")),
    ) -> None:
        """Show top processes by number of connections."""
        from ininet_win.core.monitor import (
            Filter,
            get_connections,
            group_by_process,
            unresolved_count,
        )
        from ininet_win.platform.elevate import is_admin, relaunch_as_admin
        from ininet_win.render import render_top

        if elevate and not is_admin():
            if relaunch_as_admin(["top", "--limit", str(limit)]):
                console.print(f"[green]{t('admin.relaunching')}[/green]")
                raise typer.Exit(code=0)
            console.print(f"[red]{t('admin.refused')}[/red]")

        filt = Filter(connected_only=connected)
        conns = get_connections(filt)
        groups = group_by_process(conns)
        if json_out:
            payload = [
                {
                    "pid": g.pid,
                    "process": g.process,
                    "count": g.count,
                    "remote_hosts": sorted(g.remote_hosts),
                    "remote_ports": sorted(g.remote_ports),
                }
                for g in groups[:limit]
            ]
            console.print_json(json.dumps(payload, ensure_ascii=False))
        else:
            render_top(groups, console, limit)
            unresolved = unresolved_count(conns)
            if unresolved and not is_admin():
                console.print(
                    f"[dim]{t('unresolved.warning', count=unresolved)}[/dim]"
                )

    @app.command()
    def topology(
        network: str = typer.Option(
            "", "--network", "-n", help=_help("opt.network.help")
        ),
        ports: str = typer.Option("1-1024", "--ports", "-p", help=_help("opt.ports.help")),
        timeout: float = typer.Option(1.0, "--timeout", "-t", help=_help("opt.timeout.help")),
        no_scan: bool = typer.Option(
            False, "--no-scan", help=_help("opt.no_scan.help")
        ),
        no_live: bool = typer.Option(
            False, "--no-live", help=_help("opt.no_live.help")
        ),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json.help")),
    ) -> None:
        """Show the network topology (hosts and their links)."""
        from ininet_win.core.monitor import get_connections
        from ininet_win.core.scan import scan_network
        from ininet_win.core.topology import build_topology
        from ininet_win.render import render_topology, topology_to_json

        scan = None
        if not no_scan:
            target = network or _default_network()
            if not target:
                console.print(f"[red]{t('topo.no_network')}[/red]")
                raise typer.Exit(code=2)
            scan = asyncio.run(scan_network(target, ports, ping_timeout=timeout))

        conns = [] if no_live else get_connections()
        topo = build_topology(scan, conns, include_live=not no_live)

        if json_out:
            console.print_json(topology_to_json(topo))
        else:
            render_topology(topo, console)

    @app.command()
    def traffic(
        interval: float = typer.Option(
            1.0, "--interval", "-i", help=_help("opt.interval.help")
        ),
        count: int = typer.Option(
            0, "--count", "-n", help=_help("opt.count.help")
        ),
        all_ifaces: bool = typer.Option(
            False, "--all", help=_help("opt.all_ifaces.help")
        ),
        json_out: bool = typer.Option(False, "--json", help=_help("opt.json.help")),
    ) -> None:
        """Show per-interface traffic volume and rate (light mode)."""
        from ininet_win.core.traffic import TrafficSnapshot, is_noise
        from ininet_win.render import render_traffic

        def collect(previous):
            snap = TrafficSnapshot.capture()
            items = list(snap.rates(previous).values())
            if not all_ifaces:
                items = [i for i in items if not is_noise(i.name)]
            items.sort(key=lambda i: i.total, reverse=True)
            return snap, items

        def emit(items) -> None:
            if json_out:
                payload = [
                    {
                        "interface": i.name,
                        "bytes_recv": i.bytes_recv,
                        "bytes_sent": i.bytes_sent,
                        "recv_bps": i.recv_bps,
                        "send_bps": i.send_bps,
                    }
                    for i in items
                ]
                console.print_json(json.dumps(payload, ensure_ascii=False))
            else:
                render_traffic(items, console)

        prev, items = collect(None)
        time.sleep(interval)
        prev, items = collect(prev)
        emit(items)

        if count == 1:
            return
        remaining = count - 1 if count > 0 else 0
        try:
            while remaining != 0:
                time.sleep(interval)
                prev, items = collect(prev)
                console.clear()
                emit(items)
                if remaining > 0:
                    remaining -= 1
        except KeyboardInterrupt:
            console.print(f"[dim]{t('common.stopped')}[/dim]")

    @app.command()
    def tui(
        interval: float = typer.Option(
            2.0, "--interval", "-i", help=_help("opt.interval.help")
        ),
    ) -> None:
        """Launch the interactive terminal UI (Scan / Watch / Top / History)."""
        try:
            from ininet_win.tui.app import run_tui
        except ImportError:
            console.print(f"[red]{t('tui.no_textual')}[/red]")
            raise typer.Exit(code=2) from None
        run_tui(watch_interval=interval)


def _diff_payload(result) -> dict:
    return {
        "old_network": result.old_network,
        "new_network": result.new_network,
        "added_hosts": result.added_hosts,
        "removed_hosts": result.removed_hosts,
        "changed_hosts": [
            {
                "ip": c.ip,
                "added_ports": c.added_ports,
                "removed_ports": c.removed_ports,
            }
            for c in result.changed_hosts
        ],
    }


# Resolve the language once at import time so the initial help text is localized.
# No interactive prompt here (that happens in main() for real first runs).
_initial_lang, _ = resolve_language(prompt=False)
translator.set_language(_initial_lang)

app = _build_app()


def main() -> None:
    """Entry point: launch the TUI by default, or dispatch a subcommand.

    With no arguments (e.g. double-clicking the .exe) the interactive TUI is
    started. On the first interactive run the language is asked once.
    """
    import sys

    argv = sys.argv[1:]
    wants_help = any(a in ("-h", "--help") for a in argv)
    has_lang = any(a == "--lang" or a.startswith("--lang=") for a in argv)

    if not wants_help and not has_lang:
        from ininet_win.language import resolve_language as _resolve

        resolved, prompted = _resolve(prompt=True)
        if prompted:
            translator.set_language(resolved)

    if not argv:
        _run_tui_default()
        return

    app()


def _run_tui_default() -> None:
    """Launch the TUI, falling back to help if textual is unavailable."""
    try:
        from ininet_win.tui.app import run_tui
    except ImportError:
        console.print(t("tui.no_textual"))
        app()
        return
    run_tui()


if __name__ == "__main__":
    main()
