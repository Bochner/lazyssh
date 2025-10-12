"""UI utilities for LazySSH"""

import os
from pathlib import Path
from typing import Any

from rich.align import Align
from rich.box import ROUNDED
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from . import __version__
from .models import SSHConnection

# Centralized Dracula theme definition
LAZYSSH_THEME = Theme(
    {
        # Core Dracula colors
        "info": "#8be9fd",  # Cyan - for info messages and function names
        "warning": "#f1fa8c",  # Yellow - for warnings and variables
        "error": "#ff5555",  # Red - for errors and danger messages
        "success": "#50fa7b",  # Green - for success messages and strings
        "header": "#bd93f9",  # Purple - for headers and operators
        "accent": "#8be9fd",  # Cyan - for accents and highlights
        "dim": "#6272a4",  # Comment - for muted text and secondary info
        "highlight": "#ff79c6",  # Pink - for keywords and special commands
        "border": "#6272a4",  # Comment - for borders
        "table.header": "#bd93f9",  # Purple - for table headers
        "table.row": "#f8f8f2",  # Foreground - for table rows
        "panel.title": "#bd93f9",  # Purple - for panel titles
        "panel.subtitle": "#6272a4",  # Comment - for panel subtitles
        # Additional Dracula colors for specific use cases
        "keyword": "#ff79c6",  # Pink - for keywords like if, for, return
        "operator": "#bd93f9",  # Purple - for operators and special symbols
        "string": "#50fa7b",  # Green - for strings
        "variable": "#f8f8f2",  # Foreground - for variables
        "number": "#ffb86c",  # Orange - for numbers and constants
        "comment": "#6272a4",  # Comment - for comments and muted text
        "foreground": "#f8f8f2",  # Foreground - for default text
        "background": "#282a36",  # Background - for main background
        # Progress bar specific colors
        "progress.description": "#8be9fd",  # Cyan - for progress descriptions
        "progress.percentage": "#f8f8f2",  # Foreground - for percentage text
        "progress.bar": "#6272a4",  # Comment - for progress bar background
        "progress.bar.complete": "#50fa7b",  # Green - for completed portion
    }
)


# Environment variable parsing functions
def parse_boolean_env_var(var_name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    value = os.getenv(var_name)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def parse_integer_env_var(var_name: str, default: int, min_val: int = 1, max_val: int = 10) -> int:
    """Parse an integer environment variable with bounds checking."""
    value = os.getenv(var_name, "")
    try:
        int_value = int(value)
        return max(min_val, min(max_val, int_value))
    except (ValueError, TypeError):
        return default


def get_ui_config() -> dict[str, Any]:
    """Get UI configuration from environment variables."""
    return {
        "high_contrast": parse_boolean_env_var("LAZYSSH_HIGH_CONTRAST", False),
        "no_rich": parse_boolean_env_var("LAZYSSH_NO_RICH", False),
        "refresh_rate": parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10),
        "no_animations": parse_boolean_env_var("LAZYSSH_NO_ANIMATIONS", False),
        "colorblind_mode": parse_boolean_env_var("LAZYSSH_COLORBLIND_MODE", False),
        "plain_text": parse_boolean_env_var("LAZYSSH_PLAIN_TEXT", False),
    }


def get_theme_for_config(config: dict[str, Any]) -> Theme:
    """Get the appropriate theme based on configuration."""
    if config["plain_text"]:
        # Return a minimal theme for plain text mode
        return Theme(
            {
                "info": "default",
                "warning": "default",
                "error": "default",
                "success": "default",
                "header": "default",
                "accent": "default",
                "dim": "default",
                "highlight": "default",
                "border": "default",
                "table.header": "default",
                "table.row": "default",
                "panel.title": "default",
                "panel.subtitle": "default",
                "keyword": "default",
                "operator": "default",
                "string": "default",
                "variable": "default",
                "number": "default",
                "comment": "default",
                "foreground": "default",
                "background": "default",
                "progress.description": "default",
                "progress.percentage": "default",
                "progress.bar": "default",
                "progress.bar.complete": "default",
            }
        )
    elif config["high_contrast"]:
        return create_high_contrast_theme()
    elif config["colorblind_mode"]:
        return create_colorblind_friendly_theme()
    else:
        return LAZYSSH_THEME


