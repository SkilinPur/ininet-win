"""Rendering scan results: rich tables and JSON."""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from ininet_win.core.monitor import Connection, ProcessGroup
from ininet_win.core.scan import ScanResult
from ininet_win.i18n.translator import t


def render_table(result: ScanResult, console: Console | None = None) -> None:
    """Print scan results as a rich table."""
    console = console or Console()

    console.print(
        f"[bold]{t('common.network')}[/bold] {result.network}  "
        f"[green]{result.host_count}[/green] {t('common.host_s')}, "
        f"[cyan]{result.open_port_count}[/cyan] {t('common.open_port_s')}"
    )

    if not result.hosts:
        console.print(f"[yellow]{t('common.no_live_hosts')}[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(t("table.ip"), style="green", no_wrap=True)
    table.add_column(t("table.mac"), style="dim")
    table.add_column(t("table.ports"), style="cyan")
    table.add_column(t("table.services"), style="white")

    for host in result.hosts:
        ports = ", ".join(str(p.port) for p in host.ports) or "-"
        services = ", ".join(
            f"{p.port}/{p.service}" if p.service else str(p.port) for p in host.ports
        ) or "-"
        banners = ", ".join(
            f"{p.port}: {p.banner}" for p in host.ports if p.banner
        )
        if banners:
            services = f"{services}\n{banners}"
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
                    {"port": p.port, "service": p.service, "banner": p.banner}
                    for p in h.ports
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
        console.print(f"[yellow]{t('common.no_connections')}[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(t("table.proto"), style="dim", no_wrap=True)
    table.add_column(t("table.local"), style="cyan", no_wrap=True)
    table.add_column(t("table.remote"), style="green", no_wrap=True)
    table.add_column(t("table.state"), style="yellow", no_wrap=True)
    table.add_column(t("table.pid"), justify="right", style="dim", no_wrap=True)
    table.add_column(t("table.process"), style="white")

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
        console.print(f"[yellow]{t('common.no_connections')}[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(t("table.count"), justify="right", style="cyan", no_wrap=True)
    table.add_column(t("table.pid"), justify="right", style="dim", no_wrap=True)
    table.add_column(t("table.process"), style="white")
    table.add_column(t("table.remote_hosts"), style="green", justify="right")
    table.add_column(t("table.remote_ports"), style="yellow")

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


def render_history(snapshots, console: Console | None = None) -> None:
    """Print a table of saved scan snapshots."""
    console = console or Console()
    if not snapshots:
        console.print(f"[yellow]{t('common.no_saved_scans')}[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(t("table.id"), justify="right", style="cyan", no_wrap=True)
    table.add_column(t("table.created"), style="dim", no_wrap=True)
    table.add_column(t("table.network"), style="green", no_wrap=True)
    table.add_column(t("table.hosts"), justify="right", style="white")
    table.add_column(t("table.open_ports"), justify="right", style="yellow")

    for snap in snapshots:
        table.add_row(
            str(snap.id),
            snap.created_at,
            snap.network,
            str(snap.host_count),
            str(snap.open_port_count),
        )
    console.print(table)


def render_diff(diff, console: Console | None = None) -> None:
    """Print a scan-to-scan diff."""
    console = console or Console()
    console.print(f"[bold]Diff[/bold] {diff.old_network} -> {diff.new_network}")
    if not diff.has_changes:
        console.print(f"[green]{t('diff.no_changes')}[/green]")
        return

    if diff.added_hosts:
        console.print(f"[green]{t('diff.added_hosts')}[/green] {', '.join(diff.added_hosts)}")
    if diff.removed_hosts:
        console.print(f"[red]{t('diff.removed_hosts')}[/red] {', '.join(diff.removed_hosts)}")
    for change in diff.changed_hosts:
        parts = []
        if change.added_ports:
            parts.append(f"[green]+{','.join(map(str, change.added_ports))}[/green]")
        if change.removed_ports:
            parts.append(f"[red]-{','.join(map(str, change.removed_ports))}[/red]")
        console.print(f"  {change.ip}: {' '.join(parts)}")


def render_topology(topo, console: Console | None = None) -> None:
    """Print a network topology as an ASCII tree from its root nodes."""
    console = console or Console()
    console.print(
        f"[bold]{t('topo.title')}[/bold]  "
        f"[green]{topo.node_count}[/green] {t('common.host_s')}, "
        f"[cyan]{topo.edge_count}[/cyan] {t('topo.links')}"
    )

    if not topo.nodes:
        console.print(f"[yellow]{t('topo.empty')}[/yellow]")
        return

    roots = topo.roots()
    if not roots:
        roots = list(topo.nodes)

    seen: set[str] = set()
    for index, root in enumerate(roots):
        if root in seen:
            continue
        _print_branch(topo, root, "", index == len(roots) - 1, seen, console)


def _print_branch(
    topo, node_id: str, prefix: str, last: bool, seen: set[str], console
) -> None:
    node = topo.nodes[node_id]
    connector = "└─" if last else "├─"
    color = "green" if node.kind == "host" else "magenta"
    detail = f"  [dim]{node.mac}[/dim]" if node.mac else ""
    console.print(f"{prefix}{connector} [{color}]{node.label}[/{color}]{detail}")
    seen.add(node_id)

    children = [
        (other, edge) for other, edge in topo.neighbors(node_id) if other not in seen
    ]
    child_prefix = prefix + ("   " if last else "│  ")
    for index, (other, edge) in enumerate(children):
        _print_edge(topo, other, edge, child_prefix, index == len(children) - 1, seen, console)


def _print_edge(
    topo, node_id: str, edge, prefix: str, last: bool, seen: set[str], console
) -> None:
    node = topo.nodes[node_id]
    connector = "└─" if last else "├─"
    color = "green" if node.kind == "host" else "magenta"
    ports = f" [cyan]:{','.join(map(str, edge.ports))}[/cyan]" if edge.ports else ""
    count = f" [dim]x{edge.count}[/dim]" if edge.count > 1 else ""
    kind = f"[dim]{edge.kind}[/dim]"
    detail = f"  [dim]{node.mac}[/dim]" if node.mac else ""
    console.print(
        f"{prefix}{connector} [{color}]{node.label}[/{color}]{detail} "
        f"{kind}{ports}{count}"
    )
    seen.add(node_id)

    children = [
        (other, e) for other, e in topo.neighbors(node_id) if other not in seen
    ]
    child_prefix = prefix + ("   " if last else "│  ")
    for index, (other, sub_edge) in enumerate(children):
        _print_edge(
            topo, other, sub_edge, child_prefix, index == len(children) - 1, seen, console
        )


def topology_to_json(topo) -> str:
    """Serialize a topology graph to JSON."""
    payload = {
        "nodes": [
            {"id": n.id, "kind": n.kind, "mac": n.mac, "ports": n.ports}
            for n in topo.nodes.values()
        ],
        "edges": [
            {
                "src": e.src,
                "dst": e.dst,
                "kind": e.kind,
                "count": e.count,
                "ports": e.ports,
            }
            for e in topo.edges
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_traffic(traffic, console: Console | None = None) -> None:
    """Print per-interface traffic volume and rates as a rich table."""
    from ininet_win.core.traffic import format_bytes, format_rate

    console = console or Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column(t("table.interface"), style="green", no_wrap=True)
    table.add_column(t("table.recv"), justify="right")
    table.add_column(t("table.sent"), justify="right")
    table.add_column(t("table.recv_rate"), justify="right")
    table.add_column(t("table.send_rate"), justify="right")

    for item in traffic:
        table.add_row(
            item.name,
            format_bytes(item.bytes_recv),
            format_bytes(item.bytes_sent),
            format_rate(item.recv_bps),
            format_rate(item.send_bps),
        )
    console.print(table)
