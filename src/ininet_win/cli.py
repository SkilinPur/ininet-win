"""Command-line interface for ininet-win."""

from __future__ import annotations

import asyncio
import json
import time

import typer
from rich.console import Console

from ininet_win import __version__
from ininet_win.console import enable_utf8

enable_utf8()

app = typer.Typer(
    name="ininet-win",
    help="Network scanner & live connection monitor (Windows).",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Show the ininet-win version."""
    console.print(f"ininet-win [bold cyan]{__version__}[/bold cyan]")


@app.command()
def admin(
    elevate: bool = typer.Option(
        False, "--elevate", help="Relaunch this command with UAC elevation"
    ),
) -> None:
    """Show privilege status (administrator or not)."""
    from ininet_win.platform.elevate import is_admin, relaunch_as_admin

    if is_admin():
        console.print("[green]Administrator:[/green] yes")
        return

    console.print("[yellow]Administrator:[/yellow] no")
    console.print(
        "[dim]Without admin rights, the owning process of connections that belong\n"
        "to other users cannot be resolved (shown as PID 0 / empty process).[/dim]"
    )
    if elevate:
        if relaunch_as_admin(["admin"]):
            console.print("[green]Relaunching with elevation...[/green]")
            raise typer.Exit(code=0)
        console.print("[red]Elevation was refused or unavailable.[/red]")


@app.command()
def interfaces() -> None:
    """List local network interfaces and their networks."""
    from rich.table import Table

    from ininet_win.platform.ifaces import get_interfaces

    ifaces = get_interfaces()
    if not ifaces:
        console.print("[yellow]No usable IPv4 interfaces found.[/yellow]")
        return
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Interface", style="green")
    table.add_column("Address", style="cyan")
    table.add_column("Netmask", style="dim")
    table.add_column("Network", style="white")
    for iface in ifaces:
        table.add_row(*iface.as_row())
    console.print(table)


@app.command()
def scan(
    network: str = typer.Argument(..., help="Target network in CIDR, e.g. 192.168.0.0/24"),
    ports: str = typer.Option("1-1024", "--ports", "-p", help="Port range, e.g. 1-1024"),
    timeout: float = typer.Option(1.0, "--timeout", "-t", help="Ping timeout (seconds)"),
    port_timeout: float = typer.Option(0.5, "--port-timeout", help="Port timeout (seconds)"),
    concurrency: int = typer.Option(128, "--jobs", "-j", help="Ping concurrency"),
    no_ports: bool = typer.Option(False, "--no-ports", help="Discover hosts only"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
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
        )

    try:
        result = asyncio.run(_run())
    except ValueError as exc:
        console.print(f"[red]error:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    if json_out:
        console.print_json(to_json(result))
    else:
        render_table(result, console)


@app.command()
def watch(
    interval: float = typer.Option(1.0, "--interval", "-i", help="Refresh interval (seconds)"),
    count: int = typer.Option(0, "--count", "-n", help="Stop after N refreshes (0 = forever)"),
    process: str = typer.Option("", "--process", help="Filter by process name (substring)"),
    port: int = typer.Option(None, "--port", help="Filter by local/remote port"),
    host: str = typer.Option("", "--host", help="Filter by remote/local address"),
    status: str = typer.Option("", "--status", help="Filter by connection state"),
    connected: bool = typer.Option(False, "--connected", help="Only established connections"),
    json_out: bool = typer.Option(False, "--json", help="Print a one-shot JSON snapshot and exit"),
    elevate: bool = typer.Option(
        False, "--elevate", help="Relaunch with UAC elevation to resolve all processes"
    ),
) -> None:
    """Watch live network connections (read-only)."""
    from rich.live import Live

    from ininet_win.core.monitor import Filter, get_connections, unresolved_count
    from ininet_win.platform.elevate import is_admin, relaunch_as_admin
    from ininet_win.render import connections_to_json, render_connections

    if elevate and not is_admin():
        if relaunch_as_admin(["watch"]):
            console.print("[green]Relaunching with elevation...[/green]")
            raise typer.Exit(code=0)
        console.print("[red]Elevation was refused or unavailable.[/red]")

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
                f"[dim]{unresolved} connection(s) without a process — "
                "run with --elevate to resolve[/dim]"
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
        console.print("[dim]stopped[/dim]")


@app.command()
def top(
    limit: int = typer.Option(20, "--limit", "-l", help="Show top N processes"),
    connected: bool = typer.Option(False, "--connected", help="Only established connections"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
    elevate: bool = typer.Option(
        False, "--elevate", help="Relaunch with UAC elevation to resolve all processes"
    ),
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
            console.print("[green]Relaunching with elevation...[/green]")
            raise typer.Exit(code=0)
        console.print("[red]Elevation was refused or unavailable.[/red]")

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
                f"[dim]{unresolved} connection(s) without a process — "
                "run with --elevate to resolve[/dim]"
            )


if __name__ == "__main__":
    app()