def get_terminal_width() -> int:
    """Get the terminal width with fallbacks."""
    # Try environment variable first
    if "COLUMNS" in os.environ:
        try:
            return int(os.environ["COLUMNS"])
        except ValueError:
            pass

    # Try tput command
    try:
        import shutil

        result = shutil.which("tput")
        if result:
            import subprocess

            cols = subprocess.check_output(["tput", "cols"], text=True).strip()
            return int(cols)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass

    # Fallback to a reasonable default
    return 80


def create_console_with_config(config: dict[str, Any]) -> Console:
    """Create a console instance with configuration applied."""
    theme = get_theme_for_config(config)

    return Console(
        theme=theme,
        force_terminal=not config["no_rich"],
        legacy_windows=False,
        color_system="auto" if not (config["no_rich"] or config["plain_text"]) else None,
        width=get_terminal_width(),
        height=None,  # Auto-detect height
    )


# Initialize UI configuration and console
ui_config = get_ui_config()
console = create_console_with_config(ui_config)


def display_banner() -> None:
    """Display the LazySSH banner with sophisticated styling"""
    # Create ASCII art for the logo
    ascii_art = [
        "██╗      █████╗ ███████╗██╗   ██╗███████╗███████╗██╗  ██╗",
        "██║     ██╔══██╗╚══███╔╝╚██╗ ██╔╝██╔════╝██╔════╝██║  ██║",
        "██║     ███████║  ███╔╝  ╚████╔╝ ███████╗███████╗███████║",
        "██║     ██╔══██║ ███╔╝    ╚██╔╝  ╚════██║╚════██║██╔══██║",
        "███████╗██║  ██║███████╗   ██║   ███████║███████║██║  ██║",
        "╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝",
    ]

    # Build the content using a table for better alignment
    content = Table.grid(padding=0)
    content.add_column(justify="center")

    # Add the ASCII art logo as centered rows
    for line in ascii_art:
        content.add_row(Text(line, style="accent"))

    # Add tagline
    content.add_row("")
    content.add_row(Text("⚡ Modern SSH Connection Manager ⚡", style="highlight"))
    content.add_row("")

    # Add version using the dynamic version from __init__.py
    content.add_row(Text(f"v{__version__}", style="dim"))

    # Create panel
    panel = Panel(
        content,
        title="[panel.title]Welcome to LazySSH[/panel.title]",
        subtitle="[panel.subtitle]SSH Made Easy[/panel.subtitle]",
        border_style="border",
        box=ROUNDED,
        padding=(1, 2),  # Increased padding for better readability
    )

    # Print the panel centered
    console.print(Align.center(panel))


def display_menu(options: dict[str, str]) -> None:
    table = create_standard_table(show_header=False)
    table.add_column("Option", style="info", justify="center")
    table.add_column("Description", style="table.row", justify="center")
    for key, value in options.items():
        table.add_row(f"[info]{key}[/info]", f"[table.row]{value}[/table.row]")
    console.print(table)


def get_user_input(prompt_text: str) -> str:
    result: str = Prompt.ask(f"[info]{prompt_text}[/info]")
    return result


def display_error(message: str) -> None:
    console.print(f"[error]Error:[/error] {message}")


def display_success(message: str) -> None:
    console.print(f"[success]Success:[/success] {message}")


def display_info(message: str) -> None:
    console.print(f"[info]{message}[/info]")


def display_warning(message: str) -> None:
    console.print(f"[warning]Warning:[/warning] {message}")


def display_ssh_status(
    connections: dict[str, SSHConnection], terminal_method: str = "auto"
) -> None:
    table = create_standard_table(title="Active SSH Connections")
    table.add_column("Name", style="table.header", justify="center")
    table.add_column("Host", style="highlight", justify="center")
    table.add_column("Username", style="success", justify="center")
    table.add_column("Port", style="warning", justify="center")
    table.add_column("Dynamic Port", style="info", justify="center")
    table.add_column("Terminal Method", style="accent", justify="center")
    table.add_column("Active Tunnels", style="error", justify="center")
    table.add_column("Socket Path", style="dim", justify="center")

    for socket_path, conn in connections.items():
        if isinstance(conn, SSHConnection):
            name = Path(socket_path).name
            table.add_row(
                name,
                conn.host,
                conn.username,
                str(conn.port),
                str(conn.dynamic_port or "N/A"),
                terminal_method,
                str(len(conn.tunnels)),
                socket_path,
            )

    console.print(table)


