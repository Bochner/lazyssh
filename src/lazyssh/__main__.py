#!/usr/bin/env python3
"""
LazySSH - Main module providing the entry point and interactive menus.
"""
from __future__ import annotations

import sys
from typing import Literal

import click
from rich.prompt import Confirm

from lazyssh import check_dependencies
from lazyssh.command_mode import CommandMode
from lazyssh.models import SSHConnection
from lazyssh.ssh import SSHManager
from lazyssh.ui import (
    display_banner,
    display_error,
    display_info,
    display_menu,
    display_ssh_status,
    display_success,
    display_tunnels,
    display_warning,
    get_user_input,
)

# Initialize the SSH manager for the application
ssh_manager = SSHManager()


def show_status() -> None:
    """
    Display current SSH connections and tunnels status.

    This function will print a table of active SSH connections and
    detailed information about any tunnels associated with them.
    """
    if ssh_manager.connections:
        display_ssh_status(ssh_manager.connections)
        for socket_path, conn in ssh_manager.connections.items():
            if conn.tunnels:  # Only show tunnels table if there are tunnels
                display_tunnels(socket_path, conn)


def handle_menu_action(choice: str) -> bool | Literal["mode"]:
    """
    Process the menu choice and execute the corresponding action.

    Args:
        choice: The menu option selected by the user

    Returns:
        True if the action was successful, False if it failed,
        or "mode" to indicate a mode switch is requested.
    """
    success = False
    if choice == "1":
        create_connection_menu()
        success = True  # Always true as the connection creation handles its own success message
    elif choice == "2":
        manage_tunnels_menu()
        success = True  # Always show updated status after tunnel management
    elif choice == "3":
        success = tunnel_menu()
    elif choice == "4":
        success = terminal_menu()
    elif choice == "5":
        success = close_connection_menu()
    elif choice == "6":
        return "mode"  # Special return value to trigger mode switch
    return success


def main_menu() -> str:
    """
    Display the main menu and get the user's choice.

    Returns:
        The user's menu selection
    """
    show_status()
    options = {
        "1": "Create new SSH connection",
        "2": "Destroy tunnel",
        "3": "Create tunnel",
        "4": "Open terminal",
        "5": "Close connection",
        "6": "Switch to command mode",
        "7": "Exit",
    }
    display_menu(options)
    choice = get_user_input("Choose an option")
    return str(choice)  # Ensure we return a string


def create_connection_menu() -> bool:
    """
    Interactive menu for creating a new SSH connection.

    Prompts the user for connection details including host, port, username,
    and optional dynamic proxy settings.

    Returns:
        True if the connection was successfully created, False otherwise.
    """
    display_info("\nCreate new SSH connection")
    host = get_user_input("Enter hostname or IP")
    port = get_user_input("Enter port (default: 22)")
    if not port:
        port = "22"

    socket_name = get_user_input("Enter connection name (used as identifier)")
    if not socket_name:
        display_error("Connection name is required")
        return False

    username = get_user_input("Enter username")
    if not username:
        display_error("Username is required")
        return False

    # Ask about dynamic proxy
    use_proxy = get_user_input("Create dynamic SOCKS proxy? (y/N)").lower() == "y"
    dynamic_port = None

    if use_proxy:
        proxy_port = get_user_input("Enter proxy port (default: 9050)")
        if not proxy_port:
            dynamic_port = 9050
        else:
            try:
                dynamic_port = int(proxy_port)
            except ValueError:
                display_error("Port must be a number")
                return False

    # Create the connection
    conn = SSHConnection(
        host=host,
        port=int(port),
        username=username,
        socket_path=f"/tmp/{socket_name}",
        dynamic_port=dynamic_port,
    )

    # The SSH command will be displayed by the create_connection method

    if ssh_manager.create_connection(conn):
        display_success(f"Connection '{socket_name}' established")
        if dynamic_port:
            display_success(f"Dynamic proxy created on port {dynamic_port}")
        return True
    return False


