#!/usr/bin/env python3
"""
LazySSH - Main module providing the entry point and interactive menus.
"""
from __future__ import annotations

import sys

import click
from rich.prompt import Confirm

from lazyssh import check_dependencies
from lazyssh.command_mode import CommandMode
from lazyssh.config import initialize_config_file, load_configs
from lazyssh.console_instance import (
    console,
    display_error,
    display_info,
    display_success,
    display_warning,
)
from lazyssh.logging_module import APP_LOGGER, ensure_log_directory
from lazyssh.plugin_manager import ensure_runtime_plugins_dir
from lazyssh.ssh import SSHManager
from lazyssh.ui import display_banner, display_saved_configs, display_ssh_status, display_tunnels

# Initialize the SSH manager for the application
ssh_manager = SSHManager()


def show_status() -> None:
    """
    Display loaded configurations, current SSH connections and tunnels status.

    This function will display saved configurations (if any), print a table of
    active SSH connections and detailed information about any tunnels associated with them.
    """
    from .config import load_configs
    from .ui import display_saved_configs

    # Display loaded configurations (if any exist)
    configs = load_configs()
    if configs:
        display_saved_configs(configs)

    # Display active SSH connections
    if ssh_manager.connections:
        display_ssh_status(ssh_manager.connections, ssh_manager.get_current_terminal_method())
        for socket_path, conn in ssh_manager.connections.items():
            if conn.tunnels:  # Only show tunnels table if there are tunnels
                display_tunnels(socket_path, conn)


def close_all_connections() -> None:
    """Close all active SSH connections before exiting."""
    display_info("\nClosing all connections...")
    successful_closures = 0
    total_connections = len(ssh_manager.connections)

    # Create a copy of the connections to avoid modification during iteration
    for socket_path in list(ssh_manager.connections.keys()):
        try:
            if ssh_manager.close_connection(socket_path):
                successful_closures += 1
        except Exception as e:
            display_warning(f"Failed to close connection for {socket_path}: {str(e)}")

    # Report closure results
    if successful_closures == total_connections:
        if total_connections > 0:
            display_success(f"Successfully closed all {total_connections} connections")
    else:
        display_warning(f"Closed {successful_closures} out of {total_connections} connections")
        display_info("Some connections may require manual cleanup")


def check_active_connections() -> bool:
    """
    Check if there are active connections and prompt for confirmation before closing.

    Returns:
        True if the user confirmed or there are no active connections, False otherwise.
    """
    if ssh_manager.connections and not Confirm.ask(
        "You have active connections. Close them and exit?"
    ):
        return False
    return True


def safe_exit() -> None:
    """Safely exit the program, closing all connections."""
    close_all_connections()
    sys.exit(0)


@click.command()
@click.option("--debug", is_flag=True, help="Enable debug logging to console")
@click.option(
    "--config",
    type=click.Path(exists=False),
    default=None,
    help="Load configuration file on startup (default: /tmp/lazyssh/connections.conf)",
)
def main(debug: bool, config: str | None) -> None:
    """
    LazySSH - A comprehensive SSH toolkit for managing connections and tunnels.

    This is the main entry point for the application. It initializes the program,
    checks dependencies, and starts the command mode interface.
    """
    try:
        # Initialize logging first
        ensure_log_directory()
        if APP_LOGGER:
            APP_LOGGER.info("Starting LazySSH")

        # Enable debug logging if requested
        if debug:
            from lazyssh.logging_module import set_debug_mode

            set_debug_mode(True)
            if APP_LOGGER:
                APP_LOGGER.debug("Debug logging enabled")

        # Initialize config file with examples if it doesn't exist
        initialize_config_file()

        # Ensure runtime plugin directory exists (best-effort)
        ensure_runtime_plugins_dir()

        # Display banner
        display_banner()

        # Load and display configurations if --config flag is provided
        if config is not None:
            # If config is an empty string or flag was used without value, use default path
            config_path = config if config else None
            configs = load_configs(config_path)
            if configs:
                display_saved_configs(configs)
                if APP_LOGGER:
                    APP_LOGGER.info(f"Loaded {len(configs)} configuration(s) from config file")
            else:
                if config:
                    display_warning(f"Configuration file not found or empty: {config}")
                else:
                    display_warning("No saved configurations found")
                if APP_LOGGER:
                    APP_LOGGER.warning("No configurations loaded")

        # Check dependencies
        required_missing, optional_missing = check_dependencies()

        # Display warnings for optional missing dependencies
        if optional_missing:
            display_warning("Missing optional dependencies:")
            for dep in optional_missing:
                console.print(f"  - {dep}")
            display_info("Native terminal method will be used as fallback.")

        # Exit only if required dependencies are missing
        if required_missing:
            display_error("Missing required dependencies:")
            for dep in required_missing:
                console.print(f"  - {dep}")
            display_info("Please install the required dependencies and try again.")
            sys.exit(1)

        # Start in command mode (default interface)
        if APP_LOGGER:
            APP_LOGGER.info("Starting in command mode")
        cmd_mode = CommandMode(ssh_manager)
        cmd_mode.run()

    except KeyboardInterrupt:
        display_warning("\nUse the exit command to safely exit LazySSH.")
        try:
            input("\nPress Enter to continue...")
            return None  # Return to caller
        except KeyboardInterrupt:
            if APP_LOGGER:
                APP_LOGGER.info("LazySSH terminated by user (KeyboardInterrupt)")
            display_info("\nExiting...")
            if check_active_connections():
                safe_exit()
    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.exception(f"Unhandled exception: {str(e)}")
        display_error(f"An unexpected error occurred: {str(e)}")
        display_info("Please report this issue on GitHub.")
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
