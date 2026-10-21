"""Rendering scan results: rich tables and JSON."""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from ininet_win.core.monitor import Connection, ProcessGroup
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


def render_connections(conns: list[Connection], console: Console | None = None) -> None:
    """Print a live connection table."""
    console = console or Console()
    if not conns:
        console.print("[yellow]No connections.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Proto", style="dim", no_wrap=True)
    table.add_column("Local", style="cyan", no_wrap=True)
    table.add_column("Remote", style="green", no_wrap=True)
    table.add_column("State", style="yellow", no_wrap=True)
    table.add_column("PID", justify="right", style="dim", no_wrap=True)
    table.add_column("Process", style="white")

    for conn in conns:
        table.add_row(
            conn.proto,
            conn.local or "-",
            conn.remote or "-",
            conn.status or "-",
            str(conn.pid) if conn.pid is not None else "-",
            conn.process or "-",
        )
    console.print(table)


def render_top(groups: list[ProcessGroup], console: Console | None = None, limit: int = 20) -> None:
    """Print top processes by connection count."""
    console = console or Console()
    if not groups:
        console.print("[yellow]No connections.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Count", justify="right", style="cyan", no_wrap=True)
    table.add_column("PID", justify="right", style="dim", no_wrap=True)
    table.add_column("Process", style="white")
    table.add_column("Remote hosts", style="green", justify="right")
    table.add_column("Remote ports", style="yellow")

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
    console.print(table)


def connections_to_json(conns: list[Connection]) -> str:
    """Serialize connections to JSON."""
    payload = [
        {
            "proto": c.proto,
            "local": c.local,
            "remote": c.remote,
            "status": c.status,
            "pid": c.pid,
            "process": c.process,
        }
        for c in conns
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)