def display_tunnels(socket_path: str, conn: SSHConnection) -> None:
    if not conn.tunnels:
        display_info("No tunnels for this connection")
        return

    table = create_standard_table(title=f"Tunnels for {conn.host}")
    table.add_column("ID", style="table.header", justify="center")
    table.add_column("Connection", style="info", justify="center")
    table.add_column("Type", style="highlight", justify="center")
    table.add_column("Local Port", style="success", justify="center")
    table.add_column("Remote", style="warning", justify="center")

    for tunnel in conn.tunnels:
        table.add_row(
            tunnel.id,
            tunnel.connection_name,
            tunnel.type,
            str(tunnel.local_port),
            f"{tunnel.remote_host}:{tunnel.remote_port}",
        )

    console.print(table)


def display_saved_configs(configs: dict[str, dict[str, Any]]) -> None:
    """
    Display saved connection configurations in a formatted table.

    Args:
        configs: Dictionary mapping config names to their parameters
    """
    if not configs:
        display_info("No saved configurations")
        return

    table = create_standard_table(title="Saved Connection Configurations")
    table.add_column("Name", style="table.header", justify="center")
    table.add_column("Host", style="highlight", justify="center")
    table.add_column("Username", style="success", justify="center")
    table.add_column("Port", style="warning", justify="center")
    table.add_column("SSH Key", style="accent", justify="center")
    table.add_column("Shell", style="info", justify="center")
    table.add_column("Proxy", style="info", justify="center")
    table.add_column("No-Term", style="dim", justify="center")

    for name, params in configs.items():
        # Extract parameters with defaults
        host = params.get("host", "N/A")
        username = params.get("username", "N/A")
        port = str(params.get("port", "22"))
        ssh_key = params.get("ssh_key", "N/A")
        shell = params.get("shell", "N/A")
        proxy_port = str(params.get("proxy_port", "N/A"))
        no_term = "Yes" if params.get("no_term", False) else "No"

        # Truncate SSH key path for display if too long
        if ssh_key != "N/A" and len(ssh_key) > 30:
            ssh_key = "..." + ssh_key[-27:]

        table.add_row(name, host, username, port, ssh_key, shell, proxy_port, no_term)

    console.print()  # Add blank line before table
    console.print(table)
    console.print()  # Add blank line after table


# Standardized UI Component Factory Functions


def create_standard_table(title: str = "", show_header: bool = True) -> Table:
    """Create a standardized table with consistent styling."""
    table = Table(
        title=title,
        border_style="border",
        show_header=show_header,
        header_style="table.header",
        box=ROUNDED,
        padding=(0, 2, 0, 2),  # Increased horizontal padding for better readability
    )
    return table


def create_info_panel(content: str, title: str = "Information") -> Panel:
    """Create a standardized information panel."""
    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]",
        border_style="info",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )


def create_success_panel(content: str, title: str = "Success") -> Panel:
    """Create a standardized success panel."""
    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]",
        border_style="success",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )


def create_error_panel(content: str, title: str = "Error") -> Panel:
    """Create a standardized error panel."""
    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]",
        border_style="error",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )


def create_warning_panel(content: str, title: str = "Warning") -> Panel:
    """Create a standardized warning panel."""
    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]",
        border_style="warning",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )


def get_current_ui_config() -> dict[str, Any]:
    """Get the current UI configuration."""
    return ui_config.copy()


def update_console_config() -> None:
    """Update the global console instance with current configuration."""
    global console
    ui_config = get_ui_config()
    console = create_console_with_config(ui_config)


def get_console() -> Console:
    """Get the centralized console instance."""
    return console


