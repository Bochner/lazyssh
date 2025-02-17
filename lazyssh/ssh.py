import os
import subprocess
import pexpect
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
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
                "-S", conn.socket_path,
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "StrictHostKeyChecking=no",
                "-f", "-N"  # Background mode
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
            if confirmation != 'y':
                display_info("Connection cancelled by user")
                return False

            # Store the connection before attempting to connect
            self.connections[conn.socket_path] = conn

            # Prompt for password
            password = input("Enter SSH password (leave empty for key-based auth): ")

            if password:
                # Use pexpect for password authentication
                ssh_cmd = " ".join(cmd)
                child = pexpect.spawn(ssh_cmd, timeout=30, encoding='utf-8')
                
                # Wait for password prompt or early failure
                i = child.expect(['password:', 'Connection refused', 'Permission denied', pexpect.EOF, pexpect.TIMEOUT])
                
                if i == 0:  # Got password prompt
                    child.sendline(password)
                    # Now we wait for either success (EOF) or explicit failure
                    try:
                        child.expect(['Permission denied'], timeout=5)
                        display_error("Authentication failed: incorrect password")
                        del self.connections[conn.socket_path]
                        return False
                    except pexpect.TIMEOUT:
                        # No "Permission denied" message - this is good
                        time.sleep(2)  # Wait for connection to establish
                        if self.check_connection(conn.socket_path):
                            display_success("SSH connection established")
                            self.open_terminal(conn.socket_path)
                            return True
                    except pexpect.EOF:
                        # EOF can mean success for background connections
                        time.sleep(2)  # Wait for connection to establish
                        if self.check_connection(conn.socket_path):
                            display_success("SSH connection established")
                            self.open_terminal(conn.socket_path)
                            return True
                        else:
                            display_error("Connection failed to establish")
                            del self.connections[conn.socket_path]
                            return False
                elif i == 1:  # Connection refused
                    display_error("Connection refused by remote host")
                    del self.connections[conn.socket_path]
                    return False
                elif i == 2:  # Permission denied immediately
                    display_error("Permission denied by remote host")
                    del self.connections[conn.socket_path]
                    return False
                else:  # EOF or timeout without password prompt
                    display_error("Failed to establish connection")
                    del self.connections[conn.socket_path]
                    return False
            else:
                # Key-based authentication
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    time.sleep(2)
                    if self.check_connection(conn.socket_path):
                        display_success("SSH connection established")
                        self.open_terminal(conn.socket_path)
                        return True
                    else:
                        display_error("SSH control socket not ready")
                        del self.connections[conn.socket_path]
                        return False
                else:
                    display_error(f"SSH connection failed: {stderr.decode()}")
                    del self.connections[conn.socket_path]
                    return False

        except Exception as e:
            if conn.socket_path in self.connections:
                del self.connections[conn.socket_path]
            display_error(f"Error creating SSH connection: {str(e)}")
            return False

    def check_connection(self, socket_path: str) -> bool:
        """Check if the SSH connection is active and working."""
        if socket_path not in self.connections:
            return False
            
        conn = self.connections[socket_path]
        try:
            # First check if the socket file exists
            if not os.path.exists(socket_path):
                return False

            # Try to check the connection
            result = subprocess.run(
                ["ssh", "-S", socket_path, "-O", "check", f"{conn.username}@{conn.host}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )

            # If check succeeds, verify we can actually use the connection
            if result.returncode == 0:
                test_result = subprocess.run(
                    ["ssh", "-S", socket_path, conn.username + "@" + conn.host, "echo test"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=5
                )
                return test_result.returncode == 0
            return False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
        except Exception:
            return False

    def create_tunnel(self, socket_path: str, local_port: int, remote_host: str, remote_port: int, reverse: bool = False) -> bool:
        if socket_path not in self.connections:
            display_error(f"Connection not found: {os.path.basename(socket_path)}")
            return False

        conn = self.connections[socket_path]
        try:
            # Build command before execution to show the user
            cmd = ["ssh", "-S", socket_path, "-O", "forward"]
            if reverse:
                cmd.extend(["-R", f"{local_port}:{remote_host}:{remote_port}"])
            else:
                cmd.extend(["-L", f"{local_port}:{remote_host}:{remote_port}"])
            cmd.append(f"{conn.username}@{conn.host}")

            # Always show the command being executed
            display_info("\nExecuting tunnel creation command:")
            display_info(" ".join(cmd))

            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.stderr:
                display_error(f"SSH error: {process.stderr.strip()}")
            
            if process.returncode == 0:
                tunnel = conn.add_tunnel(local_port, remote_host, remote_port, reverse)
                tunnel_type = "reverse" if reverse else "forward"
                display_success(f"\nTunnel '{tunnel.id}' created successfully")
                display_info(f"Type: {tunnel_type}")
                display_info(f"Local port: {local_port}")
                display_info(f"Remote: {remote_host}:{remote_port}")
                return True
            return False

        except Exception as e:
            display_error(f"Error creating tunnel: {str(e)}")
            return False

    def close_tunnel(self, socket_path: str, tunnel_id: str) -> bool:
        if socket_path not in self.connections:
            display_error(f"Connection not found: {os.path.basename(socket_path)}")
            return False

        conn = self.connections[socket_path]
        tunnel = conn.get_tunnel(tunnel_id)
        if not tunnel:
            display_error(f"Tunnel {tunnel_id} not found")
            return False

        try:
            # Build command before execution to show the user
            cmd = ["ssh", "-S", socket_path, "-O", "cancel"]
            if tunnel.type == "reverse":
                cmd.extend(["-R", f"{tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"])
            else:
                cmd.extend(["-L", f"{tunnel.local_port}:{tunnel.remote_host}:{tunnel.remote_port}"])
            cmd.append(f"{conn.username}@{conn.host}")

            # Always show the command being executed
            display_info("\nExecuting tunnel destroy command:")
            display_info(" ".join(cmd))

            process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.stderr:
                display_error(f"SSH error: {process.stderr.strip()}")
            
            if process.returncode == 0:
                conn.remove_tunnel(tunnel_id)
                display_success(f"\nTunnel '{tunnel_id}' destroyed successfully")
                return True
            return False

        except Exception as e:
            display_error(f"Error destroying tunnel: {str(e)}")
            return False

    def open_terminal(self, socket_path: str) -> None:
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
                terminator_path = ""

            if not terminator_path:
                display_error("Terminator is required but not installed")
                display_info("Please install Terminator using your package manager:")
                display_info("Fedora/RHEL : sudo dnf install terminator")
                display_info("Ubuntu/Debian: sudo apt install terminator")
                display_info("Arch Linux  : sudo pacman -S terminator")
                return

            # Build SSH command with explicit TTY allocation
            ssh_cmd = f"ssh -tt -S {socket_path} {conn.username}@{conn.host}"

            # Display the commands that will be executed
            display_info("Opening terminal with command:")
            display_info(f"{terminator_path} -e '{ssh_cmd}'")

            # Run terminator with simplified process handling
            try:
                process = subprocess.Popen(
                    [terminator_path, "-e", ssh_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Short wait to detect immediate failures
                time.sleep(0.5)
                
                if process.poll() is None:
                    # Still running, which is good
                    display_success(f"Terminal opened for {conn.host}")
                else:
                    # Check if there was an error
                    _, stderr = process.communicate()
                    if stderr and stderr.strip():
                        display_error(f"Terminal failed to start: {stderr.decode().strip()}")
                    else:
                        # No error output usually means terminator detached successfully
                        display_success(f"Terminal opened for {conn.host}")
                    
            except Exception as e:
                display_error(f"Failed to start terminal: {str(e)}")
                display_info("You can manually connect using:")
                display_info(ssh_cmd)
                
        except Exception as e:
            display_error(f"Error opening terminal: {str(e)}")
            display_info("You can manually connect using:")
            display_info(f"ssh -S {socket_path} {conn.username}@{conn.host}")

    def close_connection(self, socket_path: str) -> bool:
        if socket_path not in self.connections:
            return False

        try:
            cmd = ["ssh", "-S", socket_path, "-O", "exit", "localhost"]
            process = subprocess.run(cmd, capture_output=True, text=True)
            if process.returncode == 0:
                del self.connections[socket_path]
                return True
            return False

        except Exception as e:
            console.print(f"[red]Error closing connection:[/red] {str(e)}")
            return False

    def list_connections(self) -> Dict[str, SSHConnection]:
        return self.connections