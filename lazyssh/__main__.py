#!/usr/bin/env python3
import click
import os
from rich.prompt import Confirm
from typing import Dict

from lazyssh import check_dependencies
from lazyssh.ssh import SSHManager
from lazyssh.models import SSHConnection
from lazyssh.ui import (
    display_banner, display_menu, get_user_input, 
    display_error, display_success, display_info,
    display_warning, display_ssh_status, display_tunnels
)

ssh_manager = SSHManager()

def display_current_status():
    """Display current SSH connections and tunnels status"""
    if ssh_manager.connections:
        display_ssh_status(ssh_manager.connections)
        for socket_path, conn in ssh_manager.connections.items():
            if conn.tunnels:  # Only show tunnels table if there are tunnels
                display_tunnels(socket_path, conn)

def handle_menu_action(choice: str) -> bool:
    """Handle menu choices and return True if action was successful"""
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
    return success

def main_menu():
    display_current_status()
    options = {
        "1": "Create new SSH connection",
        "2": "Destroy tunnel",
        "3": "Create tunnel",
        "4": "Open terminal session",
        "5": "Close connection",
        "q": "Quit"
    }
    display_menu(options)
    return get_user_input("Select an option")

def create_connection_menu():
    host = get_user_input("Enter host")
    port = int(get_user_input("Enter port") or "22")
    username = get_user_input("Enter username")
    socket_name = get_user_input("Enter connection name (for socket)")
    
    socket_path = os.path.join(ssh_manager.control_path_base, socket_name)
    
    dynamic_port = get_user_input("Enter dynamic port (optional)")
    if dynamic_port:
        dynamic_port = int(dynamic_port)
    
    identity_file = get_user_input("Enter identity file path (optional)")
    
    conn = SSHConnection(
        host=host,
        port=port,
        username=username,
        socket_path=socket_path,
        dynamic_port=dynamic_port,
        identity_file=identity_file
    )
    
    if ssh_manager.create_connection(conn):
        display_success(f"Connection established to {host}")
    else:
        display_error("Failed to create connection")

def tunnel_menu():
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
            
            is_reverse = tunnel_type.startswith('r')
            if ssh_manager.create_tunnel(socket_path, local_port, remote_host, remote_port, is_reverse):
                display_success("Tunnel created successfully")
                return True
            else:
                display_error("Failed to create tunnel")
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")
    return False

def terminal_menu():
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
            ssh_manager.open_terminal(socket_path)
            return True
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")
    return False

def close_connection_menu():
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

def manage_tunnels_menu():
    if not ssh_manager.connections:
        display_error("No active connections")
        return

    display_info("Select connection to destroy tunnel:")
    for i, (socket_path, conn) in enumerate(ssh_manager.connections.items(), 1):
        display_info(f"{i}. {conn.host} ({conn.username})")
    
    try:
        choice = int(get_user_input("Enter connection number")) - 1
        if 0 <= choice < len(ssh_manager.connections):
            socket_path = list(ssh_manager.connections.keys())[choice]
            conn = ssh_manager.connections[socket_path]
            
            if not conn.tunnels:
                display_info("No tunnels for this connection")
                return
                
            display_tunnels(socket_path, conn)
            tunnel_choice = get_user_input("Enter tunnel number to destroy (or press Enter to cancel)")
            
            if tunnel_choice.isdigit():
                tunnel_idx = int(tunnel_choice) - 1
                if ssh_manager.close_tunnel(socket_path, tunnel_idx):
                    display_success("Tunnel destroyed successfully")
                else:
                    display_error("Failed to destroy tunnel")
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")

@click.command()
def main():
    display_banner()
    
    # Check dependencies at startup
    missing_deps = check_dependencies()
    if missing_deps:
        display_warning("Missing system dependencies:")
        for dep in missing_deps:
            display_warning(f"- {dep}")
        display_warning("Please install the missing dependencies for full functionality")
    
    while True:
        choice = main_menu()
        
        if choice.lower() == "q":
            if Confirm.ask("Are you sure you want to quit?"):
                # Close all connections before exiting
                for socket_path in list(ssh_manager.connections.keys()):
                    ssh_manager.close_connection(socket_path)
                break
        else:
            handle_menu_action(choice)

if __name__ == "__main__":
    main()