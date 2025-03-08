#!/usr/bin/env python3
import click
import os
import sys
from rich.prompt import Confirm
from typing import Dict, List, Tuple

from lazyssh import check_dependencies
from lazyssh.ssh import SSHManager
from lazyssh.models import SSHConnection
from lazyssh.command_mode import CommandMode
from lazyssh.ui import (
    display_banner, display_menu, get_user_input, 
    display_error, display_success, display_info,
    display_warning, display_ssh_status, display_tunnels
)

ssh_manager = SSHManager()

def show_status():
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
    elif choice == "6":
        return "mode"  # Special return value to trigger mode switch
    return success

def main_menu():
    show_status()
    options = {
        "1": "Create new SSH connection",
        "2": "Destroy tunnel",
        "3": "Create tunnel",
        "4": "Open terminal",
        "5": "Close connection",
        "6": "Switch to command mode",
        "7": "Exit"
    }
    display_menu(options)
    return get_user_input("Choose an option")

def create_connection_menu():
    """Menu for creating a new SSH connection"""
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
    use_proxy = get_user_input("Create dynamic SOCKS proxy? (y/N)").lower() == 'y'
    dynamic_port = None
    
    if use_proxy:
        proxy_port = get_user_input("Enter proxy port (default: 1080)")
        if not proxy_port:
            dynamic_port = 1080
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
        socket_path=f"/tmp/lazyssh/{socket_name}",
        dynamic_port=dynamic_port
    )
    
    # The SSH command will be displayed by the create_connection method
    
    if ssh_manager.create_connection(conn):
        display_success(f"Connection '{socket_name}' established")
        if dynamic_port:
            display_success(f"Dynamic proxy created on port {dynamic_port}")
        return True
    return False

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
            
            if ssh_manager.create_tunnel(socket_path, local_port, remote_host, remote_port, is_reverse):
                display_success(f"{tunnel_type_str.capitalize()} tunnel created: {local_port} -> {remote_host}:{remote_port}")
                return True
            else:
                # Error already displayed by create_tunnel
                return False
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
            
            # The SSH command will be displayed by the open_terminal method
            
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
            tunnel_id = get_user_input("Enter tunnel ID to destroy (or press Enter to cancel)")
            
            if tunnel_id:
                # Find the tunnel
                tunnel = conn.get_tunnel(tunnel_id)
                if tunnel:
                    # Build the command for display
                    if tunnel.type == "reverse":
                        tunnel_args = f"-O cancel -R {tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"
                    else:
                        tunnel_args = f"-O cancel -L {tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"
                    
                    cmd = f"ssh -S {socket_path} {tunnel_args} dummy"
                    
                    # Display the command that will be executed
                    display_info("The following SSH command will be executed:")
                    display_info(cmd)
                
                if ssh_manager.close_tunnel(socket_path, tunnel_id):
                    display_success("Tunnel destroyed successfully")
                else:
                    display_error("Failed to destroy tunnel")
        else:
            display_error("Invalid connection number")
    except ValueError:
        display_error("Invalid input")

def close_all_connections():
    """Close all active connections and clean up"""
    display_info("\nClosing all connections...")
    for socket_path in list(ssh_manager.connections.keys()):
        ssh_manager.close_connection(socket_path)

def check_active_connections():
    """Check if there are active connections and ask for confirmation if there are"""
    if ssh_manager.connections:
        return Confirm.ask("\nThere are active SSH connections. Are you sure you want to exit?")
    return True

def safe_exit():
    """Safely exit the program, closing all connections"""
    display_info("\nClosing all connections...")
    for socket_path in list(ssh_manager.connections.keys()):
        ssh_manager.close_connection(socket_path)
    sys.exit(0)

def prompt_mode_main():
    """Main function for prompt (menu-based) mode"""
    while True:
        try:
            choice = main_menu()
            if choice == "7":
                if check_active_connections():
                    safe_exit()
                return
            
            result = handle_menu_action(choice)
            if result == "mode":
                return  # Return to trigger mode switch
        except KeyboardInterrupt:
            display_info("\nUse option 7 to exit.")
        except Exception as e:
            display_error(f"Error: {str(e)}")

@click.command()
@click.option('--prompt', is_flag=True, help='Start in prompt mode instead of command mode')
def main(prompt: bool):
    """LazySSH - A comprehensive SSH toolkit for managing connections and tunnels"""
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
                prompt_mode_main()
                current_mode = "command"
            else:
                display_info("Current mode: Command (type 'mode' to switch to prompt mode)")
                cmd_mode = CommandMode(ssh_manager)
                cmd_mode.run()
                current_mode = "prompt"
    
    except KeyboardInterrupt:
        safe_exit()
    except Exception as e:
        display_error(f"An unexpected error occurred: {str(e)}")
        safe_exit()

if __name__ == "__main__":
    main()