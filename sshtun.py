#!/usr/bin/env python

import subprocess
import readline

# Dictionary to store active tunnels
active_tunnels = {}
# Dictionary to store SSH control sockets with user and server info
ssh_sockets = {}

def create_forward_tunnel(spec, ssh_socket, user, ssh_server):
    """
    Creates a forward tunnel through a separate SSH control socket.
    """
    try:
        local_port, remote_host, remote_port = spec.split()
        forward_command = [
            'ssh', '-S', ssh_socket, '-fnNT',
            '-L', f'{local_port}:{remote_host}:{remote_port}',
            f"{user}@{ssh_server}"
        ]
        print("Forward command:", " ".join(forward_command))  # Print the forward command
        subprocess.run(forward_command, check=True)
        print(f"Forward tunnel created: {local_port} -> {remote_host}:{remote_port} through {ssh_socket}")
        active_tunnels[len(active_tunnels) + 1] = {
            'type': 'forward',
            'local_port': local_port,
            'remote_host': remote_host,
            'remote_port': remote_port,
            'ssh_socket': ssh_socket
        }
    except subprocess.CalledProcessError as e:
        print(f"Error creating forward tunnel: {e}")

def create_reverse_tunnel(spec, ssh_socket, user, ssh_server):
    """
    Creates a reverse tunnel through a separate SSH control socket.
    """
    try:
        local_port, remote_host, remote_port = spec.split()
        reverse_command = [
            'ssh', '-S', ssh_socket, '-fnNT',
            '-R', f'{local_port}:{remote_host}:{remote_port}',
            f"{user}@{ssh_server}"
        ]
        print("Reverse command:", " ".join(reverse_command))  # Print the reverse command
        subprocess.run(reverse_command, check=True)
        print(f"Reverse tunnel created: {local_port} -> {remote_host}:{remote_port} through {ssh_socket}")
        active_tunnels[len(active_tunnels) + 1] = {
            'type': 'reverse',
            'local_port': local_port,
            'remote_host': remote_host,
            'remote_port': remote_port,
            'ssh_socket': ssh_socket
        }
    except subprocess.CalledProcessError as e:
        print(f"Error creating reverse tunnel: {e}")

def kill_tunnel(tunnel_number):
    """
    Kills the specified tunnel.
    """
    if tunnel_number in active_tunnels:
        tunnel = active_tunnels.pop(tunnel_number)
        try:
            cancel_command = ['ssh', '-S', tunnel['ssh_socket'], '-O', 'cancel']
            if tunnel['type'] == 'forward':
                cancel_command.extend(['-L', f"{tunnel['local_port']}:{tunnel['remote_host']}:{tunnel['remote_port']}"])
            elif tunnel['type'] == 'reverse':
                cancel_command.extend(['-R', f"{tunnel['local_port']}:{tunnel['remote_host']}:{tunnel['remote_port']}"])
            cancel_command.append(f"{ssh_sockets[tunnel['ssh_socket']]['user']}@{ssh_sockets[tunnel['ssh_socket']]['server']}")
            print("Cancel command:", " ".join(cancel_command))  # Print the cancel command
            subprocess.run(cancel_command, check=True)
            print(f"Tunnel {tunnel_number} ({tunnel['type']}) killed")
        except subprocess.CalledProcessError as e:
            print(f"Error killing tunnel: {e}")
    else:
        print("Tunnel not found")

def list_active_tunnels():
    """
    Lists all active SSH tunnels created.
    """
    if active_tunnels:
        print("Active tunnels:")
        for num, tunnel in active_tunnels.items():
            print(f"{num}: {tunnel['type']} - {tunnel['local_port']} -> {tunnel['remote_host']}:{tunnel['remote_port']} through {tunnel['ssh_socket']}")
    else:
        print("No active tunnels created.")

def add_socket(path, user, ssh_server):
    """
    Adds a new SSH control socket to be tracked.
    """
    ssh_sockets[path] = {'socket': path, 'user': user, 'server': ssh_server}
    print(f"Socket {path} added: {path}")

def remove_socket(path):
    """
    Removes an SSH control socket from being tracked.
    """
    if path in ssh_sockets:
        ssh_socket = ssh_sockets.pop(path)
        print(f"Socket {path} removed: {ssh_socket['socket']}")
    else:
        print("Socket not found")