def create_spinner(text: str = "Processing...") -> str:
    """Create a standardized spinner text for indeterminate operations."""
    return f"[info]{text}[/info]"


def create_status_indicator(status: str, message: str) -> str:
    """Create a standardized status indicator."""
    status_colors = {
        "success": "success",
        "error": "error",
        "warning": "warning",
        "info": "info",
        "processing": "accent",
    }
    color = status_colors.get(status.lower(), "info")
    return f"[{color}]{status.upper()}:[/{color}] {message}"


# Rich Layout System Functions


def create_main_layout() -> Layout:
    """Create a standardized main layout for complex interfaces."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    return layout


def create_sidebar_layout() -> Layout:
    """Create a layout with sidebar for navigation and main content."""
    layout = Layout()
    layout.split_row(
        Layout(name="sidebar", size=30),
        Layout(name="main"),
    )
    return layout


def create_dashboard_layout() -> Layout:
    """Create a dashboard-style layout with multiple sections."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="stats", size=5),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    # Split main area into columns
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    return layout


def create_progress_layout() -> Layout:
    """Create a layout optimized for progress displays."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="progress", size=5),
        Layout(name="details"),
        Layout(name="footer", size=3),
    )
    return layout


def update_layout_header(layout: Layout, content: str) -> None:
    """Update the header section of a layout."""
    layout["header"].update(
        Panel(
            content,
            title="[panel.title]LazySSH[/panel.title]",
            border_style="border",
            box=ROUNDED,
        )
    )


def update_layout_footer(layout: Layout, content: str) -> None:
    """Update the footer section of a layout."""
    layout["footer"].update(
        Panel(
            content,
            border_style="dim",
            box=ROUNDED,
        )
    )


def render_layout(layout: Layout) -> None:
    """Render a layout to the console."""
    console.print(layout)


# Markdown Rendering Functions


def render_markdown(content: str, title: str = "") -> None:
    """Render markdown content with consistent styling."""
    markdown = Markdown(content)
    if title:
        panel = Panel(
            markdown,
            title=f"[panel.title]{title}[/panel.title]",
            border_style="border",
            box=ROUNDED,
            padding=(1, 3),  # Increased padding for better readability
        )
        console.print(panel)
    else:
        console.print(markdown)


def render_help_markdown(content: str) -> None:
    """Render help content as markdown with help-specific styling."""
    markdown = Markdown(content)
    panel = Panel(
        markdown,
        title="[panel.title]Help[/panel.title]",
        subtitle="[panel.subtitle]LazySSH Documentation[/panel.subtitle]",
        border_style="info",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )
    console.print(panel)


def render_documentation_markdown(content: str, section: str = "") -> None:
    """Render documentation content as markdown."""
    markdown = Markdown(content)
    title = "[panel.title]Documentation[/panel.title]"
    if section:
        title += f" - [panel.subtitle]{section}[/panel.subtitle]"

    panel = Panel(
        markdown,
        title=title,
        border_style="accent",
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )
    console.print(panel)


def create_markdown_panel(content: str, title: str = "", panel_type: str = "info") -> Panel:
    """Create a panel with markdown content."""
    markdown = Markdown(content)
    border_styles = {
        "info": "info",
        "success": "success",
        "error": "error",
        "warning": "warning",
        "accent": "accent",
    }
    border_style = border_styles.get(panel_type, "info")

    return Panel(
        markdown,
        title=f"[panel.title]{title}[/panel.title]" if title else None,
        border_style=border_style,
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
    )


# Live Updating Display Functions


def create_live_progress(task_description: str) -> tuple[Live, Progress]:
    """Create a live progress display for long-running operations."""
    config = get_ui_config()  # Get fresh configuration
    if config["no_animations"]:
        # Create a simple progress without spinner for no-animations mode
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    else:
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    progress.add_task(task_description, total=None)
    refresh_rate = config["refresh_rate"]
    live = Live(progress, console=console, refresh_per_second=refresh_rate)
    return live, progress


def create_live_status_display() -> Live:
    """Create a live status display for real-time updates."""
    layout = create_progress_layout()
    config = get_ui_config()  # Get fresh configuration
    refresh_rate = config["refresh_rate"]
    live = Live(layout, console=console, refresh_per_second=refresh_rate)
    return live


def update_live_status(live: Live, status_text: str, details: str = "") -> None:
    """Update a live status display with new information."""
    if hasattr(live, "renderable") and hasattr(live.renderable, "update"):
        # Update the layout with new status information
        status_panel = create_info_panel(f"{status_text}\n{details}", "Status")
        # Type assertion: we know renderable is a Layout when it has update method
        layout = live.renderable
        if isinstance(layout, Layout):
            layout["main"].update(status_panel)


def create_live_table(table_title: str) -> tuple[Live, Table]:
    """Create a live updating table display."""
    table = create_standard_table(title=table_title)
    config = get_ui_config()  # Get fresh configuration
    refresh_rate = config["refresh_rate"]
    live = Live(table, console=console, refresh_per_second=refresh_rate)
    return live, table


def create_live_connection_monitor() -> Live:
    """Create a live connection monitoring display."""
    layout = create_dashboard_layout()

    # Initialize with connection status
    update_layout_header(layout, "SSH Connection Monitor")
    update_layout_footer(layout, "Press Ctrl+C to exit")

    config = get_ui_config()  # Get fresh configuration
    refresh_rate = config["refresh_rate"]
    live = Live(layout, console=console, refresh_per_second=refresh_rate)
    return live


def update_live_connections(live: Live, connections: dict[str, SSHConnection]) -> None:
    """Update live connection display with current connection data."""
    if hasattr(live, "renderable"):
        # Create connection table
        table = create_standard_table(title="Active Connections")
        table.add_column("Name", style="table.header")
        table.add_column("Host", style="highlight")
        table.add_column("Status", style="success")
        table.add_column("Tunnels", style="info")

        for socket_path, conn in connections.items():
            if isinstance(conn, SSHConnection):
                name = Path(socket_path).name
                status = "Connected"  # This would be determined by actual connection status
                tunnels = str(len(conn.tunnels))
                table.add_row(name, conn.host, status, tunnels)

        # Type assertion: we know renderable is a Layout when it has update method
        layout = live.renderable
        if isinstance(layout, Layout):
            layout["main"].update(table)


# Accessibility and Readability Functions


def create_high_contrast_theme() -> Theme:
    """Create a high contrast theme for better accessibility using Dracula colors."""
    return Theme(
        {
            "info": "#8be9fd",  # Cyan - bright for high contrast
            "warning": "#f1fa8c",  # Yellow - bright for visibility
            "error": "#ff5555",  # Red - bright for errors
            "success": "#50fa7b",  # Green - bright for success
            "header": "#bd93f9",  # Purple - bright for headers
            "accent": "#8be9fd",  # Cyan - bright for accents
            "dim": "#f8f8f2",  # Foreground - bright instead of dim
            "highlight": "#ff79c6",  # Pink - bright for highlights
            "border": "#f8f8f2",  # Foreground - bright borders
            "table.header": "#bd93f9",  # Purple - bright headers
            "table.row": "#f8f8f2",  # Foreground - bright text
            "panel.title": "#bd93f9",  # Purple - bright titles
            "panel.subtitle": "#f8f8f2",  # Foreground - bright subtitles
            "keyword": "#ff79c6",  # Pink - bright keywords
            "operator": "#bd93f9",  # Purple - bright operators
            "string": "#50fa7b",  # Green - bright strings
            "variable": "#f8f8f2",  # Foreground - bright variables
            "number": "#ffb86c",  # Orange - bright numbers
            "comment": "#f8f8f2",  # Foreground - bright comments
            "foreground": "#f8f8f2",  # Foreground - bright text
            # Progress bar specific colors
            "progress.description": "#8be9fd",  # Cyan - for progress descriptions
            "progress.percentage": "#f8f8f2",  # Foreground - for percentage text
            "progress.bar": "#f8f8f2",  # Foreground - bright progress bar background
            "progress.bar.complete": "#50fa7b",  # Green - for completed portion
        }
    )


def create_colorblind_friendly_theme() -> Theme:
    """Create a colorblind-friendly theme using Dracula colors with enhanced differentiation."""
    return Theme(
        {
            "info": "#8be9fd",  # Cyan - distinct from other colors
            "warning": "#f1fa8c",  # Yellow - distinct warning color
            "error": "#ff5555",  # Red - distinct error color
            "success": "#50fa7b",  # Green - distinct success color
            "header": "#bd93f9",  # Purple - distinct header color
            "accent": "#8be9fd",  # Cyan - accent color
            "dim": "#6272a4",  # Comment - muted but readable
            "highlight": "#ff79c6",  # Pink - distinct highlight color
            "border": "#6272a4",  # Comment - subtle borders
            "table.header": "#bd93f9",  # Purple - distinct headers
            "table.row": "#f8f8f2",  # Foreground - readable text
            "panel.title": "#bd93f9",  # Purple - distinct titles
            "panel.subtitle": "#6272a4",  # Comment - readable subtitles
            "keyword": "#ff79c6",  # Pink - distinct keywords
            "operator": "#bd93f9",  # Purple - distinct operators
            "string": "#50fa7b",  # Green - distinct strings
            "variable": "#f8f8f2",  # Foreground - readable variables
            "number": "#ffb86c",  # Orange - distinct numbers
            "comment": "#6272a4",  # Comment - readable comments
            "foreground": "#f8f8f2",  # Foreground - readable text
            # Progress bar specific colors
            "progress.description": "#8be9fd",  # Cyan - for progress descriptions
            "progress.percentage": "#f8f8f2",  # Foreground - for percentage text
            "progress.bar": "#6272a4",  # Comment - progress bar background
            "progress.bar.complete": "#50fa7b",  # Green - for completed portion
        }
    )


def create_readable_table(title: str = "", show_header: bool = True) -> Table:
    """Create a table optimized for readability and accessibility."""
    table = Table(
        title=title,
        border_style="border",
        show_header=show_header,
        header_style="table.header",
        box=ROUNDED,
        padding=(0, 2, 0, 2),  # Increased horizontal padding for better readability
        show_lines=True,  # Add lines between rows for better separation
    )
    return table


def create_accessible_panel(content: str, title: str = "", panel_type: str = "info") -> Panel:
    """Create a panel optimized for accessibility."""
    border_styles = {
        "info": "info",
        "success": "success",
        "error": "error",
        "warning": "warning",
        "accent": "accent",
    }
    border_style = border_styles.get(panel_type, "info")

    return Panel(
        content,
        title=f"[panel.title]{title}[/panel.title]" if title else None,
        border_style=border_style,
        box=ROUNDED,
        padding=(1, 3),  # Increased padding for better readability
        expand=True,  # Expand to full width for better visibility
    )


def display_accessible_message(message: str, message_type: str = "info") -> None:
    """Display a message with accessibility considerations."""
    # Add clear prefixes for screen readers
    prefixes = {
        "info": "INFO:",
        "success": "SUCCESS:",
        "error": "ERROR:",
        "warning": "WARNING:",
    }

    prefix = prefixes.get(message_type, "INFO:")
    styled_message = f"[{message_type}]{prefix}[/{message_type}] {message}"
    console.print(styled_message)


def create_status_with_indicators(status: str, message: str) -> str:
    """Create status indicators with both color and text for accessibility."""
    status_indicators = {
        "success": ("✓", "success"),
        "error": ("✗", "error"),
        "warning": ("⚠", "warning"),
        "info": ("ℹ", "info"),
        "processing": ("⟳", "accent"),
    }

    indicator, color = status_indicators.get(status.lower(), ("ℹ", "info"))
    return f"[{color}]{indicator} {status.upper()}:[/{color}] {message}"


def ensure_terminal_compatibility() -> bool:
    """Check if terminal supports Rich features and provide fallbacks."""
    try:
        # Test if Rich can render properly
        test_console = Console()
        test_console.print("[success]Test[/success]")
        return True
    except Exception:
        # Fallback to basic text output
        return False


def create_fallback_display(content: str) -> None:
    """Create a fallback display for terminals that don't support Rich."""
    # Strip Rich markup for basic terminals
    import re

    clean_content = re.sub(r"\[/?[^\]]*\]", "", content)
    print(clean_content)


