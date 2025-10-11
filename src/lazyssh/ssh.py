import os
import shutil
import subprocess
import time
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from .config import get_terminal_method
from .logging_module import SSH_LOGGER, log_ssh_connection, log_tunnel_creation
from .models import SSHConnection
from .ui import display_error, display_info, display_success, display_warning

console = Console()


class SSHManager:
    def __init__(self) -> None:
        """Initialize the SSH manager"""
        self.connections: dict[str, SSHConnection] = {}

        # Set the base path for control sockets
        self.control_path_base = "/tmp/"
        
        # Initialize terminal method from configuration
        self.terminal_method = get_terminal_method()

        # Log initialization
        if SSH_LOGGER:
            SSH_LOGGER.debug(f"SSHManager initialized with terminal method: {self.terminal_method}")

        # We don't need to create or chmod the /tmp directory as it already exists
        # with the appropriate permissions

    def create_connection(self, conn: SSHConnection) -> bool:
        try:
            # Ensure directories exist using pathlib
            connection_dir = Path(conn.connection_dir)
            downloads_dir = Path(conn.downloads_dir)

            if not connection_dir.exists():
                connection_dir.mkdir(parents=True, exist_ok=True)
                connection_dir.chmod(0o700)
                if SSH_LOGGER:
                    SSH_LOGGER.debug(f"Created connection directory: {connection_dir}")

            if not downloads_dir.exists():
                downloads_dir.mkdir(parents=True, exist_ok=True)
                downloads_dir.chmod(0o700)
                if SSH_LOGGER:
                    SSH_LOGGER.debug(f"Created downloads directory: {downloads_dir}")

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
                cmd.extend(["-i", str(Path(conn.identity_file).expanduser())])

            cmd.append(f"{conn.username}@{conn.host}")

            # Display the command that will be executed
            display_info("The following SSH command will be executed:")
            display_info(" ".join(cmd))
            if SSH_LOGGER:
                SSH_LOGGER.debug(f"SSH command: {' '.join(cmd)}")

            # Ask for confirmation using Rich's Confirm.ask for a color-coded prompt
            if not Confirm.ask("Do you want to proceed?"):
                display_info("Connection cancelled by user")
                if SSH_LOGGER:
                    SSH_LOGGER.info("Connection cancelled by user")
                return False

            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"SSH connection failed: {result.stderr}")
                log_ssh_connection(
                    conn.host,
                    conn.port,
                    conn.username,
                    conn.socket_path,
                    conn.dynamic_port,
                    conn.identity_file,
                    conn.shell,
                    success=False,
                )
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"SSH connection error: {result.stderr}")
                return False

            # Store the connection
            self.connections[conn.socket_path] = conn
            display_success(f"SSH connection established to {conn.host}")

            # Log connection success
            log_ssh_connection(
                conn.host,
                conn.port,
                conn.username,
                conn.socket_path,
                conn.dynamic_port,
                conn.identity_file,
                conn.shell,
            )

            # Wait a moment for the connection to be fully established
            time.sleep(0.5)

            # Automatically open a terminal unless no_term is True
            if not conn.no_term:
                self.open_terminal(conn.socket_path)

            return True
        except Exception as e:
            display_error(f"Error creating SSH connection: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error creating SSH connection: {str(e)}")
            return False

    def check_connection(self, socket_path: str) -> bool:
        """Check if an SSH connection is active via control socket"""
        try:
            # Use pathlib to check if socket file exists
            socket_file = Path(socket_path)
            if not socket_file.exists():
                if SSH_LOGGER:
                    SSH_LOGGER.debug(f"Socket file not found: {socket_path}")
                return False

            # Check the connection
            cmd = ["ssh", "-S", socket_path, "-O", "check", "dummy"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0

            if success:
                if SSH_LOGGER:
                    SSH_LOGGER.debug(f"Connection check successful: {socket_path}")
            else:
                if SSH_LOGGER:
                    SSH_LOGGER.debug(f"Connection check failed: {socket_path}")

            return success
        except Exception as e:
            display_error(f"Error checking connection: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Error checking connection: {str(e)}")
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
                if SSH_LOGGER:
                    SSH_LOGGER.error(
                        f"Tunnel creation failed: connection not found for {socket_path}"
                    )
                return False

            conn = self.connections[socket_path]

            # Build the command
            if reverse:
                tunnel_args = f"-O forward -R {local_port}:{remote_host}:{remote_port}"
            else:
                tunnel_args = f"-O forward -L {local_port}:{remote_host}:{remote_port}"

            cmd = f"ssh -S {socket_path} {tunnel_args} dummy"
            if SSH_LOGGER:
                SSH_LOGGER.debug(f"Tunnel command: {cmd}")

            # Execute the command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to create tunnel: {result.stderr}")
                log_tunnel_creation(
                    socket_path, local_port, remote_host, remote_port, reverse, success=False
                )
                return False

            # Add the tunnel to the connection
            conn.add_tunnel(local_port, remote_host, remote_port, reverse)

            # Log tunnel creation
            log_tunnel_creation(socket_path, local_port, remote_host, remote_port, reverse)

            return True
        except Exception as e:
            display_error(f"Error creating tunnel: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error creating tunnel: {str(e)}")
            return False

    def close_tunnel(self, socket_path: str, tunnel_id: str) -> bool:
        """Close a tunnel"""
        try:
            if socket_path not in self.connections:
                display_error("SSH connection not found")
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"Close tunnel failed: connection not found for {socket_path}")
                return False

            conn = self.connections[socket_path]

            # Find the tunnel
            tunnel = conn.get_tunnel(tunnel_id)
            if not tunnel:
                display_error(f"Tunnel {tunnel_id} not found")
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"Tunnel {tunnel_id} not found for {socket_path}")
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
            if SSH_LOGGER:
                SSH_LOGGER.debug(f"Close tunnel command: {cmd}")

            # Execute the command
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to close tunnel: {result.stderr}")
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"Failed to close tunnel: {result.stderr}")
                return False

            # Remove the tunnel from the connection
            conn.remove_tunnel(tunnel_id)
            if SSH_LOGGER:
                SSH_LOGGER.info(f"Tunnel {tunnel_id} closed for {socket_path}")

            return True
        except Exception as e:
            display_error(f"Error closing tunnel: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error closing tunnel: {str(e)}")
            return False

    def open_terminal_native(self, socket_path: str) -> bool:
        """
        Open a terminal for an SSH connection using native Python subprocess.
        This runs SSH as a subprocess, allowing LazySSH to continue running.
        
        Returns:
            True if terminal session completed successfully, False otherwise.
        """
        if socket_path not in self.connections:
            display_error(f"SSH connection not found for socket: {socket_path}")
            if SSH_LOGGER:
                SSH_LOGGER.error(f"Terminal open failed: connection not found for {socket_path}")
            return False

        conn = self.connections[socket_path]
        try:
            # First verify the SSH connection is still active
            if not self.check_connection(socket_path):
                display_error("SSH connection is not active")
                if SSH_LOGGER:
                    SSH_LOGGER.error(
                        f"Cannot open terminal: connection not active for {socket_path}"
                    )
                return False

            # Build SSH command with explicit TTY allocation
            ssh_args = ["ssh", "-tt", "-S", socket_path, f"{conn.username}@{conn.host}"]

            # Add specified shell if provided
            if conn.shell:
                ssh_args.append(conn.shell)

            # Display the command that will be executed
            display_info("Opening terminal (native):")
            display_info(" ".join(ssh_args))
            if SSH_LOGGER:
                SSH_LOGGER.info(
                    f"Opening native terminal for {conn.username}@{conn.host} using socket {socket_path}"
                )

            # Run SSH as subprocess and wait for it to complete
            # User can exit with 'exit' or Ctrl+D to return to LazySSH
            result = subprocess.run(ssh_args)

            if result.returncode == 0:
                display_success("Terminal session ended")
                if SSH_LOGGER:
                    SSH_LOGGER.info(f"Native terminal session completed for {socket_path}")
                return True
            else:
                display_warning(f"Terminal session ended with exit code {result.returncode}")
                if SSH_LOGGER:
                    SSH_LOGGER.warning(
                        f"Native terminal session ended with exit code {result.returncode} for {socket_path}"
                    )
                return False

        except Exception as e:
            display_error(f"Error opening native terminal: {str(e)}")
            display_info("You can manually connect using:")
            display_info(f"ssh -S {socket_path} {conn.username}@{conn.host}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error opening native terminal: {str(e)}")
            return False

    def open_terminal_terminator(self, socket_path: str) -> bool:
        """
        Open a terminal for an SSH connection using Terminator.
        
        Returns:
            True if terminal was opened successfully, False otherwise.
        """
        if socket_path not in self.connections:
            display_error(f"SSH connection not found for socket: {socket_path}")
            if SSH_LOGGER:
                SSH_LOGGER.error(f"Terminal open failed: connection not found for {socket_path}")
            return False

        conn = self.connections[socket_path]
        try:
            # First verify the SSH connection is still active
            if not self.check_connection(socket_path):
                display_error("SSH connection is not active")
                if SSH_LOGGER:
                    SSH_LOGGER.error(
                        f"Cannot open terminal: connection not active for {socket_path}"
                    )
                return False

            # Check if terminator is available
            terminator_path = shutil.which("terminator")
            if not terminator_path:
                if SSH_LOGGER:
                    SSH_LOGGER.debug("Terminator not found in PATH")
                return False

            # Build SSH command with explicit TTY allocation
            ssh_cmd = f"ssh -tt -S {socket_path} {conn.username}@{conn.host}"

            # Add specified shell if provided
            if conn.shell:
                ssh_cmd += f" {conn.shell}"

            # Display the commands that will be executed
            display_info("Opening terminal (terminator):")
            display_info(f"{terminator_path} -e '{ssh_cmd}'")
            if SSH_LOGGER:
                SSH_LOGGER.info(
                    f"Opening Terminator terminal for {conn.username}@{conn.host} using socket {socket_path}"
                )

            # Run terminator
            process = subprocess.Popen(
                [terminator_path, "-e", ssh_cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Short wait to detect immediate failures
            time.sleep(0.5)

            if process.poll() is None:
                # Still running, which is good
                display_success(f"Terminal opened for {conn.host}")
                return True
            else:
                # Check if there was an error
                _, stderr = process.communicate()
                display_error(f"Terminator failed to start: {stderr.decode().strip()}")
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"Terminator failed to start: {stderr.decode().strip()}")
                return False

        except Exception as e:
            display_error(f"Error opening Terminator terminal: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error opening Terminator terminal: {str(e)}")
            return False

    def open_terminal(self, socket_path: str) -> bool:
        """
        Open a terminal for an SSH connection.
        
        Automatically selects the appropriate terminal method based on configuration
        and availability. Methods are tried in order:
        - If method is 'terminator': try Terminator only
        - If method is 'native': use native terminal only
        - If method is 'auto' (default): try Terminator, fallback to native
        
        Returns:
            True if terminal was opened successfully, False otherwise.
        """
        if socket_path not in self.connections:
            display_error(f"SSH connection not found for socket: {socket_path}")
            if SSH_LOGGER:
                SSH_LOGGER.error(f"Terminal open failed: connection not found for {socket_path}")
            return False

        conn = self.connections[socket_path]
        
        # First verify the SSH connection is still active
        if not self.check_connection(socket_path):
            display_error("SSH connection is not active")
            if SSH_LOGGER:
                SSH_LOGGER.error(
                    f"Cannot open terminal: connection not active for {socket_path}"
                )
            return False

        # Use the current terminal method from instance state
        terminal_method = self.terminal_method
        
        if SSH_LOGGER:
            SSH_LOGGER.debug(f"Terminal method configured: {terminal_method}")

        try:
            if terminal_method == "terminator":
                # User explicitly requested Terminator
                if not self.open_terminal_terminator(socket_path):
                    display_error("Terminator is not available")
                    display_info("Please install Terminator or set LAZYSSH_TERMINAL_METHOD=native")
                    return False
                return True
            elif terminal_method == "native":
                # User explicitly requested native terminal
                return self.open_terminal_native(socket_path)
            else:  # "auto"
                # Try Terminator first, fallback to native
                if shutil.which("terminator"):
                    if SSH_LOGGER:
                        SSH_LOGGER.debug("Attempting to use Terminator (auto mode)")
                    if not self.open_terminal_terminator(socket_path):
                        # Terminator failed, fallback to native
                        if SSH_LOGGER:
                            SSH_LOGGER.debug("Terminator failed, falling back to native terminal")
                        display_warning("Terminator failed, falling back to native terminal")
                        return self.open_terminal_native(socket_path)
                    return True
                else:
                    # Terminator not available, use native
                    if SSH_LOGGER:
                        SSH_LOGGER.debug("Terminator not available, using native terminal (auto mode)")
                    return self.open_terminal_native(socket_path)

        except Exception as e:
            display_error(f"Error opening terminal: {str(e)}")
            display_info("You can manually connect using:")
            display_info(f"ssh -S {socket_path} {conn.username}@{conn.host}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Unexpected error opening terminal: {str(e)}")
            return False

    def close_connection(self, socket_path: str) -> bool:
        """Close an SSH connection"""
        try:
            if socket_path not in self.connections:
                display_error("SSH connection not found")
                if SSH_LOGGER:
                    SSH_LOGGER.error(f"Close connection failed: socket not found: {socket_path}")
                return False

            # First close all tunnels
            conn = self.connections[socket_path]
            for tunnel in list(conn.tunnels):  # Use list to avoid modification during iteration
                self.close_tunnel(socket_path, tunnel.id)

            # Check if the socket file exists before trying to close it
            socket_file = Path(socket_path)
            if not socket_file.exists():
                # Don't display the message to the user, it's not an actual error
                if SSH_LOGGER:
                    SSH_LOGGER.info(
                        f"Socket file {socket_path} no longer exists, cleaning up reference"
                    )
                del self.connections[socket_path]
                return True

            # Then close the master connection
            cmd = ["ssh", "-S", socket_path, "-O", "exit", "dummy"]
            if SSH_LOGGER:
                SSH_LOGGER.debug(f"Close connection command: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                # Don't show warning to user if the error is just that the socket doesn't exist
                # This is expected during cleanup and not an actual error
                if "No such file or directory" in result.stderr:
                    if SSH_LOGGER:
                        SSH_LOGGER.info(f"Socket already removed: {result.stderr}")
                else:
                    display_warning(f"Issue closing connection: {result.stderr}")
                    if SSH_LOGGER:
                        SSH_LOGGER.warning(f"Issue closing connection: {result.stderr}")
                # Even if there was an error, remove it from our tracking to avoid repeated errors
                del self.connections[socket_path]
                return True  # Return success anyway so we continue closing other connections

            # Remove the connection from our dict
            del self.connections[socket_path]
            if SSH_LOGGER:
                SSH_LOGGER.info(f"Connection closed: {socket_path}")

            display_success("SSH connection closed")
            return True
        except Exception as e:
            display_warning(f"Error during connection cleanup: {str(e)}")
            if SSH_LOGGER:
                SSH_LOGGER.exception(f"Error during connection cleanup: {str(e)}")
            # Still try to clean up the reference even if there was an error
            if socket_path in self.connections:
                del self.connections[socket_path]
            return True  # Return success so we continue closing other connections

    def list_connections(self) -> dict[str, SSHConnection]:
        """Return a copy of the connections dictionary"""
        # Log counts of active connections
        if SSH_LOGGER:
            SSH_LOGGER.debug(f"Listing {len(self.connections)} connections")
        return self.connections.copy()
    
    def set_terminal_method(self, method: str) -> bool:
        """
        Change the terminal method at runtime.
        
        Args:
            method: Terminal method to set ('auto', 'native', or 'terminator')
        
        Returns:
            True if method was set successfully, False if invalid method
        """
        from .config import TerminalMethod
        
        if method not in ["auto", "native", "terminator"]:
            display_error(f"Invalid terminal method: {method}")
            display_info("Valid methods: auto, native, terminator")
            return False
        
        self.terminal_method = method  # type: ignore
        display_success(f"Terminal method set to: {method}")
        
        if SSH_LOGGER:
            SSH_LOGGER.info(f"Terminal method changed to: {method}")
        
        return True
    
    def get_current_terminal_method(self) -> str:
        """
        Get the current terminal method.
        
        Returns:
            Current terminal method ('auto', 'native', or 'terminator')
        """
        return self.terminal_method
