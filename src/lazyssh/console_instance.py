"""Centralized Rich Console management for LazySSH"""

import os
import shutil
import subprocess
from typing import Any

from rich.console import Console
from rich.theme import Theme

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
        result = shutil.which("tput")
        if result:
            cols = subprocess.check_output(["tput", "cols"], text=True).strip()
            return int(cols)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        pass

    # Fallback to a reasonable default
    return 80


def create_high_contrast_theme() -> Theme:
    """Create a high contrast theme."""
    return Theme(
        {
            "info": "bright_cyan",
            "warning": "bright_yellow",
            "error": "bright_red",
            "success": "bright_green",
            "header": "bright_magenta",
            "accent": "bright_cyan",
            "dim": "bright_black",
            "highlight": "bright_magenta",
            "border": "bright_white",
            "table.header": "bright_magenta",
            "table.row": "bright_white",
            "panel.title": "bright_magenta",
            "panel.subtitle": "bright_black",
            "keyword": "bright_magenta",
            "operator": "bright_magenta",
            "string": "bright_green",
            "variable": "bright_white",
            "number": "bright_yellow",
            "comment": "bright_black",
            "foreground": "bright_white",
            "background": "black",
            "progress.description": "bright_cyan",
            "progress.percentage": "bright_white",
            "progress.bar": "bright_black",
            "progress.bar.complete": "bright_green",
        }
    )


def create_colorblind_friendly_theme() -> Theme:
    """Create a colorblind-friendly theme."""
    return Theme(
        {
            "info": "bright_blue",
            "warning": "bright_yellow",
            "error": "bright_red",
            "success": "bright_green",
            "header": "bright_magenta",
            "accent": "bright_blue",
            "dim": "bright_black",
            "highlight": "bright_white",
            "border": "bright_black",
            "table.header": "bright_magenta",
            "table.row": "white",
            "panel.title": "bright_magenta",
            "panel.subtitle": "bright_black",
            "keyword": "bright_white",
            "operator": "bright_magenta",
            "string": "bright_green",
            "variable": "white",
            "number": "bright_yellow",
            "comment": "bright_black",
            "foreground": "white",
            "background": "black",
            "progress.description": "bright_blue",
            "progress.percentage": "white",
            "progress.bar": "bright_black",
            "progress.bar.complete": "bright_green",
        }
    )


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


# Display functions
def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[error]Error:[/error] {message}")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[success]Success:[/success] {message}")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[info]{message}[/info]")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[warning]Warning:[/warning] {message}")


def display_accessible_message(message: str, message_type: str = "info") -> None:
    """Display a message with accessibility considerations."""
    if message_type == "error":
        display_error(message)
    elif message_type == "success":
        display_success(message)
    elif message_type == "warning":
        display_warning(message)
    else:
        display_info(message)


def display_message_with_fallback(message: str, message_type: str = "info") -> None:
    """Display a message with fallback for different environments."""
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