def display_message_with_fallback(message: str, message_type: str = "info") -> None:
    """Display a message with fallback for plain text mode."""
    config = get_ui_config()  # Get fresh configuration
    if config["plain_text"] or config["no_rich"]:
        # Use simple text output for plain text mode
        prefixes = {
            "info": "INFO:",
            "success": "SUCCESS:",
            "error": "ERROR:",
            "warning": "WARNING:",
        }
        prefix = prefixes.get(message_type, "INFO:")
        print(f"{prefix} {message}")
    else:
        # Use Rich styling for normal mode
        if message_type == "info":
            display_info(message)
        elif message_type == "success":
            display_success(message)
        elif message_type == "error":
            display_error(message)
        elif message_type == "warning":
            display_warning(message)
        else:
            display_info(message)


# Performance Testing and Optimization Functions


def benchmark_rich_rendering() -> dict[str, float]:
    """Benchmark Rich rendering performance for different components."""
    import time

    results = {}

    # Test table rendering
    start_time = time.time()
    table = create_standard_table(title="Test Table")
    table.add_column("Column 1")
    table.add_column("Column 2")
    for i in range(100):
        table.add_row(f"Row {i}", f"Data {i}")
    console.print(table)
    results["table_100_rows"] = time.time() - start_time

    # Test panel rendering
    start_time = time.time()
    panel = create_info_panel("Test panel content", "Test Panel")
    console.print(panel)
    results["panel"] = time.time() - start_time

    # Test markdown rendering
    start_time = time.time()
    markdown_content = "# Test\n\nThis is a **test** markdown content with *formatting*."
    render_markdown(markdown_content, "Test Markdown")
    results["markdown"] = time.time() - start_time

    return results


