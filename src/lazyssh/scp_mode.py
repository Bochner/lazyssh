"""SCP mode interface for LazySSH using prompt_toolkit"""

import os
import shlex
import subprocess
from typing import Any, Iterable, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

from .models import SSHConnection
from .ssh import SSHManager
from .ui import display_error, display_info, display_success


class SCPModeCompleter(Completer):
    """Completer for prompt_toolkit with SCP mode commands"""

    def __init__(self, scp_mode):
        self.scp_mode = scp_mode

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text = document.text
        word_before_cursor = document.get_word_before_cursor()

        # Split the input into words
        try:
            words = shlex.split(text[: document.cursor_position])
        except ValueError:
            words = text[: document.cursor_position].split()

        if not words or (len(words) == 1 and not text.endswith(" ")):
            # Show base commands if at start
            for cmd in self.scp_mode.commands:
                if not word_before_cursor or cmd.startswith(word_before_cursor):
                    yield Completion(cmd, start_position=-len(word_before_cursor))
            return

        command = words[0].lower()

        # Add command-specific completions based on first word
        if command in ["get", "ls", "mget"] and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # If we have an active connection, try to complete remote files
                if self.scp_mode.conn and self.scp_mode.socket_path:
                    try:
                        # Get partial path from what user typed so far
                        partial_path = words[1] if len(words) > 1 else ""
                        base_dir = (
                            os.path.dirname(partial_path)
                            if partial_path
                            else self.scp_mode.current_remote_dir
                        )
                        if not base_dir:
                            base_dir = self.scp_mode.current_remote_dir

                        # Get files in the directory
                        result = self.scp_mode._execute_ssh_command(f"ls -a {base_dir}")
                        if result and result.returncode == 0:
                            file_list = result.stdout.strip().split("\n")
                            file_list = [f for f in file_list if f and f not in [".", ".."]]

                            for f in file_list:
                                if not word_before_cursor or f.startswith(word_before_cursor):
                                    yield Completion(f, start_position=-len(word_before_cursor))
                    except Exception:
                        # Silently fail for completions
                        pass

        elif command == "put" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete local files
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[1] if len(words) > 1 else ""
                    base_dir = (
                        os.path.dirname(partial_path)
                        if partial_path
                        else self.scp_mode.local_download_dir
                    )
                    if not base_dir:
                        base_dir = self.scp_mode.local_download_dir

                    # Get filename part for matching
                    filename_part = os.path.basename(partial_path) if partial_path else ""

                    # List files in the local directory
                    for f in os.listdir(base_dir or "."):
                        if not filename_part or f.startswith(filename_part):
                            full_path = os.path.join(base_dir, f) if base_dir else f
                            yield Completion(full_path, start_position=-len(partial_path))
                except Exception:
                    # Silently fail for completions
                    pass

        elif command == "cd" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete remote directories
                if self.scp_mode.conn and self.scp_mode.socket_path:
                    try:
                        # Get partial path from what user typed so far
                        partial_path = words[1] if len(words) > 1 else ""
                        base_dir = (
                            os.path.dirname(partial_path)
                            if partial_path
                            else self.scp_mode.current_remote_dir
                        )
                        if not base_dir:
                            base_dir = self.scp_mode.current_remote_dir

                        # Get directories in the base directory
                        result = self.scp_mode._execute_ssh_command(
                            f"find {base_dir} -maxdepth 1 -type d -printf '%f\\n'"
                        )
                        if result and result.returncode == 0:
                            dir_list = result.stdout.strip().split("\n")
                            dir_list = [d for d in dir_list if d and d not in [".", ".."]]

                            for d in dir_list:
                                if not word_before_cursor or d.startswith(word_before_cursor):
                                    yield Completion(d, start_position=-len(word_before_cursor))
                    except Exception:
                        # Silently fail for completions
                        pass

        elif command == "local" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete local directories
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[1] if len(words) > 1 else ""
                    base_dir = os.path.dirname(partial_path) if partial_path else "."

                    # Get filename part for matching
                    dirname_part = os.path.basename(partial_path) if partial_path else ""

                    # List directories in the local directory
                    for d in os.listdir(base_dir or "."):
                        if (not dirname_part or d.startswith(dirname_part)) and os.path.isdir(
                            os.path.join(base_dir, d)
                        ):
                            full_path = os.path.join(base_dir, d) if base_dir else d
                            yield Completion(full_path, start_position=-len(partial_path))
                except Exception:
                    # Silently fail for completions
                    pass
        elif command == "lls" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete local directories
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[1] if len(words) > 1 else ""

                    # Determine the base directory
                    if os.path.isabs(partial_path):
                        base_dir = os.path.dirname(partial_path) or "/"
                    else:
                        base_dir = (
                            os.path.dirname(
                                os.path.join(self.scp_mode.local_download_dir, partial_path)
                            )
                            or self.scp_mode.local_download_dir
                        )

                    # Get filename part for matching
                    filename_part = os.path.basename(partial_path) if partial_path else ""

                    # List files and directories in the local directory
                    for item in os.listdir(base_dir):
                        full_path = os.path.join(base_dir, item)

                        # Only suggest if it matches the partial path
                        if not filename_part or item.startswith(filename_part):
                            # If it's a directory, add a trailing slash
                            if os.path.isdir(full_path):
                                completion = os.path.join(base_dir, item) + "/"
                            else:
                                completion = os.path.join(base_dir, item)

                            # If the base directory is the download directory, make path relative
                            if base_dir == self.scp_mode.local_download_dir and not os.path.isabs(
                                partial_path
                            ):
                                completion = os.path.relpath(
                                    completion, self.scp_mode.local_download_dir
                                )

                            yield Completion(completion, start_position=-len(partial_path))
                except Exception:
                    # Silently fail for completions
                    pass


