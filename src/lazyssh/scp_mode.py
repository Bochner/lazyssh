"""SCP mode interface for LazySSH using prompt_toolkit"""

import os
import shlex
import subprocess
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm, IntPrompt
from rich.table import Table
from rich.text import Text

from .models import SSHConnection
from .ssh import SSHManager
from .ui import display_error, display_info, display_success


class SCPModeCompleter(Completer):
    """Completer for prompt_toolkit with SCP mode commands"""

    def __init__(self, scp_mode: "SCPMode") -> None:
        self.scp_mode = scp_mode

    def get_completions(self, document: Document, complete_event: Any) -> Iterable[Completion]:
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
                        if partial_path:
                            base_dir = str(Path(partial_path).parent)
                        else:
                            base_dir = self.scp_mode.current_remote_dir

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
                # Complete local files from the upload directory
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[1] if len(words) > 1 else ""
                    if partial_path:
                        base_dir = str(Path(partial_path).parent)
                    else:
                        base_dir = self.scp_mode.local_upload_dir

                    if not base_dir:
                        base_dir = self.scp_mode.local_upload_dir

                    # Get filename part for matching
                    filename_part = Path(partial_path).name if partial_path else ""

                    # List files in the local upload directory
                    for f in os.listdir(base_dir or "."):
                        if not filename_part or f.startswith(filename_part):
                            full_path = str(Path(base_dir) / f) if base_dir else f
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
                        if partial_path:
                            base_dir = str(Path(partial_path).parent)
                        else:
                            base_dir = self.scp_mode.current_remote_dir

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

        elif command == "local" and (len(words) == 1 or len(words) == 2 or len(words) == 3):
            # Handle different stages of local command completion
            if len(words) == 1 and text.endswith(" "):
                # After "local " - suggest ONLY download/upload options
                yield Completion("download", start_position=-len(word_before_cursor))
                yield Completion("upload", start_position=-len(word_before_cursor))
                # Don't show directory completions here
            elif len(words) == 2:
                if words[1] in ["download", "upload"] and text.endswith(" "):
                    # After "local download " or "local upload " - complete directories
                    try:
                        # List directories in the current directory
                        for d in os.listdir("."):
                            full_path = Path(".") / d
                            if full_path.is_dir():
                                result_path = str(full_path)
                                yield Completion(result_path, start_position=0)
                    except Exception:
                        # Silently fail for completions
                        pass
                else:
                    # Complete local directories for backward compatibility
                    try:
                        # Get partial path from what user typed so far
                        partial_path = words[1]

                        if partial_path:
                            path_obj = Path(partial_path)
                            base_dir = str(path_obj.parent) if path_obj.name else str(path_obj)
                            dirname_part = path_obj.name
                        else:
                            base_dir = "."
                            dirname_part = ""

                        # List directories in the local directory
                        for d in os.listdir(base_dir or "."):
                            full_path = Path(base_dir) / d
                            if (
                                not dirname_part or d.startswith(dirname_part)
                            ) and full_path.is_dir():
                                result_path = str(full_path) if base_dir else d
                                yield Completion(result_path, start_position=-len(partial_path))
                    except Exception:
                        # Silently fail for completions
                        pass
            elif len(words) == 3 and words[1] in ["download", "upload"] and not text.endswith(" "):
                # Complete directory path for "local download <path>" or "local upload <path>"
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[2]

                    if partial_path:
                        path_obj = Path(partial_path)
                        base_dir = str(path_obj.parent) if path_obj.name else str(path_obj)
                        dirname_part = path_obj.name
                    else:
                        base_dir = "."
                        dirname_part = ""

                    # List directories in the local directory
                    for d in os.listdir(base_dir or "."):
                        full_path = Path(base_dir) / d
                        if (not dirname_part or d.startswith(dirname_part)) and full_path.is_dir():
                            result_path = str(full_path) if base_dir else d
                            yield Completion(result_path, start_position=-len(partial_path))
                except Exception:
                    # Silently fail for completions
                    pass
        elif command == "lls" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete local directories
                partial_path = words[1] if len(words) > 1 else ""

                if partial_path:
                    path_obj = Path(partial_path)
                    base_dir = str(path_obj.parent) if path_obj.name else str(path_obj)
                    filename_part = path_obj.name
                else:
                    base_dir = "."
                    filename_part = ""

                if not base_dir:
                    base_dir = "."

                try:
                    # List files in the directory
                    files = os.listdir(base_dir)

                    for f in files:
                        if not filename_part or f.startswith(filename_part):
                            # Check if it's a directory and append / if it is
                            full_path = Path(base_dir) / f
                            if full_path.is_dir():
                                f = f + "/"
                            yield Completion(f, start_position=-len(filename_part))
                except (FileNotFoundError, PermissionError):
                    # Silently fail for completions
                    pass

        elif command == "lcd" and (len(words) == 1 or len(words) == 2):
            # Always offer completions after typing the command and a space
            if (len(words) == 1 and text.endswith(" ")) or len(words) == 2:
                # Complete local directories
                try:
                    # Get partial path from what user typed so far
                    partial_path = words[1] if len(words) > 1 else ""

                    if partial_path:
                        path_obj = Path(partial_path)
                        base_dir = str(path_obj.parent)
                        dirname_part = path_obj.name
                    else:
                        base_dir = "."
                        dirname_part = ""

                    # List directories in the local directory
                    for d in os.listdir(base_dir or "."):
                        full_path = Path(base_dir) / d
                        if (not dirname_part or d.startswith(dirname_part)) and full_path.is_dir():
                            result_path = str(full_path) if base_dir else d
                            yield Completion(result_path, start_position=-len(partial_path))
                except Exception:
                    # Silently fail for completions
                    pass


