"""Command-line interface for ininet-win."""

from __future__ import annotations

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
def scan(
    network: str = typer.Argument(..., help="Target network in CIDR, e.g. 192.168.0.0/24"),
    ports: str = typer.Option("1-1024", "--ports", "-p", help="Port range, e.g. 1-1024"),
) -> None:
    """Scan a network for live hosts and open ports. (not implemented yet)"""
    console.print(f"[yellow]scan[/yellow] {network} ports={ports} — coming in Stage 1")


@app.command()
def watch(
    interval: float = typer.Option(1.0, "--interval", "-i", help="Refresh interval in seconds"),
) -> None:
    """Watch live network connections. (not implemented yet)"""
    console.print(f"[yellow]watch[/yellow] interval={interval}s — coming in Stage 2")


if __name__ == "__main__":
    app()
