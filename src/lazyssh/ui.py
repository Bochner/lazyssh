"""UI utilities for LazySSH"""

import os

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .models import SSHConnection

console = Console()


def display_banner():
    """Display the LazySSH banner"""
    console.print(
        """
╭───────────────────────────── Welcome to LazySSH ─────────────────────────────╮
│                                                                               │
│     ╦  ┌─┐┌─┐┬ ┬╔═╗╔═╗╦ ╦                                                     │
│     ║  ├─┤┌─┘└┬┘╚═╗╚═╗╠═╣                                                     │
│     ╩═╝┴ ┴└─┘ ┴ ╚═╝╚═╝╩ ╩                                                     │
│                                                                               │
╰───────────────────────────────────────────────────────────────────────────────╯
""",
        style="bold blue",
    )


def display_menu(options):
    table = Table(show_header=False, border_style="blue")
    for key, value in options.items():
        table.add_row(f"[cyan]{key}[/cyan]", f"[white]{value}[/white]")
    console.print(table)


def get_user_input(prompt_text):
    return Prompt.ask(f"[cyan]{prompt_text}[/cyan]")


def display_error(message):
    console.print(f"[red]Error:[/red] {message}")


def display_success(message):
    console.print(f"[green]Success:[/green] {message}")


def display_info(message):
    console.print(f"[blue]Info:[/blue] {message}")


def display_warning(message):
    console.print(f"[yellow]Warning:[/yellow] {message}")


def display_ssh_status(connections):
    table = Table(title="Active SSH Connections", border_style="blue")
    table.add_column("Name", style="cyan")
    table.add_column("Host", style="magenta")
    table.add_column("Username", style="green")
    table.add_column("Port", style="yellow")
    table.add_column("Dynamic Port", style="blue")
    table.add_column("Active Tunnels", style="red")

    for socket_path, conn in connections.items():
        if isinstance(conn, SSHConnection):
            name = os.path.basename(socket_path)
            table.add_row(
                name,
                conn.host,
                conn.username,
                str(conn.port),
                str(conn.dynamic_port or "N/A"),
                str(len(conn.tunnels)),
            )

    console.print(table)


def display_tunnels(socket_path: str, conn: SSHConnection):
    if not conn.tunnels:
        display_info("No tunnels for this connection")
        return

    table = Table(title=f"Tunnels for {conn.host}", border_style="blue")
    table.add_column("ID", style="cyan")
    table.add_column("Connection", style="blue")
    table.add_column("Type", style="magenta")
    table.add_column("Local Port", style="green")
    table.add_column("Remote", style="yellow")

    for tunnel in conn.tunnels:
        table.add_row(
            tunnel.id,
            tunnel.connection_name,
            tunnel.type,
            str(tunnel.local_port),
            f"{tunnel.remote_host}:{tunnel.remote_port}",
        )

    console.print(table)