def tunnel_menu() -> bool:
    """
    Interactive menu for creating a new tunnel.

    Allows the user to select an active SSH connection and create either
    a forward or reverse tunnel with specified ports and hosts.

    Returns:
        True if the tunnel was successfully created, False otherwise.
    """
    if not ssh_manager.connections:
        display_error("No active connections")
        return False

    display_info("Select connection:")
    for i, (socket_path, conn) in enumerate(ssh_manager.connections.items(), 1):
        display_info(f"{i}. {conn.host} ({conn.username})")

    try:
        choice = int(get_user_input("Enter connection number")) - 1
        if 0 <= choice < len(ssh_manager.connections):
            socket_path = list(ssh_manager.connections.keys())[choice]

            tunnel_type = get_user_input("Tunnel type (f)orward or (r)everse").lower()
            local_port = int(get_user_input("Enter local port"))
            remote_host = get_user_input("Enter remote host")
            remote_port = int(get_user_input("Enter remote port"))

            is_reverse = tunnel_type.startswith("r")

            # Build the command for display
            if is_reverse:
                tunnel_args = f"-O forward -R {local_port}:{remote_host}:{remote_port}"
                tunnel_type_str = "reverse"
            else:
                tunnel_args = f"-O forward -L {local_port}:{remote_host}:{remote_port}"
                tunnel_type_str = "forward"

            cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

            # Display the command that will be executed
            display_info("The following SSH command will be executed:")
            display_info(cmd)

            if ssh_manager.create_tunnel(
                socket_path, local_port, remote_host, remote_port, is_reverse
            ):
                display_success(
                    f"{tunnel_type_str.capitalize()} tunnel created: "
                    f"{local_port} -> {remote_host}:{remote_port}"
                )
                return True
            else:
                # Error already displayed by create_tunnel
                return False
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")
    return False


def terminal_menu() -> bool:
    """
    Interactive menu for opening a terminal connection.

    Allows the user to select an active SSH connection and open
    a terminal session to that host.

    Returns:
        True if the terminal was successfully opened, False otherwise.
    """
    if not ssh_manager.connections:
        display_error("No active connections")
        return False

    display_info("Select connection:")
    for i, (socket_path, conn) in enumerate(ssh_manager.connections.items(), 1):
        display_info(f"{i}. {conn.host} ({conn.username})")

    try:
        choice = int(get_user_input("Enter connection number")) - 1
        if 0 <= choice < len(ssh_manager.connections):
            socket_path = list(ssh_manager.connections.keys())[choice]

            # The SSH command will be displayed by the open_terminal method

            ssh_manager.open_terminal(socket_path)
            return True
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")
    return False


def close_connection_menu() -> bool:
    """
    Interactive menu for closing an SSH connection.

    Allows the user to select an active SSH connection to close.
    All tunnels associated with the connection will also be closed.

    Returns:
        True if the connection was successfully closed, False otherwise.
    """
    if not ssh_manager.connections:
        display_error("No active connections")
        return False

    display_info("Select connection to close:")
    for i, (socket_path, conn) in enumerate(ssh_manager.connections.items(), 1):
        display_info(f"{i}. {conn.host} ({conn.username})")

    try:
        choice = int(get_user_input("Enter connection number")) - 1
        if 0 <= choice < len(ssh_manager.connections):
            socket_path = list(ssh_manager.connections.keys())[choice]

            # Build the command for display
            cmd = f"ssh -S {socket_path} -O exit dummy"

            # Display the command that will be executed
            display_info("The following SSH command will be executed:")
            display_info(cmd)

            if ssh_manager.close_connection(socket_path):
                display_success("Connection closed successfully")
                return True
            else:
                display_error("Failed to close connection")
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")
    return False


