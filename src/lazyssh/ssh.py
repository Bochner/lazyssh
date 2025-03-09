import os
import subprocess
import time
from typing import Dict

from rich.console import Console
from .ui import display_error, display_info, display_success
from .models import SSHConnection

console = Console()


class SSHManager:
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
        self.control_path_base = "/tmp/lazyssh/"
        os.makedirs(self.control_path_base, exist_ok=True)
        os.chmod(self.control_path_base, 0o700)

    def create_connection(self, conn: SSHConnection) -> bool:
        try:
            cmd = [
                "ssh",
                "-M",  # Master mode
                "-S",
                conn.socket_path,
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "StrictHostKeyChecking=no",
                "-f",
                "-N",  # Background mode
            ]

            if conn.port:
                cmd.extend(["-p", str(conn.port)])
            if conn.dynamic_port:
                cmd.extend(["-D", str(conn.dynamic_port)])
            if conn.identity_file:
                cmd.extend(["-i", os.path.expanduser(conn.identity_file)])

            cmd.append(f"{conn.username}@{conn.host}")

            # Display the command that will be executed
            display_info("The following SSH command will be executed:")
            display_info(" ".join(cmd))

            # Ask for confirmation
            confirmation = input("Do you want to proceed? (y/N): ").lower()
            if confirmation != "y":
                display_info("Connection cancelled by user")
                return False

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"SSH connection failed: {result.stderr}")
                return False

            # Store the connection
            self.connections[conn.socket_path] = conn
            display_success(f"SSH connection established to {conn.host}")

            # Automatically open a terminal
            self.open_terminal(conn.socket_path)

            return True
        except Exception as e:
            display_error(f"Error creating SSH connection: {str(e)}")
            return False

    def check_connection(self, socket_path: str) -> bool:
        """Check if the SSH connection is active"""
        try:
            if socket_path not in self.connections:
                return False

            cmd = ["ssh", "-S", socket_path, "-O", "check", "dummy"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            return result.returncode == 0
        except Exception:
            return False

    def create_tunnel(
        self,
        socket_path: str,
        local_port: int,
        remote_host: str,
        remote_port: int,
        reverse: bool = False,
    ) -> bool:
        """Create a new tunnel on an existing SSH connection"""
        try:
            if socket_path not in self.connections:
                display_error("SSH connection not found")
                return False

            conn = self.connections[socket_path]

            # Build the command
            if reverse:
                tunnel_args = f"-O forward -R {local_port}:{remote_host}:{remote_port}"
            else:
                tunnel_args = f"-O forward -L {local_port}:{remote_host}:{remote_port}"

            cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

            # Execute the command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to create tunnel: {result.stderr}")
                return False

            # Add the tunnel to the connection
            conn.add_tunnel(local_port, remote_host, remote_port, reverse)

            return True
        except Exception as e:
            display_error(f"Error creating tunnel: {str(e)}")
            return False

    def close_tunnel(self, socket_path: str, tunnel_id: str) -> bool:
        """Close a tunnel"""
        try:
            if socket_path not in self.connections:
                display_error("SSH connection not found")
                return False

            conn = self.connections[socket_path]

            # Find the tunnel
            tunnel = conn.get_tunnel(tunnel_id)
            if not tunnel:
                display_error(f"Tunnel {tunnel_id} not found")
                return False

            # Build the command
            if tunnel.type == "reverse":
                tunnel_args = (
                    f"-O cancel -R {tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"
                )
            else:
                tunnel_args = (
                    f"-O cancel -L {tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"
                )

            cmd = f"ssh -S {socket_path} {tunnel_args} dummy"

            # Execute the command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to close tunnel: {result.stderr}")
                return False

            # Remove the tunnel from the connection
            conn.remove_tunnel(tunnel_id)

            return True
        except Exception as e:
            display_error(f"Error closing tunnel: {str(e)}")
            return False

    def open_terminal(self, socket_path: str) -> None:
        """Open a terminal for an SSH connection using terminator"""
        if socket_path not in self.connections:
            return

        conn = self.connections[socket_path]
        try:
            # First verify the SSH connection is still active
            if not self.check_connection(socket_path):
                display_error("SSH connection is not active")
                return

            # Check if terminator is available
            try:
                terminator_path = subprocess.check_output(["which", "terminator"]).decode().strip()
            except subprocess.CalledProcessError:
                display_error("Terminator is required but not installed")
                display_info("Please install Terminator using your package manager")
                return

            # Build SSH command with explicit TTY allocation
            ssh_cmd = f"ssh -tt -S {socket_path} {conn.username}@{conn.host}"

            # Display the commands that will be executed
            display_info("Opening terminal with command:")
            display_info(f"{terminator_path} -e '{ssh_cmd}'")

            # Run terminator
            process = subprocess.Popen(
                [terminator_path, "-e", ssh_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Short wait to detect immediate failures
            time.sleep(0.5)

            if process.poll() is None:
                # Still running, which is good
                display_success(f"Terminal opened for {conn.host}")
            else:
                # Check if there was an error
                _, stderr = process.communicate()
                display_error(f"Terminal failed to start: {stderr.decode().strip()}")

        except Exception as e:
            display_error(f"Error opening terminal: {str(e)}")
            display_info("You can manually connect using:")
            display_info(f"ssh -S {socket_path} {conn.username}@{conn.host}")

    def close_connection(self, socket_path: str) -> bool:
        """Close an SSH connection"""
        try:
            if socket_path not in self.connections:
                return False

            # First close all tunnels
            conn = self.connections[socket_path]
            for tunnel in list(conn.tunnels):  # Use list to avoid modification during iteration
                self.close_tunnel(socket_path, tunnel.id)

            # Then close the master connection
            cmd = ["ssh", "-S", socket_path, "-O", "exit", "dummy"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to close connection: {result.stderr}")
                return False

            # Remove the connection from our dict
            del self.connections[socket_path]

            display_success("SSH connection closed")
            return True
        except Exception as e:
            display_error(f"Error closing connection: {str(e)}")
            return False

    def list_connections(self) -> Dict[str, SSHConnection]:
        """Return a copy of the connections dictionary"""
        return self.connections.copy()
