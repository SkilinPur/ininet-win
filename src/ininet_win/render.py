"""Rendering scan results: rich tables and JSON."""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from ininet_win.core.scan import ScanResult


def render_table(result: ScanResult, console: Console | None = None) -> None:
    """Print scan results as a rich table."""
    console = console or Console()

    console.print(
        f"[bold]Network[/bold] {result.network}  "
        f"[green]{result.host_count}[/green] host(s), "
        f"[cyan]{result.open_port_count}[/cyan] open port(s)"
    )

    if not result.hosts:
        console.print("[yellow]No live hosts found.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("IP", style="green", no_wrap=True)
    table.add_column("MAC", style="dim")
    table.add_column("Ports", style="cyan")
    table.add_column("Services", style="white")

    for host in result.hosts:
        ports = ", ".join(str(p.port) for p in host.ports) or "-"
        services = ", ".join(
            f"{p.port}/{p.service}" if p.service else str(p.port) for p in host.ports
        ) or "-"
        table.add_row(host.ip, host.mac or "-", ports, services)

    console.print(table)


def to_json(result: ScanResult) -> str:
    """Serialize scan results to a JSON string."""
    payload = {
        "network": result.network,
        "hosts": [
            {
                "ip": h.ip,
                "mac": h.mac,
                "ports": [
                    {"port": p.port, "service": p.service} for p in h.ports
                ],
            }
            for h in result.hosts
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
