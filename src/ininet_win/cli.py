"""Command-line interface for ininet-win."""

from __future__ import annotations

import asyncio

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
    interval: float = typer.Option(1.0, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Watch live network connections. (not implemented yet)"""
    console.print(f"[yellow]watch[/yellow] interval={interval}s — coming in Stage 2")


if __name__ == "__main__":
    app()