def manage_tunnels_menu() -> None:
    """
    Interactive menu for managing tunnels.

    Allows the user to view and delete tunnels for active SSH connections.
    """
    if not ssh_manager.connections:
        display_error("No active connections")
        return

    # Check if there are any tunnels
    has_tunnels = False
    for socket_path, conn in ssh_manager.connections.items():
        if conn.tunnels:
            has_tunnels = True
            break

    if not has_tunnels:
        display_info("No active tunnels")
        return

    # Display tunnels
    for socket_path, conn in ssh_manager.connections.items():
        if conn.tunnels:
            display_tunnels(socket_path, conn)

    # Prompt for tunnel to delete
    tunnel_id = get_user_input("Enter tunnel ID to delete (or 'q' to cancel)")
    if tunnel_id.lower() == "q":
        return

    # Find the tunnel
    for socket_path, conn in ssh_manager.connections.items():
        for tunnel in conn.tunnels:
            if tunnel.id == tunnel_id:
                # Build the command for display
                if tunnel.type == "reverse":
                    tunnel_args = (
                        f"-O cancel -R {tunnel.local_port}:"
                        f"{tunnel.remote_host}:{tunnel.remote_port}"
                    )
                else:
                    tunnel_args = (
                        f"-O cancel -L {tunnel.local_port}:"
                        f"{tunnel.remote_host}:{tunnel.remote_port}"
                    )

                cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

                # Display the command that will be executed
                display_info("The following SSH command will be executed:")
                display_info(cmd)

                if ssh_manager.close_tunnel(socket_path, tunnel_id):
                    display_success(f"Tunnel {tunnel_id} closed")
                    return
                else:
                    display_error(f"Failed to close tunnel {tunnel_id}")
                    return

    display_error(f"Tunnel with ID {tunnel_id} not found")


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


def prompt_mode_main() -> Literal["mode"] | None:
    """
    Main function for prompt (menu-based) mode.

    Returns:
        "mode" if the user wants to switch to command mode, None if the program should exit.
    """
    while True:
        try:
            choice = main_menu()
            if choice == "7":
                if check_active_connections():
                    safe_exit()
                return None

            result = handle_menu_action(choice)
            if result == "mode":
                return "mode"  # Return to trigger mode switch
        except KeyboardInterrupt:
            display_warning("\nUse option 7 to safely exit LazySSH.")
        except Exception as e:
            display_error(f"Error: {str(e)}")


@click.command()
@click.option("--prompt", is_flag=True, help="Start in prompt mode instead of command mode")
def main(prompt: bool) -> None:
    """
    LazySSH - A comprehensive SSH toolkit for managing connections and tunnels.

    This is the main entry point for the application. It initializes the program,
    checks dependencies, and starts the appropriate interface mode (command or prompt).
    """
    try:
        # Check dependencies
        missing_deps = check_dependencies()
        if missing_deps:
            display_error("Missing required dependencies:")
            for dep in missing_deps:
                display_error(f"  - {dep}")
            display_info("Please install the required dependencies and try again.")
            sys.exit(1)

        # Display banner
        display_banner()

        # Start in the specified mode
        current_mode = "prompt" if prompt else "command"

        while True:
            if current_mode == "prompt":
                display_info("Current mode: Prompt (use option 6 to switch to command mode)")
                _ = prompt_mode_main()  # Use _ to indicate unused result
                current_mode = "command"
            else:
                display_info("Current mode: Command (type 'mode' to switch to prompt mode)")
                cmd_mode = CommandMode(ssh_manager)
                cmd_mode.run()
                current_mode = "prompt"
    except KeyboardInterrupt:
        display_warning("\nUse the exit command to safely exit LazySSH.")
        try:
            input("\nPress Enter to continue...")
            main(prompt)  # Restart the main function
            return None  # Explicitly return None
        except KeyboardInterrupt:
            display_info("\nExiting...")
            if check_active_connections():
                safe_exit()


if __name__ == "__main__":
    main()