class SCPMode:
    """SCP mode for file transfers through established SSH connections"""

    def __init__(self, ssh_manager: SSHManager, selected_connection: str | None = None):
        self.ssh_manager = ssh_manager
        self.selected_connection: str | None = selected_connection
        self.current_remote_dir = "~"  # Default to home directory
        self.local_download_dir = (
            os.getcwd()
        )  # Default to current working directory (will be updated after connection)
        self.local_upload_dir = (
            os.getcwd()
        )  # Default to current working directory (will be updated after connection)
        self.socket_path: str | None = None
        self.conn: SSHConnection | None = None  # Initialize as None until connect() is called

        # Initialize commands
        self.commands = {
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "quit": self.cmd_exit,
            "put": self.cmd_put,
            "get": self.cmd_get,
            "ls": self.cmd_ls,
            "pwd": self.cmd_pwd,
            "cd": self.cmd_cd,
            "local": self.cmd_local,
            "mget": self.cmd_mget,
            "lls": self.cmd_lls,
        }

        # Create the history directory if it doesn't exist
        history_dir = str(Path.home() / ".lazyssh")
        os.makedirs(history_dir, exist_ok=True)

        # Initialize prompt_toolkit components
        self.completer = SCPModeCompleter(self)
        self.session: PromptSession = PromptSession(
            history=FileHistory(str(Path.home() / ".lazyssh" / "scp_history"))
        )
        self.style = Style.from_dict(
            {
                "prompt": "ansigreen bold",
                "path": "ansiyellow",
                "local": "ansiblue",
            }
        )

        if selected_connection:
            socket_path = f"/tmp/{selected_connection}"
            if socket_path in ssh_manager.connections:
                self.conn = ssh_manager.connections[socket_path]
                self.socket_path = socket_path
                conn_data_dir = self.conn.downloads_dir if self.conn else None
                if conn_data_dir:
                    self.local_download_dir = conn_data_dir
                conn_upload_dir = self.conn.uploads_dir if self.conn else None
                if conn_upload_dir:
                    self.local_upload_dir = conn_upload_dir

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

        # Set the local download and upload directories to the connection's directories
        self.local_download_dir = self.conn.downloads_dir
        self.local_upload_dir = self.conn.uploads_dir

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

    def _execute_ssh_command(self, remote_command: str) -> Any | None:
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
            f" [↓<local>{self.local_download_dir}</local> | ↑<local>{self.local_upload_dir}</local>]> "
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
            conn_name = Path(socket_path).name
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

        # Use Rich's prompt for the connection selection
        try:
            choice = IntPrompt.ask("Enter selection (number)", default=1)
            if 1 <= choice <= len(connections):
                self.selected_connection = connections[choice - 1]
                return True
            else:
                display_error("Invalid selection")
                return False
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
        return str(Path(self.current_remote_dir) / path)

    def _resolve_local_path(self, path: str, for_upload: bool = False) -> str:
        """Resolve a local path relative to the local download or upload directory"""
        if not path:
            return self.local_upload_dir if for_upload else self.local_download_dir
        if Path(path).is_absolute():
            return path

        # Join with local download or upload directory
        base_dir = self.local_upload_dir if for_upload else self.local_download_dir
        return str(Path(base_dir) / path)

    def _get_scp_command(self, source: str, destination: str) -> list[str]:
        """Build the SCP command"""
        return ["scp", "-q", "-o", f"ControlPath={self.socket_path}", source, destination]

    def _get_file_size(self, path: str, is_remote: bool = False) -> int:
        """Get the size of a file in bytes"""
        try:
            if is_remote and self.conn:
                # Get size of remote file
                result = self._execute_ssh_command(f"stat -c %s {path}")
                if result and result.returncode == 0:
                    return int(result.stdout.strip())
                return 0
            else:
                # Get size of local file
                return Path(path).stat().st_size
        except Exception:
            return 0

    def cmd_put(self, args: list[str]) -> bool:
        """Upload files to the remote server"""
        if not args:
            display_error("Usage: put <local_file> [remote_path]")
            return False

        if not self.conn:
            display_error("Not connected to an SSH server")
            return False

        local_file = self._resolve_local_path(args[0], for_upload=True)

        if len(args) == 2:
            remote_file = self._resolve_remote_path(args[1])
        else:
            # Use the same filename in the current remote directory
            filename = Path(local_file).name
            remote_file = str(Path(self.current_remote_dir) / filename)

        try:
            if not Path(local_file).exists():
                display_error(f"Local file not found: {local_file}")
                return False

            # Get file size for progress tracking
            file_size = self._get_file_size(local_file)
            human_size = self._format_file_size(file_size)

            display_info(f"Uploading {local_file} to {remote_file} ({human_size})...")

            # Get the SCP command
            remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
            cmd = self._get_scp_command(local_file, remote_path)

            with Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Uploading {Path(local_file).name}", total=file_size)

                # Start the upload process
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # For uploads, we cannot easily track progress, so use an estimation approach
                # that smoothly progresses from 0 to 100%
                start_time = time.time()
                estimated_duration = max(
                    2, file_size / 1000000
                )  # Estimate based on file size (min 2 seconds)

                while process.poll() is None:
                    elapsed = time.time() - start_time
                    # Calculate progress as a percentage of estimated time
                    progress_percentage = min(0.99, elapsed / estimated_duration)
                    current_progress = int(file_size * progress_percentage)
                    progress.update(task, completed=current_progress)
                    time.sleep(0.1)

                # Complete the progress bar
                progress.update(task, completed=file_size)

                result = process.wait()
                stderr = process.stderr.read() if process.stderr else ""

            if result != 0:
                display_error(f"Upload failed: {stderr}")
                return False

            display_success(f"Successfully uploaded {local_file} to {remote_file}")
            return True
        except Exception as e:
            display_error(f"Upload failed: {str(e)}")
            return False

    def cmd_get(self, args: list[str]) -> bool:
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
            filename = Path(remote_file).name
            local_file = str(Path(self.local_download_dir) / filename)

        try:
            # First check if the remote file exists
            check_cmd = self._execute_ssh_command(f"test -f {remote_file} && echo 'exists'")
            if not check_cmd or check_cmd.returncode != 0 or "exists" not in check_cmd.stdout:
                display_error(f"Remote file not found: {remote_file}")
                return False

            # Get file size for progress tracking
            file_size = self._get_file_size(remote_file, is_remote=True)
            human_size = self._format_file_size(file_size)

            # Create local directory if it doesn't exist
            local_dir_path = Path(local_file).parent
            if local_dir_path.name and not local_dir_path.exists():
                local_dir_path.mkdir(parents=True, exist_ok=True)
                # Ensure proper permissions
                local_dir_path.chmod(0o755)

            display_info(f"Downloading {remote_file} to {local_file} ({human_size})...")

            # Get the SCP command
            remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
            cmd = self._get_scp_command(remote_path, local_file)

            with Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {Path(remote_file).name}", total=file_size)

                # Start the download process
                process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Monitor progress
                downloaded_file = Path(local_file)
                while process.poll() is None:
                    if downloaded_file.exists():
                        current_size = downloaded_file.stat().st_size
                        progress.update(task, completed=current_size)
                    # Sleep a bit to avoid too frequent updates
                    time.sleep(0.1)

                # Complete the progress bar
                progress.update(task, completed=file_size)

                result = process.wait()
                stderr = process.stderr.read() if process.stderr else ""

            if result != 0:
                display_error(f"Download failed: {stderr}")
                return False

            display_success(f"Successfully downloaded {remote_file} to {local_file}")
            return True
        except Exception as e:
            display_error(f"Download failed: {str(e)}")
            return False

    def cmd_ls(self, args: list[str]) -> bool:
        """List contents of a remote directory"""
        path = self.current_remote_dir
        if args:
            path = self._resolve_remote_path(args[0])

        try:
            # Use ls -la command via SSH for detailed listing
            result = self._execute_ssh_command(f"ls -la {path}")

            if not result or result.returncode != 0:
                display_error(
                    f"Error listing directory: {result.stderr if result else 'Unknown error'}"
                )
                return False

            # Format and display the output
            output = result.stdout.strip()
            if not output:
                display_info(f"Directory [bold blue]{path}[/] is empty")
                return True

            display_info(f"Contents of [bold blue]{path}[/]:")

            # Create a Rich table
            table = Table(
                show_header=True, header_style="bold cyan", box=None, padding=(0, 1, 0, 1)
            )

            # Add columns
            table.add_column("Permissions", style="dim")
            table.add_column("Links", justify="right", style="dim")
            table.add_column("Owner")
            table.add_column("Group")
            table.add_column("Size", justify="right")
            table.add_column("Modified")
            table.add_column("Name")

            # Parse ls output and add rows
            lines = output.split("\n")
            for line in lines:
                # Skip total line
                if line.startswith("total "):
                    continue

                # Parse the ls -la output, which follows a standard format
                # Example: -rw-r--r-- 1 username group 12345 Jan 01 12:34 filename
                parts = line.split(maxsplit=8)
                if len(parts) < 9:
                    continue

                perms, links, owner, group, size_str, date1, date2, date3, name = parts

                # Format the size to be human readable
                try:
                    size_bytes = int(size_str)
                    human_size = self._format_file_size(size_bytes)
                except ValueError:
                    human_size = size_str

                # Format the date in a consistent way - attempt to convert to a standard format
                try:
                    # Try to parse the date parts into a consistent format
                    # Handle different date formats from ls
                    date_str = f"{date1} {date2} {date3}"

                    # Parse the date - try different formats
                    date_formats = [
                        "%b %d %Y",  # Jan 01 2023
                        "%b %d %H:%M",  # Jan 01 12:34
                        "%Y-%m-%d %H:%M",  # 2023-01-01 12:34
                    ]

                    parsed_date = None
                    for fmt in date_formats:
                        try:
                            parsed_date = time.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue

                    if parsed_date:
                        # Format in a consistent way
                        date = time.strftime("%b %d %Y %H:%M", parsed_date)
                    else:
                        # Fall back to original if parsing fails
                        date = date_str
                except Exception:
                    # If any error, just use the original
                    date = f"{date1} {date2} {date3}"

                # Color the filename based on type
                name_text = Text(name)
                if perms.startswith("d"):  # Directory
                    name_text.stylize("bold blue")
                elif perms.startswith("l"):  # Symlink
                    name_text.stylize("cyan")
                elif perms.startswith("-") and (
                    "x" in perms[1:4] or "x" in perms[4:7] or "x" in perms[7:10]
                ):  # Executable
                    name_text.stylize("green")

                table.add_row(perms, links, owner, group, human_size, date, name_text)

            # Display the table
            console = Console()
            console.print(table)

            return True
        except Exception as e:
            display_error(f"Error listing directory: {str(e)}")
            return False

    def cmd_cd(self, args: list[str]) -> bool:
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

    def cmd_pwd(self, args: list[str]) -> bool:
        """Print current remote directory"""
        display_info(f"Current remote directory: {self.current_remote_dir}")
        return True

    def cmd_mget(self, args: list[str]) -> bool:
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

            # Display matched files in a Rich table instead of simple list
            display_info(f"Found {len(matched_files)} matching files:")

            # Create a Rich table for listing the files
            table = Table(
                show_header=True, header_style="bold cyan", box=None, padding=(0, 1, 0, 1)
            )

            # Add columns
            table.add_column("Filename", style="cyan")
            table.add_column("Size", justify="right")

            # Add files to table
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
                        table.add_row(filename, human_size)
                    except ValueError:
                        table.add_row(filename, "unknown size")
                else:
                    table.add_row(filename, "unknown size")

            # Display the table
            console = Console()
            console.print(table)

            # Format total size in human-readable format
            human_total = self._format_file_size(total_size)
            display_info(f"Total download size: [bold green]{human_total}[/]")

            # Confirm download using Rich's Confirm.ask for a color-coded prompt
            if not Confirm.ask(
                f"Download [bold cyan]{len(matched_files)}[/] files to [bold blue]{self.local_download_dir}[/]?"
            ):
                display_info("Download cancelled")
                return False

            # Ensure download directory exists with proper permissions
            download_dir_path = Path(self.local_download_dir)
            if not download_dir_path.exists():
                download_dir_path.mkdir(parents=True, exist_ok=True)
                download_dir_path.chmod(0o755)

            # Download files with progress tracking
            success_count = 0

            # Start timing the download
            start_time = time.time()

            with Progress(
                TextColumn("[bold blue]{task.description}", justify="right"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                DownloadColumn(),
                "•",
                TransferSpeedColumn(),
                "•",
                TimeRemainingColumn(),
            ) as progress:
                # Create a task for overall progress based on total bytes, not file count
                overall_task = progress.add_task("Overall progress", total=total_size)

                for idx, filename in enumerate(matched_files):
                    remote_file = str(Path(self.current_remote_dir) / filename)
                    local_file = str(Path(self.local_download_dir) / filename)
                    file_size = file_sizes.get(filename, 0)

                    try:
                        # Create a task for this file
                        file_task = progress.add_task(
                            f"[cyan]Downloading {filename}", total=file_size
                        )

                        # Get the SCP command
                        remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
                        cmd = self._get_scp_command(remote_path, local_file)

                        # Start the download process
                        process = subprocess.Popen(
                            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                        )

                        # Monitor progress
                        downloaded_file = Path(local_file)
                        last_size = 0
                        while process.poll() is None:
                            if downloaded_file.exists():
                                current_size = downloaded_file.stat().st_size
                                # Update file progress
                                progress.update(file_task, completed=current_size)

                                # Update overall progress with the delta from last check
                                if current_size > last_size:
                                    progress.update(overall_task, advance=current_size - last_size)
                                    last_size = current_size
                            time.sleep(0.1)

                        # Complete the progress bar for this file
                        final_size = file_size
                        if downloaded_file.exists():
                            final_size = downloaded_file.stat().st_size

                        # Update file task to completion
                        progress.update(file_task, completed=final_size)

                        # Update overall progress with any remaining bytes
                        if final_size > last_size:
                            progress.update(overall_task, advance=final_size - last_size)

                        result = process.wait()
                        stderr = process.stderr.read() if process.stderr else ""

                        if result != 0:
                            display_error(f"Failed to download {filename}: {stderr}")
                        else:
                            success_count += 1

                    except Exception as e:
                        display_error(f"Failed to download {filename}: {str(e)}")

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            elapsed_str = f"{elapsed_time:.1f} seconds"
            if elapsed_time > 60:
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                elapsed_str = f"{minutes}m {seconds}s"

            if success_count > 0:
                # Include file size and elapsed time in success message
                display_success(
                    f"Successfully downloaded [bold cyan]{success_count}[/] of [bold cyan]{len(matched_files)}[/] files ([bold green]{self._format_file_size(total_size)}[/] in [bold]{elapsed_str}[/])"
                )

            return success_count > 0
        except Exception as e:
            display_error(f"Error during mget: {str(e)}")
            return False

    def cmd_local(self, args: list[str]) -> bool:
        """Set or display local download and upload directories"""
        if not args:
            display_info(f"Current local download directory: {self.local_download_dir}")
            display_info(f"Current local upload directory: {self.local_upload_dir}")
            return True

        if len(args) >= 2 and args[0] in ["download", "upload"]:
            # Handle specific directory type
            dir_type = args[0]
            new_path = args[1]

            try:
                # Resolve path (make absolute if needed)
                path_obj = Path(new_path)
                if not path_obj.is_absolute():
                    path_obj = path_obj.absolute()

                new_path = str(path_obj)

                # Create directory if it doesn't exist
                if not path_obj.exists():
                    display_info(f"Local directory does not exist, creating: {new_path}")
                    path_obj.mkdir(parents=True, exist_ok=True)
                    # Ensure proper permissions
                    path_obj.chmod(0o755)
                elif not path_obj.is_dir():
                    display_error(f"Path exists but is not a directory: {new_path}")
                    return False

                # Set the appropriate directory
                if dir_type == "download":
                    self.local_download_dir = new_path
                    display_success(f"Local download directory set to: {new_path}")
                else:  # upload
                    self.local_upload_dir = new_path
                    display_success(f"Local upload directory set to: {new_path}")

                return True
            except Exception as e:
                display_error(f"Failed to set local directory: {str(e)}")
                return False
        else:
            # Legacy behavior - set download directory for backward compatibility
            new_path = args[0]

            try:
                # Resolve path (make absolute if needed)
                path_obj = Path(new_path)
                if not path_obj.is_absolute():
                    path_obj = path_obj.absolute()

                new_path = str(path_obj)

                # Create directory if it doesn't exist
                if not path_obj.exists():
                    display_info(f"Local directory does not exist, creating: {new_path}")
                    path_obj.mkdir(parents=True, exist_ok=True)
                    # Ensure proper permissions
                    path_obj.chmod(0o755)
                elif not path_obj.is_dir():
                    display_error(f"Path exists but is not a directory: {new_path}")
                    return False

                self.local_download_dir = new_path
                display_success(f"Local download directory set to: {new_path}")
                display_info(
                    "Note: Use 'local download <path>' or 'local upload <path>' to set specific directories"
                )
                return True
            except Exception as e:
                display_error(f"Failed to set local directory: {str(e)}")
                return False

    def cmd_help(self, args: list[str]) -> bool:
        """Display help information"""
        if args:
            cmd = args[0].lower()
            if cmd == "put":
                display_info("[bold cyan]\nUpload a file to the remote server:[/bold cyan]")
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]put[/cyan] [yellow]<local_file>[/yellow] [[yellow]<remote_file>[/yellow]]"
                )
                display_info(
                    "If [yellow]<remote_file>[/yellow] is not specified, the file will be uploaded with the same name"
                )
                display_info(
                    "[dim]Local files are read from the upload directory shown in the prompt[/dim]"
                )
                display_info(
                    "[dim]Use tab completion to see available files in the upload directory[/dim]"
                )
            elif cmd == "get":
                display_info("[bold cyan]\nDownload a file from the remote server:[/bold cyan]")
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]get[/cyan] [yellow]<remote_file>[/yellow] [[yellow]<local_file>[/yellow]]"
                )
                display_info(
                    "If [yellow]<local_file>[/yellow] is not specified, the file will be downloaded to the current local directory"
                )
            elif cmd == "ls":
                display_info("[bold cyan]\nList files in a remote directory:[/bold cyan]")
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]ls[/cyan] [[yellow]<remote_path>[/yellow]]"
                )
                display_info(
                    "If [yellow]<remote_path>[/yellow] is not specified, lists the current remote directory"
                )
            elif cmd == "pwd":
                display_info("[bold cyan]\nShow current remote working directory:[/bold cyan]")
                display_info("[yellow]Usage:[/yellow] [cyan]pwd[/cyan]")
            elif cmd == "cd":
                display_info("[bold cyan]\nChange remote working directory:[/bold cyan]")
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]cd[/cyan] [yellow]<remote_path>[/yellow]"
                )
            elif cmd == "local":
                display_info(
                    "[bold cyan]\nSet or display local download and upload directories:[/bold cyan]"
                )
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]local[/cyan] [[yellow]<local_path>[/yellow]]"
                )
                display_info(
                    "If [yellow]<local_path>[/yellow] is not specified, displays both the download and upload directories"
                )
                display_info("[magenta bold]To set a specific directory type:[/magenta bold]")
                display_info(
                    "  [cyan]local download[/cyan] [yellow]<path>[/yellow] - Set the download directory"
                )
                display_info(
                    "  [cyan]local upload[/cyan] [yellow]<path>[/yellow]   - Set the upload directory"
                )
            elif cmd == "exit":
                display_info("[bold cyan]\nExit SCP mode and return to lazyssh prompt:[/bold cyan]")
                display_info("[yellow]Usage:[/yellow] [cyan]exit[/cyan]")
            elif cmd == "lls":
                display_info(
                    "[bold cyan]\nList contents of the local download directory:[/bold cyan]"
                )
                display_info(
                    "[yellow]Usage:[/yellow] [cyan]lls[/cyan] [[yellow]<local_path>[/yellow]]"
                )
                display_info(
                    "If [yellow]<local_path>[/yellow] is not specified, lists the current local download directory"
                )
                display_info("Shows file sizes and directory summary information")
            else:
                display_error(f"Unknown command: {cmd}")
                self.cmd_help([])
            return True

        display_info("[bold cyan]\nAvailable SCP mode commands:[/bold cyan]")
        display_info("  [cyan]put[/cyan]     - Upload a file to the remote server")
        display_info("  [cyan]get[/cyan]     - Download a file from the remote server")
        display_info("  [cyan]ls[/cyan]      - List files in a remote directory")
        display_info("  [cyan]lls[/cyan]     - List files in the local download directory")
        display_info("  [cyan]pwd[/cyan]     - Show current remote working directory")
        display_info("  [cyan]cd[/cyan]      - Change remote working directory")
        display_info("  [cyan]local[/cyan]   - Set or display local download directory")
        display_info("  [cyan]exit[/cyan]    - Exit SCP mode")
        display_info(
            "  [cyan]help[/cyan]    - Show this help message or help for a specific command"
        )
        display_info(
            "\n[dim]Use 'help [yellow]<command>[/yellow]' for detailed help on a specific command[/dim]"
        )
        return True

    def cmd_exit(self, args: list[str]) -> bool:
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

    def cmd_lls(self, args: list[str]) -> bool:
        """List contents of the local download directory with total size and file count"""
        try:
            # Determine which directory to list
            target_dir_path = Path(self.local_download_dir)
            if args:
                # Allow listing other directories relative to the download dir
                path = args[0]
                path_obj = Path(path)
                if path_obj.is_absolute():
                    target_dir_path = path_obj
                else:
                    target_dir_path = Path(self.local_download_dir) / path

            # Check if directory exists
            if not target_dir_path.exists() or not target_dir_path.is_dir():
                display_error(f"Directory not found: {target_dir_path}")
                return False

            display_info(f"Contents of [bold blue]{target_dir_path}[/]:")

            # Create a Rich table
            table = Table(
                show_header=True, header_style="bold cyan", box=None, padding=(0, 1, 0, 1)
            )

            # Add columns - removed Type column
            table.add_column("Permissions", style="dim")
            table.add_column("Size", justify="right")
            table.add_column("Modified")
            table.add_column("Name")

            # Get directory contents
            total_size = 0
            file_count = 0
            dir_count = 0

            # List directory contents in a table format
            for item in sorted(target_dir_path.iterdir()):
                # Get file stat info
                stat = item.stat()

                # Format permission bits similar to Unix ls
                mode = stat.st_mode
                perms = ""
                for who in [0o700, 0o70, 0o7]:  # User, group, other
                    perms += "r" if mode & (who >> 2) else "-"
                    perms += "w" if mode & (who >> 1) else "-"
                    perms += "x" if mode & who else "-"

                # Format modification time - more concise format
                mtime = time.strftime("%b %d %Y %H:%M", time.localtime(stat.st_mtime))

                if item.is_dir():
                    dir_count += 1
                    name_text = Text(f"{item.name}/")
                    name_text.stylize("bold blue")
                    size_text = "--"
                    table.add_row(perms, size_text, mtime, name_text)
                else:
                    # Get file size
                    size = item.stat().st_size
                    file_count += 1
                    total_size += size

                    # Format size for display
                    human_size = self._format_file_size(size)

                    # Create name text with styling
                    name_text = Text(item.name)

                    # Colorize based on file type and permissions
                    if item.suffix.lower() in [".py", ".js", ".sh", ".bash", ".zsh"]:
                        name_text.stylize("green")  # Script files
                    elif item.suffix.lower() in [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".tif",
                        ".tiff",
                    ]:
                        name_text.stylize("magenta")  # Image files
                    elif item.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv", ".wmv"]:
                        name_text.stylize("cyan")  # Video files
                    elif item.suffix.lower() in [".tar", ".gz", ".zip", ".rar", ".7z", ".bz2"]:
                        name_text.stylize("yellow")  # Archive files

                    # Check if executable and style if needed
                    if (mode & 0o100) or (mode & 0o010) or (mode & 0o001):
                        if not name_text.style:
                            name_text.stylize("green")

                    table.add_row(perms, human_size, mtime, name_text)

            # Display the table
            console = Console()
            console.print(table)

            # Show summary footer
            human_total = self._format_file_size(total_size)
            console.print(
                f"\nTotal: [bold cyan]{file_count}[/] files, [bold cyan]{dir_count}[/] directories, [bold green]{human_total}[/] total size"
            )

            return True

        except Exception as e:
            display_error(f"Error listing directory: {str(e)}")
            return False