def list_sockets():
    """
    Lists all active SSH control sockets.
    """
    if ssh_sockets:
        print("Active sockets:")
        for path, info in ssh_sockets.items():
            print(f"{path}: {info['socket']} (User: {info['user']}, Server: {info['server']})")
    else:
        print("No active sockets created.")

def display_status():
    """
    Displays the status of all active sockets and tunnels.
    """
    print("\n--- Status ---")
    list_sockets()
    list_active_tunnels()
    print("----------------\n")

def main():
    print("Welcome to sshtun CLI")
    try:
        while True:
            # Readline configuration
            readline.parse_and_bind(r'"\e[A": history-search-backward')  # Up arrow key
            
            display_status()
            
            try:
                cmd = input("sshtun> ").lower()
            except KeyboardInterrupt:
                print("\nCtrl + C detected. Use 'exit' to exit the program.")
                continue

            if cmd.startswith("add "):
                parts = cmd.split()
                if len(parts) == 4:
                    path, user, ssh_server = parts[1], parts[2], parts[3]
                    add_socket(path, user, ssh_server)
                else:
                    print("Invalid command format. Use 'add <path> <user> <ssh_server>'.")
            elif cmd.startswith("remove "):
                parts = cmd.split()
                if len(parts) == 2:
                    path = parts[1]
                    remove_socket(path)
                else:
                    print("Invalid command format. Use 'remove <path>'.")
            elif cmd.startswith("l "):
                parts = cmd.split()
                if len(parts) == 5:
                    path, local_port, remote_host, remote_port = parts[1], parts[2], parts[3], parts[4]
                    spec = f"{local_port} {remote_host} {remote_port}"
                    if path in ssh_sockets:
                        user, ssh_server = ssh_sockets[path]['user'], ssh_sockets[path]['server']
                        create_forward_tunnel(spec, ssh_sockets[path]['socket'], user, ssh_server)
                    else:
                        print(f"Socket {path} not found.")
                else:
                    print("Invalid command format. Use 'l <path> <local_port> <remote_host> <remote_port>'.")
            elif cmd.startswith("r "):
                parts = cmd.split()
                if len(parts) == 5:
                    path, local_port, remote_host, remote_port = parts[1], parts[2], parts[3], parts[4]
                    spec = f"{local_port} {remote_host} {remote_port}"
                    if path in ssh_sockets:
                        user, ssh_server = ssh_sockets[path]['user'], ssh_sockets[path]['server']
                        create_reverse_tunnel(spec, ssh_sockets[path]['socket'], user, ssh_server)
                    else:
                        print(f"Socket {path} not found.")
                else:
                    print("Invalid command format. Use 'r <path> <local_port> <remote_host> <remote_port>'.")
            elif cmd.startswith("kill"):
                parts = cmd.split()
                if len(parts) == 2 and parts[1].isdigit():
                    tunnel_number = int(parts[1])
                    if tunnel_number in active_tunnels:
                        kill_tunnel(tunnel_number)
                    else:
                        print("Tunnel not found.")
                else:
                    print("Invalid command format. Use 'kill <tunnel_number>'.")
            elif cmd == "list":
                list_active_tunnels()
            elif cmd == "sockets":
                list_sockets()
            elif cmd == "exit":
                print("Exiting...")
                break
            elif cmd == "help":
                print("""
Available commands:
  add <path> <user> <ssh_server>: Add a new SSH control socket to be tracked
  remove <path>: Remove an existing SSH control socket from being tracked
  l <path> <local_port> <remote_host> <remote_port>: Create a forward tunnel
  r <path> <local_port> <remote_host> <remote_port>: Create a reverse tunnel
  kill <tunnel_number>: Kill a specific tunnel
  list: List all active tunnels
  sockets: List all active sockets
  exit: Exit the program
  help: Show this help message
                      
  Example:
      add /tmp/my_socket user@example.com
      remove /tmp/my_socket
      l /tmp/my_socket 1234 192.168.1.1 22
      r /tmp/my_socket 443 127.0.0.1 8080
""")
            else:
                print("Unknown command. Type 'help' for a list of available commands.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