class SCPMode:
    """SCP mode for file transfers through established SSH connections"""

    def __init__(self, ssh_manager: SSHManager, selected_connection: Optional[str] = None):
        self.ssh_manager = ssh_manager
        self.selected_connection: Optional[str] = selected_connection
        self.current_remote_dir = "~"  # Default to home directory
        self.local_download_dir = (
            os.getcwd()
        )  # Default to current working directory (will be updated after connection)
        self.socket_path: Optional[str] = None
        self.conn: Optional[SSHConnection] = None  # Initialize as None until connect() is called

        # Initialize commands
        self.commands = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "put": self.cmd_put,
            "get": self.cmd_get,
            "ls": self.cmd_ls,
            "lls": self.cmd_lls,  # New command for local directory listing
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "mget": self.cmd_mget,
            "local": self.cmd_local,
        }

        # Initialize prompt_toolkit components
        self.completer = SCPModeCompleter(self)
        self.session: PromptSession = PromptSession()
        self.style = Style.from_dict(
            {
                "prompt": "ansigreen bold",
                "path": "ansiyellow",
                "local": "ansiblue",
            }
        )

    def connect(self) -> bool:
        """Verify the SSH connection is active via control socket"""
        if not self.selected_connection:
            display_error("No SSH connection selected")
            return False

        # The selected_connection is now the socket name directly
        conn_name = self.selected_connection
        socket_path = f"/tmp/{conn_name}"

        # Find connection by socket path
        if socket_path in self.ssh_manager.connections:
            self.socket_path = socket_path
            self.conn = self.ssh_manager.connections[socket_path]
        else:
            # If we get here, the connection wasn't found
            display_error(f"Connection '{conn_name}' not found")
            return False

        # Verify the connection is active
        if not self.ssh_manager.check_connection(self.socket_path):
            display_error(f"SSH connection '{self.selected_connection}' is not active")
            display_info("Try reconnecting or creating a new connection")
            return False

        # Set the local download directory to the connection's downloads directory
        self.local_download_dir = self.conn.downloads_dir

        # Get initial remote directory
        try:
            cmd = [
                "ssh",
                "-o",
                f"ControlPath={self.socket_path}",
                f"{self.conn.username}@{self.conn.host}",
                "pwd",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Failed to get remote directory: {result.stderr}")
                return False

            self.current_remote_dir = result.stdout.strip()
            display_success(f"Connected to {self.conn.username}@{self.conn.host}")
            return True
        except Exception as e:
            display_error(f"Connection error: {str(e)}")
            return False

    def _execute_ssh_command(self, remote_command) -> Optional[Any]:
        """Execute a command on the SSH server and return the result"""
        if not self.socket_path:
            display_error("Not connected to an SSH server")
            return None

        # Build the SSH command using the control socket
        command = [
            "ssh",
            "-S",
            self.socket_path,
            "-l",
            self.conn.username if self.conn else "unknown",
            self.conn.host if self.conn else "unknown",
            remote_command,
        ]

        # Execute the command and capture the output
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            return result
        except Exception as e:
            display_error(f"Failed to execute command: {e}")
            return None

    def get_prompt_text(self) -> HTML:
        """Get the prompt text with HTML formatting"""
        conn_name = self.selected_connection or "none"
        return HTML(
            f"<prompt>scp {conn_name}</prompt>:<path>{self.current_remote_dir}</path>"
            f" [<local>{self.local_download_dir}</local>]> "
        )

    def run(self) -> None:
        """Run the SCP mode interface"""
        # If no connection is selected, prompt for selection
        if not self.selected_connection:
            if not self._select_connection():
                return

        # Connect to the selected SSH session
        if not self.connect():
            return

        while True:
            try:
                user_input = self.session.prompt(
                    self.get_prompt_text(),
                    completer=self.completer,
                    style=self.style,
                    complete_while_typing=True,
                )

                # Split the input into command and args
                args = shlex.split(user_input)
                if not args:
                    continue

                cmd = args[0].lower()
                if cmd in self.commands:
                    result = self.commands[cmd](args[1:])
                    if cmd == "exit" and result:
                        break
                else:
                    display_error(f"Unknown command: {cmd}")
                    self.cmd_help([])
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                display_error(f"Error: {str(e)}")

    def _select_connection(self) -> bool:
        """Prompt user to select an SSH connection"""
        connections = []
        connection_map = {}

        # Build a map of connection names to actual connections
        for socket_path, conn in self.ssh_manager.connections.items():
            conn_name = os.path.basename(socket_path)
            connections.append(conn_name)
            connection_map[conn_name] = conn

        if not connections:
            display_error("No active SSH connections available")
            display_info("Create an SSH connection first using 'lazyssh' command")
            return False

        display_info("Select an SSH connection for SCP mode:")
        for i, name in enumerate(connections, 1):
            conn = connection_map[name]
            display_info(f"{i}. {name} ({conn.username}@{conn.host})")

        while True:
            try:
                choice = input("Enter selection (number or name): ")
                if choice.isdigit() and 1 <= int(choice) <= len(connections):
                    self.selected_connection = connections[int(choice) - 1]
                    return True
                elif choice in connections:
                    self.selected_connection = choice
                    return True
                else:
                    display_error("Invalid selection")
            except (KeyboardInterrupt, EOFError):
                return False

    def _resolve_remote_path(self, path: str) -> str:
        """Resolve a remote path relative to the current directory"""
        if not path:
            return self.current_remote_dir
        if path.startswith("/"):
            return path
        if path.startswith("~"):
            # Execute command to expand ~ on the remote server
            result = self._execute_ssh_command(f"echo {path}")
            if result and result.returncode == 0:
                expanded_path: str = result.stdout.strip()
                return expanded_path
            return path

        # Join with current directory
        return os.path.normpath(os.path.join(self.current_remote_dir, path))

    def _resolve_local_path(self, path: str) -> str:
        """Resolve a local path relative to the local download directory"""
        if not path:
            return self.local_download_dir
        if os.path.isabs(path):
            return path

        # Join with local download directory
        return os.path.normpath(os.path.join(self.local_download_dir, path))

    def _get_scp_command(self, source: str, destination: str) -> List[str]:
        """Get the SCP command using the control socket"""
        return ["scp", "-o", f"ControlPath={self.socket_path}", source, destination]

    def cmd_put(self, args: List[str]) -> bool:
        """Upload files to the remote server"""
        if not args:
            display_error("Usage: put <local_file> [remote_path]")
            return False

        if not self.conn:
            display_error("Not connected to an SSH server")
            return False

        local_file = self._resolve_local_path(args[0])

        if len(args) == 2:
            remote_file = self._resolve_remote_path(args[1])
        else:
            # Use the same filename in the current remote directory
            filename = os.path.basename(local_file)
            remote_file = os.path.join(self.current_remote_dir, filename)

        try:
            if not os.path.exists(local_file):
                display_error(f"Local file not found: {local_file}")
                return False

            display_info(f"Uploading {local_file} to {remote_file}...")

            # Get the SCP command
            remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
            cmd = self._get_scp_command(local_file, remote_path)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Upload failed: {result.stderr}")
                return False

            display_success(f"Successfully uploaded {local_file} to {remote_file}")
            return True
        except Exception as e:
            display_error(f"Upload failed: {str(e)}")
            return False

    def cmd_get(self, args: List[str]) -> bool:
        """Download files from the remote server"""
        if not args:
            display_error("Usage: get <remote_file> [local_path]")
            return False

        if not self.conn:
            display_error("Not connected to an SSH server")
            return False

        remote_file = self._resolve_remote_path(args[0])

        if len(args) == 2:
            local_file = self._resolve_local_path(args[1])
        else:
            # Use the same filename in the local download directory
            filename = os.path.basename(remote_file)
            local_file = os.path.join(self.local_download_dir, filename)

        try:
            # First check if the remote file exists
            check_cmd = self._execute_ssh_command(f"test -f {remote_file} && echo 'exists'")
            if not check_cmd or check_cmd.returncode != 0 or "exists" not in check_cmd.stdout:
                display_error(f"Remote file not found: {remote_file}")
                return False

            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_file)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
                # Ensure proper permissions
                os.chmod(local_dir, 0o755)

            display_info(f"Downloading {remote_file} to {local_file}...")

            # Get the SCP command
            remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
            cmd = self._get_scp_command(remote_path, local_file)

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                display_error(f"Download failed: {result.stderr}")
                return False

            display_success(f"Successfully downloaded {remote_file} to {local_file}")
            return True
        except Exception as e:
            display_error(f"Download failed: {str(e)}")
            return False

    def cmd_ls(self, args: List[str]) -> bool:
        """List contents of a remote directory"""
        path = self.current_remote_dir
        if args:
            path = self._resolve_remote_path(args[0])

        try:
            # Use ls -lah command via SSH for human-readable sizes
            result = self._execute_ssh_command(f"ls -lah {path}")

            if not result or result.returncode != 0:
                display_error(
                    f"Error listing directory: {result.stderr if result else 'Unknown error'}"
                )
                return False

            # Format and display the output
            output = result.stdout.strip()
            if not output:
                display_info(f"Directory {path} is empty")
                return True

            display_info(f"Contents of {path}:")

            # Filter out the "total X" line that shows disk block usage
            lines = output.split("\n")
            filtered_lines = [line for line in lines if not line.startswith("total ")]

            for line in filtered_lines:
                display_info(line)

            return True
        except Exception as e:
            display_error(f"Error listing directory: {str(e)}")
            return False

    def cmd_cd(self, args: List[str]) -> bool:
        """Change remote directory"""
        if not args:
            display_error("Usage: cd <remote_path>")
            return False

        target_dir = self._resolve_remote_path(args[0])

        try:
            # Check if directory exists and is accessible
            result = self._execute_ssh_command(f"cd {target_dir} && pwd")

            if not result or result.returncode != 0:
                display_error(
                    f"Failed to change directory: {result.stderr if result else 'Directory may not exist'}"
                )
                return False

            # Update current directory
            self.current_remote_dir = result.stdout.strip()
            display_success(f"Changed to directory: {self.current_remote_dir}")
            return True
        except Exception as e:
            display_error(f"Failed to change directory: {str(e)}")
            return False

    def cmd_pwd(self, args: List[str]) -> bool:
        """Print current remote directory"""
        display_info(f"Current remote directory: {self.current_remote_dir}")
        return True

    def cmd_mget(self, args: List[str]) -> bool:
        """Download multiple files from the remote server using wildcards"""
        if not args:
            display_error("Usage: mget <pattern>")
            return False

        if not self.conn:
            display_error("Not connected to an SSH server")
            return False

        pattern = args[0]

        try:
            # Find files matching pattern
            result = self._execute_ssh_command(
                f"find {self.current_remote_dir} -maxdepth 1 -type f -name '{pattern}' -printf '%f\\n'"
            )

            if not result or result.returncode != 0:
                display_error(
                    f"Error finding files: {result.stderr if result else 'Unknown error'}"
                )
                return False

            matched_files = [f for f in result.stdout.strip().split("\n") if f]

            if not matched_files:
                display_error(f"No files match pattern: {pattern}")
                return False

            # Calculate total size of all files
            total_size = 0
            file_sizes = {}

            display_info(f"Found {len(matched_files)} matching files:")
            for filename in matched_files:
                # Get file size
                size_result = self._execute_ssh_command(
                    f"stat -c %s {self.current_remote_dir}/{filename}"
                )
                if size_result and size_result.returncode == 0:
                    try:
                        size = int(size_result.stdout.strip())
                        file_sizes[filename] = size
                        total_size += size

                        # Format size in human-readable format
                        human_size = self._format_file_size(size)
                        display_info(f"  {filename} ({human_size})")
                    except ValueError:
                        display_info(f"  {filename} (unknown size)")
                else:
                    display_info(f"  {filename} (unknown size)")

            # Format total size in human-readable format
            human_total = self._format_file_size(total_size)
            display_info(f"Total download size: {human_total}")

            # Confirm download
            confirmation = input(
                f"Download {len(matched_files)} files to {self.local_download_dir}? (y/N): "
            )
            if confirmation.lower() != "y":
                display_info("Download cancelled")
                return False

            # Ensure download directory exists with proper permissions
            if not os.path.exists(self.local_download_dir):
                os.makedirs(self.local_download_dir, exist_ok=True)
                os.chmod(self.local_download_dir, 0o755)

            # Download files
            success_count = 0
            for filename in matched_files:
                remote_file = os.path.join(self.current_remote_dir, filename)
                local_file = os.path.join(self.local_download_dir, filename)

                try:
                    display_info(f"Downloading {filename}...")

                    # Get the SCP command
                    remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
                    cmd = self._get_scp_command(remote_path, local_file)

                    result = subprocess.run(cmd, capture_output=True, text=True)

                    if result.returncode != 0:
                        display_error(f"Failed to download {filename}: {result.stderr}")
                    else:
                        success_count += 1
                except Exception as e:
                    display_error(f"Failed to download {filename}: {str(e)}")

            if success_count > 0:
                display_success(
                    f"Successfully downloaded {success_count} of {len(matched_files)} files"
                )

            return success_count > 0
        except Exception as e:
            display_error(f"Error during mget: {str(e)}")
            return False

    def cmd_local(self, args: List[str]) -> bool:
        """Set or display local download directory"""
        if not args:
            display_info(f"Current local download directory: {self.local_download_dir}")
            return True

        new_path = args[0]

        try:
            # Resolve path (make absolute if needed)
            if not os.path.isabs(new_path):
                new_path = os.path.abspath(new_path)

            # Create directory if it doesn't exist
            if not os.path.exists(new_path):
                display_info(f"Local directory does not exist, creating: {new_path}")
                os.makedirs(new_path, exist_ok=True)
                # Ensure proper permissions
                os.chmod(new_path, 0o755)
            elif not os.path.isdir(new_path):
                display_error(f"Path exists but is not a directory: {new_path}")
                return False

            self.local_download_dir = new_path
            display_success(f"Local download directory set to: {new_path}")
            return True
        except Exception as e:
            display_error(f"Failed to set local directory: {str(e)}")
            return False

    def cmd_help(self, args: List[str]) -> bool:
        """Display help information"""
        if args:
            cmd = args[0].lower()
            if cmd == "put":
                display_info("\nUpload a file to the remote server:")
                display_info("Usage: put <local_file> [<remote_file>]")
                display_info(
                    "If <remote_file> is not specified, the file will be uploaded with the same name"
                )
            elif cmd == "get":
                display_info("\nDownload a file from the remote server:")
                display_info("Usage: get <remote_file> [<local_file>]")
                display_info(
                    "If <local_file> is not specified, the file will be downloaded to the current local directory"
                )
            elif cmd == "ls":
                display_info("\nList files in a remote directory:")
                display_info("Usage: ls [<remote_path>]")
                display_info(
                    "If <remote_path> is not specified, lists the current remote directory"
                )
            elif cmd == "lls":
                display_info("\nList files in the local download directory:")
                display_info("Usage: lls [<local_path>]")
                display_info(
                    "If <local_path> is not specified, lists the current local download directory"
                )
                display_info("Shows file details, total size, and file count")
            elif cmd == "cd":
                display_info("\nChange remote working directory:")
                display_info("Usage: cd <remote_path>")
            elif cmd == "pwd":
                display_info("\nShow current remote working directory:")
                display_info("Usage: pwd")
            elif cmd == "mget":
                display_info("\nDownload multiple files matching a pattern:")
                display_info("Usage: mget <remote_file_pattern>")
                display_info("Supports wildcard patterns (e.g., *.txt)")
            elif cmd == "local":
                display_info("\nSet or display local download directory:")
                display_info("Usage: local [<local_path>]")
                display_info(
                    "If <local_path> is not specified, displays the current local download directory"
                )
            elif cmd == "exit":
                display_info("\nExit SCP mode and return to lazyssh prompt:")
                display_info("Usage: exit")
            else:
                display_error(f"Unknown command: {cmd}")
                self.cmd_help([])
            return True

        display_info("\nAvailable SCP mode commands:")
        display_info("  put     - Upload a file to the remote server")
        display_info("  get     - Download a file from the remote server")
        display_info("  ls      - List files in a remote directory")
        display_info("  lls     - List files in the local download directory")
        display_info("  cd      - Change remote working directory")
        display_info("  pwd     - Show current remote working directory")
        display_info("  mget    - Download multiple files matching a pattern")
        display_info("  local   - Set or display local download directory")
        display_info("  exit    - Exit SCP mode")
        display_info("  help    - Show this help message or help for a specific command")
        display_info("\nUse 'help <command>' for detailed help on a specific command")
        return True

    def cmd_exit(self, args: List[str]) -> bool:
        """Exit SCP mode"""
        return True

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format (KB, MB, GB)"""
        if size_bytes < 1024:
            return f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def cmd_lls(self, args: List[str]) -> bool:
        """List contents of the local download directory with total size and file count"""
        try:
            # Determine which directory to list
            target_dir = self.local_download_dir
            if args:
                # Allow listing other directories relative to the download dir
                path = args[0]
                if os.path.isabs(path):
                    target_dir = path
                else:
                    target_dir = os.path.join(self.local_download_dir, path)

            # Check if directory exists
            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                display_error(f"Directory not found: {target_dir}")
                return False

            # Get directory contents
            total_size = 0
            file_count = 0
            dir_count = 0

            display_info(f"Contents of {target_dir}:")

            # List directory contents in a simple format
            for item in sorted(os.listdir(target_dir)):
                full_path = os.path.join(target_dir, item)

                # Get file info
                is_dir = os.path.isdir(full_path)

                if is_dir:
                    dir_count += 1
                    display_info(f"  {item}/")
                else:
                    # Get file size
                    size = os.path.getsize(full_path)
                    file_count += 1
                    total_size += size

                    # Format size for display
                    human_size = self._format_file_size(size)
                    display_info(f"  {item} ({human_size})")

            # Show summary
            human_total = self._format_file_size(total_size)
            display_info(
                f"\nTotal: {file_count} files, {dir_count} directories, {human_total} total size"
            )

            return True

        except Exception as e:
            display_error(f"Error listing directory: {str(e)}")
            return False