def optimize_console_performance() -> Console:
    """Create an optimized console instance for better performance."""
    return Console(
        theme=LAZYSSH_THEME,
        force_terminal=True,  # Force terminal mode for consistent performance
        legacy_windows=False,  # Use modern Windows terminal features
        color_system="auto",  # Auto-detect color capabilities
        file=None,  # Use stdout
        width=None,  # Auto-detect width
        height=None,  # Auto-detect height
    )


def create_cached_table_template(title: str = "") -> Table:
    """Create a cached table template for repeated use."""
    # This would ideally use a caching mechanism in a real implementation
    return create_standard_table(title=title)


def measure_render_time(func: Any) -> Any:
    """Decorator to measure rendering time of UI functions."""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        render_time = end_time - start_time

        # Log performance if rendering takes too long
        if render_time > 0.1:  # 100ms threshold
            console.print(
                f"[warning]Slow render: {func.__name__} took {render_time:.3f}s[/warning]"
            )

        return result

    return wrapper


def create_efficient_progress_bar(total: int = 100) -> Progress:
    """Create an efficient progress bar with minimal overhead."""
    config = get_ui_config()  # Get fresh configuration
    if config["no_animations"]:
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    else:
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )


def batch_render_updates(updates: list[tuple[str, str]]) -> None:
    """Batch multiple UI updates for better performance."""
    # Collect all updates and render them together
    for update_type, content in updates:
        if update_type == "info":
            display_info(content)
        elif update_type == "success":
            display_success(content)
        elif update_type == "error":
            display_error(content)
        elif update_type == "warning":
            display_warning(content)


def profile_ui_performance() -> None:
    """Profile UI performance and provide optimization recommendations."""
    benchmarks = benchmark_rich_rendering()

    console.print("\n[header]UI Performance Report[/header]")
    console.print("=" * 50)

    for test_name, duration in benchmarks.items():
        status = "✓" if duration < 0.1 else "⚠" if duration < 0.5 else "✗"
        console.print(f"{status} {test_name}: {duration:.3f}s")

    # Provide recommendations
    slow_tests = [name for name, duration in benchmarks.items() if duration > 0.1]
    if slow_tests:
        console.print(f"\n[warning]Slow components detected: {', '.join(slow_tests)}[/warning]")
        console.print("[info]Consider using caching or reducing update frequency[/info]")
    else:
        console.print("\n[success]All components performing well![/success]")
