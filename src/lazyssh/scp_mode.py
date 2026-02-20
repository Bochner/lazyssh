"""SCP mode interface for LazySSH using prompt_toolkit"""

import os
import shlex
import subprocess
import time
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

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
from rich.table import Column
from rich.text import Text
from rich.tree import Tree

from .console_instance import console, display_error, display_info, display_success
from .logging_module import (
    SCP_LOGGER,
    format_size,
    get_connection_logger,  # noqa: F401 — re-exported for plugin/test access
    log_file_transfer,
    log_scp_command,
    set_debug_mode,
    update_transfer_stats,
)
from .models import SSHConnection
from .ssh import SSHManager
from .ui import create_standard_table, get_console

# Cache and throttling configuration
CACHE_TTL_SECONDS = 30
COMPLETION_THROTTLE_MS = 300


def truncate_filename(filename: str, max_length: int = 30) -> str:
    """Truncate filename to fit within progress bar display."""
    if len(filename) <= max_length:
        return filename

    # Keep the extension if possible
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        if len(ext) + 4 <= max_length:  # 4 for "..."
            truncated_name = name[: max_length - len(ext) - 3] + "..."
            return f"{truncated_name}.{ext}"

    # Fallback: just truncate with ellipsis
    return filename[: max_length - 3] + "..."


def create_progress_bar(console_instance: Console) -> Progress:
    """Create a progress bar with proper sizing and filename truncation."""
    # Use Column ratios to control width allocation
    # Description gets 1/4 of width, bar gets 2/4, other columns get 1/4
    description_column = TextColumn("[info]{task.description}[/info]", table_column=Column(ratio=1))
    bar_column = BarColumn(
        bar_width=None, style="info", complete_style="success", table_column=Column(ratio=2)
    )

    return Progress(
        description_column,
        bar_column,
        "[progress.percentage]{task.percentage:>3.1f}%",
        "  ",
        TextColumn(
            "[accent]{task.completed:.2f}/{task.total:.2f} MB[/accent]",
            justify="right",
            table_column=Column(ratio=1),
        ),
        "  ",
        TransferSpeedColumn(),
        "  ",
        TimeRemainingColumn(),
        console=console_instance,
        expand=True,
    )


def create_multi_file_progress_bar(console_instance: Console) -> Progress:
    """Create a progress bar for multi-file downloads with proper sizing and smooth updates."""
    # Use Column ratios to control width allocation
    # Description gets 1/4 of width, bar gets 2/4, other columns get 1/4
    description_column = TextColumn("[info]{task.description}[/info]", table_column=Column(ratio=1))
    bar_column = BarColumn(
        bar_width=None, style="info", complete_style="success", table_column=Column(ratio=2)
    )

    return Progress(
        description_column,
        bar_column,
        "[progress.percentage]{task.percentage:>3.1f}%",
        "  ",
        DownloadColumn(),
        "  ",
        TransferSpeedColumn(),
        "  ",
        TimeRemainingColumn(),
        console=console_instance,
        expand=True,
        # Optimize for smoother updates and reduce blocking
        refresh_per_second=20,  # Increase refresh rate for smoother progress
        transient=False,  # Keep progress visible
        # Reduce initial rendering overhead
        disable=False,  # Ensure progress is enabled
        # Optimize for large file transfers
        speed_estimate_period=1.0,  # Update speed estimates every second
    )


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

        if command in ["get", "ls", "mget", "tree"]:
            yield from self._complete_remote_files(words, text, word_before_cursor, complete_event)
        elif command == "put":
            yield from self._complete_put(words, text, word_before_cursor)
        elif command == "cd":
            yield from self._complete_cd(words, text, word_before_cursor, complete_event)
        elif command == "local":
            yield from self._complete_local(words, text, word_before_cursor)
        elif command == "lls":
            yield from self._complete_lls(words, text, word_before_cursor)
        elif command == "lcd":
            yield from self._complete_lcd(words, text, word_before_cursor)

    def _complete_remote_files(
        self, words: list[str], text: str, word_before_cursor: str, complete_event: Any
    ) -> Iterable[Completion]:
        """Complete remote file paths for get, ls, mget, tree commands."""
        if not (len(words) == 1 or len(words) == 2):
            return
        if not ((len(words) == 1 and text.endswith(" ")) or len(words) == 2):
            return
        if not (self.scp_mode.conn and self.scp_mode.socket_path):
            return
        try:
            # Check throttling
            explicit_tab = (
                complete_event.completion_requested
                if hasattr(complete_event, "completion_requested")
                else False
            )
            if self.scp_mode._should_throttle_completion(
                explicit_tab
            ):  # pragma: no cover - remote completion
                partial_path = words[1] if len(words) > 1 else ""
                if partial_path:
                    base_dir = str(Path(partial_path).parent)
                else:
                    base_dir = self.scp_mode.current_remote_dir

                if not base_dir:
                    base_dir = self.scp_mode.current_remote_dir

                cached = self.scp_mode._get_cached_result(base_dir, "ls")
                if cached:
                    for f in cached:
                        if not word_before_cursor or f.startswith(word_before_cursor):
                            yield Completion(f, start_position=-len(word_before_cursor))
                return

            partial_path = words[1] if len(words) > 1 else ""
            if partial_path:  # pragma: no cover - remote completion
                base_dir = str(Path(partial_path).parent)
            else:
                base_dir = self.scp_mode.current_remote_dir

            if not base_dir:  # pragma: no cover
                base_dir = self.scp_mode.current_remote_dir

            file_list = self.scp_mode._get_cached_result(base_dir, "ls")

            if file_list is None:
                self.scp_mode._update_completion_time()
                result = self.scp_mode._execute_ssh_command(f"ls -a {shlex.quote(base_dir)}")
                if result and result.returncode == 0:
                    file_list = result.stdout.strip().split("\n")
                    file_list = [f for f in file_list if f and f not in [".", ".."]]
                    self.scp_mode._update_cache(base_dir, "ls", file_list)

            if file_list:
                for f in file_list:
                    if not word_before_cursor or f.startswith(word_before_cursor):
                        yield Completion(f, start_position=-len(word_before_cursor))
        except (OSError, subprocess.SubprocessError, ValueError):  # pragma: no cover
            pass  # Tab-completion errors are silently ignored to avoid disrupting the UI

    def _complete_put(
        self, words: list[str], text: str, word_before_cursor: str
    ) -> Iterable[Completion]:
        """Complete local file paths for the put command."""
        if not (len(words) == 1 or len(words) == 2):
            return
        if not ((len(words) == 1 and text.endswith(" ")) or len(words) == 2):
            return
        try:
            partial_path = words[1] if len(words) > 1 else ""
            if partial_path:  # pragma: no cover - local completion path
                base_dir = str(Path(partial_path).parent)
            else:
                base_dir = self.scp_mode.local_upload_dir or ""

            if not base_dir:  # pragma: no cover
                base_dir = self.scp_mode.local_upload_dir or ""

            filename_part = Path(partial_path).name if partial_path else ""

            for f in os.listdir(base_dir or "."):
                if not filename_part or f.startswith(filename_part):
                    full_path = str(Path(base_dir) / f) if base_dir else f
                    yield Completion(full_path, start_position=-len(partial_path))
        except (OSError, ValueError):  # pragma: no cover
            pass  # Tab-completion errors are silently ignored to avoid disrupting the UI

    def _complete_cd(
        self, words: list[str], text: str, word_before_cursor: str, complete_event: Any
    ) -> Iterable[Completion]:
        """Complete remote directory paths for the cd command."""
        if not (len(words) == 1 or len(words) == 2):
            return
        if not ((len(words) == 1 and text.endswith(" ")) or len(words) == 2):
            return
        if not (self.scp_mode.conn and self.scp_mode.socket_path):
            return
        try:
            explicit_tab = (
                complete_event.completion_requested
                if hasattr(complete_event, "completion_requested")
                else False
            )
            if self.scp_mode._should_throttle_completion(
                explicit_tab
            ):  # pragma: no cover - remote completion
                partial_path = words[1] if len(words) > 1 else ""
                if partial_path:
                    base_dir = str(Path(partial_path).parent)
                else:
                    base_dir = self.scp_mode.current_remote_dir

                if not base_dir:
                    base_dir = self.scp_mode.current_remote_dir

                cached = self.scp_mode._get_cached_result(base_dir, "find")
                if cached:
                    current_dir_name = Path(base_dir).name
                    filtered_cached = [d for d in cached if d != current_dir_name]
                    for d in filtered_cached:
                        if not word_before_cursor or d.startswith(word_before_cursor):
                            yield Completion(d, start_position=-len(word_before_cursor))
                return

            partial_path = words[1] if len(words) > 1 else ""
            if partial_path:  # pragma: no cover - remote completion path
                base_dir = str(Path(partial_path).parent)
            else:
                base_dir = self.scp_mode.current_remote_dir

            if not base_dir:  # pragma: no cover
                base_dir = self.scp_mode.current_remote_dir

            dir_list = self.scp_mode._get_cached_result(base_dir, "find")

            if dir_list is None:
                self.scp_mode._update_completion_time()
                result = self.scp_mode._execute_ssh_command(
                    f"find {base_dir} -maxdepth 1 -type d -printf '%f\\n'"
                )
                if result and result.returncode == 0:
                    dir_list = result.stdout.strip().split("\n")
                    dir_list = [d for d in dir_list if d and d not in [".", ".."]]
                    current_dir_name = Path(base_dir).name
                    dir_list = [d for d in dir_list if d != current_dir_name]
                    self.scp_mode._update_cache(base_dir, "find", dir_list)

            if dir_list:
                for d in dir_list:
                    if not word_before_cursor or d.startswith(word_before_cursor):
                        yield Completion(d, start_position=-len(word_before_cursor))
        except (OSError, subprocess.SubprocessError, ValueError):  # pragma: no cover
            pass  # Tab-completion errors are silently ignored to avoid disrupting the UI

    def _complete_local(
        self, words: list[str], text: str, word_before_cursor: str
    ) -> Iterable[Completion]:
        """Complete arguments for the local command."""
        if not (len(words) == 1 or len(words) == 2 or len(words) == 3):
            return

        if len(words) == 1 and text.endswith(" "):
            yield Completion("download", start_position=-len(word_before_cursor))
            yield Completion("upload", start_position=-len(word_before_cursor))
        elif len(words) == 2:
            if words[1] in ["download", "upload"] and text.endswith(
                " "
            ):  # pragma: no cover - local completion
                try:
                    for d in os.listdir("."):
                        path_obj = Path(".") / d
                        if path_obj.is_dir():
                            result_path = str(path_obj)
                            yield Completion(result_path, start_position=0)
                except (OSError, ValueError):  # pragma: no cover
                    pass  # Tab-completion errors are silently ignored to avoid disrupting the UI
            else:  # pragma: no cover - local completion path
                try:
                    partial_path = words[1]
                    if partial_path:
                        path_obj = Path(partial_path)
                        base_dir = str(path_obj.parent) if path_obj.name else str(path_obj)
                        dirname_part = path_obj.name
                    else:
                        base_dir = "."
                        dirname_part = ""

                    for d in os.listdir(base_dir or "."):
                        path_obj = Path(base_dir) / d
                        if (not dirname_part or d.startswith(dirname_part)) and path_obj.is_dir():
                            result_path = str(path_obj) if base_dir else d
                            yield Completion(result_path, start_position=-len(partial_path))
                except (OSError, ValueError):  # pragma: no cover
                    pass  # Tab-completion errors are silently ignored to avoid disrupting the UI
        elif (
            len(words) == 3 and words[1] in ["download", "upload"] and not text.endswith(" ")
        ):  # pragma: no cover - local completion
            try:
                partial_path = words[2]
                if partial_path:
                    path_obj = Path(partial_path)
                    base_dir = str(path_obj.parent) if path_obj.name else str(path_obj)
                    dirname_part = path_obj.name
                else:
                    base_dir = "."
                    dirname_part = ""

                for d in os.listdir(base_dir or "."):
                    dir_path_obj = Path(base_dir) / d
                    if (not dirname_part or d.startswith(dirname_part)) and dir_path_obj.is_dir():
                        result_path = str(dir_path_obj) if base_dir else d
                        yield Completion(result_path, start_position=-len(partial_path))
            except (OSError, ValueError):  # pragma: no cover
                pass  # Tab-completion errors are silently ignored to avoid disrupting the UI

    def _complete_lls(
        self, words: list[str], text: str, word_before_cursor: str
    ) -> Iterable[Completion]:  # pragma: no cover - local completion
        """Complete local file/directory paths for the lls command."""
        if not (len(words) == 1 or len(words) == 2):
            return
        if not ((len(words) == 1 and text.endswith(" ")) or len(words) == 2):
            return

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
            files = os.listdir(base_dir)
            for f in files:
                if not filename_part or f.startswith(filename_part):
                    file_path_obj = Path(base_dir) / f
                    if file_path_obj.is_dir():
                        f = f + "/"
                    yield Completion(f, start_position=-len(filename_part))
        except (FileNotFoundError, PermissionError):
            pass

    def _complete_lcd(
        self, words: list[str], text: str, word_before_cursor: str
    ) -> Iterable[Completion]:
        """Complete local directory paths for the lcd command."""
        if not (len(words) == 1 or len(words) == 2):
            return
        if not ((len(words) == 1 and text.endswith(" ")) or len(words) == 2):
            return
        try:
            partial_path = words[1] if len(words) > 1 else ""
            if partial_path:
                path_obj = Path(partial_path)
                base_dir = str(path_obj.parent)
                dirname_part = path_obj.name
            else:
                base_dir = "."
                dirname_part = ""

            for d in os.listdir(base_dir or "."):
                lcd_path_obj = Path(base_dir) / d
                if (not dirname_part or d.startswith(dirname_part)) and lcd_path_obj.is_dir():
                    result_path = str(lcd_path_obj) if base_dir else d
                    yield Completion(result_path, start_position=-len(partial_path))
        except (OSError, ValueError):  # pragma: no cover
            pass  # Tab-completion errors are silently ignored to avoid disrupting the UI


class SCPMode:
    """SCP mode for file transfers through established SSH connections"""

    def __init__(self, ssh_manager: SSHManager, selected_connection: str | None = None):
        """Initialize SCP mode"""
        self.ssh_manager = ssh_manager
        self.console = get_console()

        # State tracking
        self.socket_path: str | None = None
        self.conn: SSHConnection | None = None
        self.connections = ssh_manager.connections

        # Connection name (for logging)
        self.connection_name = selected_connection

        # Stats tracking
        self.download_count = 0
        self.download_bytes = 0
        self.upload_count = 0
        self.upload_bytes = 0

        # Log directory setup
        self.log_dir = Path("/tmp/lazyssh/logs")  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
        if not self.log_dir.exists():  # pragma: no cover - directory creation
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_dir.chmod(0o700)  # Secure permissions

        # Set up history file in /tmp/lazyssh
        self.history_dir = Path("/tmp/lazyssh")  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
        if not self.history_dir.exists():  # pragma: no cover - directory creation
            self.history_dir.mkdir(parents=True, exist_ok=True)
            self.history_dir.chmod(0o700)
        self.history_file = self.history_dir / "scp_history"

        # Initialize directories
        self.current_remote_dir = "~"  # Default to user's home dir
        self.remote_home_dir: str | None = None  # Captured during connection
        self.local_download_dir: str | None = None  # Set dynamically on connection
        self.local_upload_dir: str | None = None  # Set dynamically on connection

        # Directory listing cache: path -> {data, timestamp, type}
        self.directory_cache: dict[str, dict[str, Any]] = {}

        # Completion throttling
        self.last_completion_time: float = 0.0

        # Initialize prompt_toolkit components
        self.completer = SCPModeCompleter(self)
        self.session: PromptSession = PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=self.completer,
            complete_while_typing=True,
        )
        self.style = Style.from_dict(
            {
                "prompt": "#8be9fd bold",  # Cyan - info color
                "path": "#50fa7b",  # Green - success color
                "dir1": "#f1fa8c",  # Yellow - warning color
                "dir2": "#ff79c6",  # Pink - highlight color
                "brackets": "#6272a4",  # Comment - dim color
            }
        )

        # Available commands
        self.commands = {
            "get": self.cmd_get,
            "put": self.cmd_put,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "pwd": self.cmd_pwd,
            "mget": self.cmd_mget,
            "local": self.cmd_local,
            "lls": self.cmd_lls,
            "help": self.cmd_help,
            "exit": self.cmd_exit,
            "tree": self.cmd_tree,
            "lcd": self.cmd_lcd,
            "debug": self.cmd_debug,
        }

        # Try to connect to selected connection if provided
        if selected_connection:
            self.socket_path = f"/tmp/{selected_connection}"  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
            self.connect()

        # Log initialization
        if SCP_LOGGER:
            SCP_LOGGER.debug("SCPMode initialized")

    def connect(self) -> bool:
        """Verify the SSH connection is active via control socket"""
        if not self.socket_path:
            return False

        if self.socket_path not in self.connections:
            display_error(f"SSH connection not found: {self.socket_path}")
            return False

        self.conn = self.connections[self.socket_path]

        # Extract connection name from socket path
        if not self.connection_name:  # pragma: no cover - connection name extraction
            self.connection_name = Path(self.socket_path).name

        # Set default directories
        conn_download_dir = self.conn.downloads_dir
        conn_upload_dir = f"/tmp/lazyssh/{self.connection_name}.d/uploads"  # noqa: S108  # /tmp/lazyssh is the documented runtime directory

        self.local_download_dir = str(conn_download_dir)
        self.local_upload_dir = str(conn_upload_dir)

        # Create upload directory if it doesn't exist
        conn_upload_path = Path(conn_upload_dir)
        if not conn_upload_path.exists():  # pragma: no cover - directory creation
            try:
                conn_upload_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                display_error(f"Failed to create uploads directory: {conn_upload_dir}")
                return False

        # Get initial remote directory and store as home directory
        try:
            cmd = [
                "ssh",
                "-o",
                f"ControlPath={self.socket_path}",
                f"{self.conn.username}@{self.conn.host}",
                "pwd",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603  # args are constructed from validated SSH parameters
            if result.returncode == 0:  # pragma: no cover - SSH connection success
                self.current_remote_dir = result.stdout.strip()
                # Store the initial directory as the remote home directory for tilde expansion
                self.remote_home_dir = self.current_remote_dir
            else:  # pragma: no cover - SSH pwd error handling
                self.current_remote_dir = "~"
                self.remote_home_dir = None
        except (
            OSError,
            subprocess.SubprocessError,
        ):  # pragma: no cover - SSH pwd exception handling
            self.current_remote_dir = "~"
            self.remote_home_dir = None

        console.print(
            f"\n[success]Success:[/success] Connected to [highlight]{self.conn.host}[/highlight] as [variable]{self.conn.username}[/variable]"
        )
        console.print(
            f"[info]Local download directory:[/info] [number]{self.local_download_dir}[/number]"
        )
        console.print(
            f"[info]Local upload directory:[/info] [number]{self.local_upload_dir}[/number]"
        )
        console.print(
            f"[info]Current remote directory:[/info] [number]{self.current_remote_dir}[/number]"
        )
        if SCP_LOGGER:
            SCP_LOGGER.info(f"SCP mode connected to {self.conn.host} via {self.socket_path}")

        # Create connection-specific logs directory
        conn_log_dir = Path(f"/tmp/lazyssh/{self.connection_name}.d/logs")  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
        if not conn_log_dir.exists():  # pragma: no cover - directory creation
            conn_log_dir.mkdir(parents=True, exist_ok=True)
            conn_log_dir.chmod(0o700)

        return True

    def _normalize_cache_path(self, path: str) -> str:
        """
        Normalize a remote path to an absolute path for use as a cache key.
        This ensures cache keys are consistent regardless of how paths are specified.

        Note: This method performs local path normalization only (no SSH calls)
        to keep completion performance fast.
        """
        if not path:  # pragma: no cover - edge case for empty path
            return self.current_remote_dir or "~"

        # If starts with ~, expand to stored home directory
        if path.startswith("~"):
            # If we have a stored remote home directory, expand the tilde
            if self.remote_home_dir:  # pragma: no cover - remote path normalization
                # Handle both "~" and "~/" prefixes
                if path == "~":
                    path = self.remote_home_dir
                elif path.startswith("~/"):
                    # Replace ~/ with the home directory
                    path = self.remote_home_dir + path[1:]
                # Note: paths like "~user" are not expanded (fall through to return path)
                else:
                    # Can't expand ~user without SSH call, return as-is
                    return path
            else:  # pragma: no cover - no home dir fallback
                # No stored home directory, return original path
                return path

        # If already absolute, normalize and return
        if path.startswith("/"):
            # Normalize the path (remove redundant slashes, resolve ./ and ../)
            parts: list[str] = []
            for part in path.split("/"):
                if part == "" or part == ".":
                    continue
                if part == "..":
                    if parts:  # pragma: no cover - path normalization
                        parts.pop()
                else:
                    parts.append(part)
            return "/" + "/".join(parts) if parts else "/"

        # Relative path - resolve against current remote directory
        if self.current_remote_dir:  # pragma: no cover - relative path normalization
            # Join with current directory and normalize
            if self.current_remote_dir.endswith("/"):
                full_path = f"{self.current_remote_dir}{path}"
            else:
                full_path = f"{self.current_remote_dir}/{path}"

            # Normalize the combined path
            if full_path.startswith("/"):
                parts = []
                for part in full_path.split("/"):
                    if part == "" or part == ".":
                        continue
                    if part == "..":
                        if parts:
                            parts.pop()
                    else:
                        parts.append(part)
                return "/" + "/".join(parts) if parts else "/"
            return full_path

        return path  # pragma: no cover - fallback

    def _get_cached_result(self, path: str, command_type: str) -> list[str] | None:
        """Get cached directory listing if available and not expired"""
        # Normalize path to ensure consistent cache keys
        normalized_path = self._normalize_cache_path(path)
        cache_key = f"{normalized_path}:{command_type}"

        if cache_key not in self.directory_cache:
            return None

        cached = self.directory_cache[cache_key]
        cache_time = cached["timestamp"]

        # Check if cache is expired
        if datetime.now() - cache_time > timedelta(seconds=CACHE_TTL_SECONDS):
            if SCP_LOGGER:
                SCP_LOGGER.debug(f"Cache expired for {cache_key}")
            del self.directory_cache[cache_key]
            return None

        if SCP_LOGGER:
            SCP_LOGGER.debug(f"Cache hit for {cache_key}")
        return cast(list[str], cached["data"])

    def _update_cache(self, path: str, command_type: str, data: list[str]) -> None:
        """Update cache with new directory listing"""
        # Normalize path to ensure consistent cache keys
        normalized_path = self._normalize_cache_path(path)
        cache_key = f"{normalized_path}:{command_type}"
        self.directory_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now(),
            "type": command_type,
        }

        if SCP_LOGGER:
            SCP_LOGGER.debug(f"Cache updated for {cache_key} with {len(data)} entries")

    def _invalidate_cache(self, path: str | None = None) -> None:
        """Invalidate cache entries. If path is None, clear all cache."""
        if path is None:
            if SCP_LOGGER and self.directory_cache:
                SCP_LOGGER.debug(f"Clearing all cache ({len(self.directory_cache)} entries)")
            self.directory_cache.clear()
        else:
            # Normalize path to ensure we invalidate the correct cache entries
            normalized_path = self._normalize_cache_path(path)
            # Invalidate all cache entries for this path
            keys_to_delete = [
                k for k in self.directory_cache if k.startswith(f"{normalized_path}:")
            ]
            for key in keys_to_delete:
                del self.directory_cache[key]

            if SCP_LOGGER and keys_to_delete:
                SCP_LOGGER.debug(
                    f"Invalidated {len(keys_to_delete)} cache entries for {normalized_path}"
                )

    def _should_throttle_completion(self, explicit_tab: bool = False) -> bool:
        """Check if completion should be throttled"""
        if explicit_tab:
            return False

        current_time = time.time()
        time_since_last = (current_time - self.last_completion_time) * 1000  # Convert to ms

        if time_since_last < COMPLETION_THROTTLE_MS:
            if SCP_LOGGER:
                SCP_LOGGER.debug(
                    f"Completion throttled ({time_since_last:.0f}ms < {COMPLETION_THROTTLE_MS}ms)"
                )
            return True

        return False

    def _update_completion_time(self) -> None:
        """Update the last completion query time"""
        self.last_completion_time = time.time()

    def _execute_ssh_command(self, remote_command: str) -> subprocess.CompletedProcess | None:
        """Execute a command on the remote host via SSH and return the result"""
        if not self.conn or not self.connection_name:
            display_error("No active connection")
            return None

        try:
            cmd = [
                "ssh",
                "-o",
                f"ControlPath={self.socket_path}",
                f"{self.conn.username}@{self.conn.host}",
                remote_command,
            ]

            # Log the command execution with connection name
            log_scp_command(self.connection_name, remote_command)

            result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603  # args are constructed from validated SSH parameters
            return result
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover - SSH error handling
            display_error(f"SSH command error: {str(e)}")
            return None

    def get_prompt_text(self) -> HTML:
        """Get the prompt text with HTML formatting"""
        conn_name = self.connection_name or "none"
        return HTML(
            f"<prompt>scp {conn_name}</prompt>:<path>{self.current_remote_dir}</path>"
            f" <brackets>[</brackets><brackets>↓</brackets><dir1>{self.local_download_dir}</dir1> <brackets>|</brackets> <brackets>↑</brackets><dir2>{self.local_upload_dir}</dir2><brackets>]</brackets><brackets>></brackets> "
        )

    def run(self) -> None:
        """Run the SCP mode interface"""
        # If no connection is selected, prompt for selection
        if not self.connection_name:
            if not self._select_connection():
                return
            # Set socket path after successful connection selection
            self.socket_path = f"/tmp/{self.connection_name}"  # noqa: S108  # /tmp/lazyssh is the documented runtime directory

        # Connect to the selected SSH session if not already connected
        if not self.conn and not self.connect():
            return

        while True:  # pragma: no cover - interactive loop
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
            except Exception as e:  # top-level command loop; genuinely unknown errors possible
                display_error(f"Error: {str(e)}")

    def _select_connection(self) -> bool:
        """Prompt user to select an SSH connection"""
        connections = []
        connection_map = {}

        # Build a map of connection names to actual connections
        for socket_path, conn in self.connections.items():
            conn_name = Path(socket_path).name
            connections.append(conn_name)
            connection_map[conn_name] = conn

        if not connections:
            display_error("No active SSH connections available")
            display_info("Create an SSH connection first using 'lazyssh' command")
            return False

        console.print(
            "\n[header]Select an SSH connection for SCP mode:[/header]"
        )  # pragma: no cover
        for i, name in enumerate(connections, 1):  # pragma: no cover
            conn = connection_map[name]
            console.print(
                f"[info]{i}.[/info] [success]{name}[/success] [dim]([/dim][variable]{conn.username}[/variable][operator]@[/operator][highlight]{conn.host}[/highlight][dim])[/dim]"
            )

        # Use Rich's prompt for the connection selection
        try:  # pragma: no cover
            choice = IntPrompt.ask("Enter selection (number)", default=1)
            if 1 <= choice <= len(connections):
                self.connection_name = connections[choice - 1]
                return True
            display_error("Invalid selection")
            return False
        except (KeyboardInterrupt, EOFError):  # pragma: no cover - user interrupt
            return False

    def _resolve_remote_path(self, path: str) -> str:
        """Resolve a remote path relative to the current remote directory"""
        if not path:
            return self.current_remote_dir or ""

        # Handle absolute paths as is
        if path.startswith("/"):
            return path

        # Handle paths with ~ for home directory
        if path.startswith("~"):  # pragma: no cover - remote path expansion
            # Execute command to expand ~ on the remote server
            result = self._execute_ssh_command(f"echo {shlex.quote(path)}")
            if result and result.returncode == 0:
                expanded_path = result.stdout.strip()
                return expanded_path if expanded_path else path
            return path

        # Join with current directory
        if self.current_remote_dir:
            return str(Path(self.current_remote_dir) / path)
        return path  # pragma: no cover - fallback

    def _resolve_local_path(
        self, path: str, for_upload: bool = False
    ) -> str:  # pragma: no cover - local path resolution
        """Resolve a local path relative to the local download or upload directory"""
        if not path:
            base_dir = self.local_upload_dir if for_upload else self.local_download_dir
            return base_dir if base_dir else ""
        if Path(path).is_absolute():
            return path

        # Join with local download or upload directory
        base_dir = self.local_upload_dir if for_upload else self.local_download_dir
        if base_dir:
            return str(Path(base_dir) / path)
        return path

    def _get_scp_command(self, source: str, destination: str) -> list[str]:
        """Build the SCP command"""
        return ["scp", "-q", "-o", f"ControlPath={self.socket_path}", source, destination]

    def _get_file_size(
        self, path: str, is_remote: bool = False
    ) -> int:  # pragma: no cover - file size retrieval
        """Get the size of a file in bytes"""
        try:
            if is_remote and self.conn:
                # Get size of remote file
                result = self._execute_ssh_command(f"stat -c %s {shlex.quote(path)}")
                if result and result.returncode == 0:
                    return int(result.stdout.strip())
                return 0
            # Get size of local file
            return Path(path).stat().st_size
        except (OSError, subprocess.SubprocessError, ValueError):
            return 0

    def cmd_put(self, args: list[str]) -> None:
        """Upload a file to the remote host"""
        if not self.conn or not self.check_connection():
            display_error("No active connection")
            return

        if len(args) < 1:  # pragma: no cover - usage error
            display_error("Usage: put <local_file_path> [remote_file_path]")
            return

        local_path = args[0]

        # Check if the local file exists
        local_file = Path(local_path)
        if not local_file.exists():
            display_error(f"Local file not found: {local_path}")
            return

        # Get the file size before upload
        file_size = local_file.stat().st_size

        # Determine the remote path
        remote_path = args[1] if len(args) > 1 else None

        if not remote_path:
            # Use the filename from the local path
            filename = Path(local_path).name
            remote_path = f"{self.current_remote_dir}/{filename}"
        else:
            # Resolve relative paths to absolute paths
            remote_path = self._resolve_remote_path(remote_path)

        try:
            # Execute the SCP command
            remote_dest = f"{self.conn.username}@{self.conn.host}:{remote_path}"
            cmd = self._get_scp_command(local_path, remote_dest)

            # Show a progress bar for upload
            display_info(f"Uploading {local_path} to {remote_path}")

            # Start timing the upload
            start_time = time.time()

            # Create a progress bar with enhanced styling
            with create_progress_bar(self.console) as progress:
                # Convert bytes to MB for display
                file_size_mb = file_size / (1024 * 1024)
                upload_task = progress.add_task(
                    f"[info]Uploading {truncate_filename(Path(local_path).name)}",
                    total=file_size_mb,
                )

                # Start the upload process
                process = subprocess.Popen(  # noqa: S603  # args are constructed from validated SSH parameters
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Since SCP doesn't provide progress feedback, we monitor remote file size
                # We'll poll for completion instead with optimized timing
                last_update_time = time.time()
                update_interval = 0.1  # Update every 100ms for uploads

                while process.poll() is None:  # pragma: no cover - upload progress loop
                    current_time = time.time()
                    # Only update if enough time has passed
                    if current_time - last_update_time >= update_interval:
                        # Just update time-based progress as an approximation
                        # Actual progress can't be determined for uploads without server feedback
                        elapsed = time.time() - start_time
                        # Estimate progress based on time and file size
                        # Using a reasonable upload rate estimate (10MB/s)
                        est_progress = min(elapsed * 10, file_size_mb)  # Cap at total size
                        progress.update(upload_task, completed=est_progress)
                        last_update_time = current_time
                    else:
                        # Sleep for shorter intervals to reduce CPU usage
                        time.sleep(0.01)

                # Process is complete, set to 100%
                progress.update(upload_task, completed=file_size_mb)

                # Get result
                result = process.wait()
                stderr = process.stderr.read() if process.stderr else ""

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            elapsed_str = f"{elapsed_time:.1f} seconds"
            if elapsed_time > 60:  # pragma: no cover - elapsed time formatting
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                elapsed_str = f"{minutes}m {seconds}s"

            if result == 0:
                # Log the file transfer with size
                if self.connection_name:
                    log_file_transfer(
                        connection_name=str(self.connection_name) if self.connection_name else "",
                        source=local_path,
                        destination=remote_path,
                        size=file_size,
                        operation="upload",
                    )
                    # Update transfer stats
                    update_transfer_stats(self.connection_name, 1, file_size)

                # Invalidate cache for the target directory
                target_dir = str(Path(remote_path).parent)
                self._invalidate_cache(target_dir)

                display_success(
                    f"Uploaded {local_path} ({format_size(file_size)}) in {elapsed_str}"
                )
            else:  # pragma: no cover - upload error
                display_error(f"Upload failed: {stderr}")
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover - upload exception
            display_error(f"Upload error: {str(e)}")

    def cmd_get(self, args: list[str]) -> None:
        """Download a file from the remote host"""
        if not self.conn or not self.check_connection():
            display_error("No active connection")
            return

        if len(args) < 1:  # pragma: no cover - usage error
            display_error("Usage: get <remote_file_path> [local_file_path]")
            return

        remote_path = args[0]

        # If remote path is relative, make it absolute based on current remote dir
        if not remote_path.startswith("/"):
            remote_path = f"{self.current_remote_dir}/{remote_path}"

        # Determine the local path
        local_path = args[1] if len(args) > 1 else None

        if not local_path and self.local_download_dir:
            # Use the filename from the remote path
            filename = Path(remote_path).name
            local_path = str(Path(self.local_download_dir) / filename)
        elif not local_path:
            display_error("Local download directory not set")
            return

        # Check if the remote file exists and get its size
        try:
            # Get file size before download to log it properly
            size_cmd = f"stat -c %s {shlex.quote(remote_path)}"
            size_result = self._execute_ssh_command(size_cmd)
            file_size = 0
            if size_result and size_result.returncode == 0:
                file_size = int(size_result.stdout.strip())
            else:  # pragma: no cover - remote file error
                display_error(f"File not found or cannot access: {remote_path}")
                return
        except (
            OSError,
            subprocess.SubprocessError,
            ValueError,
        ) as e:  # pragma: no cover - exception handling
            display_error(f"Error checking file: {str(e)}")
            return

        # Display file information in a table like mget does
        display_info("Found 1 matching file:")

        # Create a Rich table for listing the file with standardized styling
        table = create_standard_table()

        # Add columns with consistent styling
        table.add_column("Filename", style="table.row")
        table.add_column("Size", justify="right", style="accent")

        # Format size in human-readable format
        human_size = self._format_file_size(file_size)
        table.add_row(Path(remote_path).name, human_size)

        # Display the table
        console.print(table)

        # Show total download size
        human_total = self._format_file_size(file_size)
        display_info(f"Total download size: [success]{human_total}[/]")

        # Confirm download using Rich's Confirm.ask for a color-coded prompt
        if not Confirm.ask(f"Download [info]1[/] file to [highlight]{self.local_download_dir}[/]?"):
            display_info("Download cancelled")
            return

        # Create parent directory if it doesn't exist
        local_dir = Path(str(local_path)).parent if local_path else None
        if local_dir and not local_dir.exists():  # pragma: no cover - directory creation
            try:
                local_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                display_error(f"Failed to create directory {local_dir}: {str(e)}")
                return

        try:
            # Execute the SCP command
            remote_source = f"{self.conn.username}@{self.conn.host}:{remote_path}"
            cmd = self._get_scp_command(remote_source, str(local_path))

            # Show a progress bar for download
            display_info(f"Downloading {remote_path} to {local_path}")

            # Start timing the download
            start_time = time.time()

            # Create a progress bar with enhanced styling
            with create_progress_bar(self.console) as progress:
                # Convert bytes to MB for display
                file_size_mb = file_size / (1024 * 1024)
                download_task = progress.add_task(
                    f"[info]Downloading {truncate_filename(Path(remote_path).name)}",
                    total=file_size_mb,
                )

                # Start the download process
                process = subprocess.Popen(  # noqa: S603  # args are constructed from validated SSH parameters
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Poll the local file size to show progress with optimized caching
                local_size = 0
                last_update_time = time.time()
                file_exists = False
                # Start with longer intervals for large files
                base_interval = 0.1 if file_size > 100 * 1024 * 1024 else 0.05
                update_interval = base_interval
                # Initialize local_file_path before the loop so it's available after
                local_file_path = Path(str(local_path)) if local_path else None

                while process.poll() is None:  # pragma: no cover - download progress loop
                    current_time = time.time()
                    # Only check file size if enough time has passed
                    if current_time - last_update_time >= update_interval:
                        if local_file_path:
                            # Only check existence if we haven't seen the file yet
                            if not file_exists:
                                file_exists = local_file_path.exists()

                            if file_exists:
                                try:
                                    new_size = local_file_path.stat().st_size
                                    if new_size > local_size:
                                        local_size = new_size
                                        # Convert to MB for the progress bar
                                        progress.update(
                                            download_task, completed=local_size / (1024 * 1024)
                                        )

                                        # Reduce polling interval as file grows
                                        if local_size > 0 and file_size > 0:
                                            progress_ratio = local_size / file_size
                                            if progress_ratio > 0.5:
                                                update_interval = base_interval * 0.5
                                            elif progress_ratio > 0.1:
                                                update_interval = base_interval * 0.7
                                except (OSError, FileNotFoundError):
                                    pass  # Ignore file access errors during download
                        last_update_time = current_time
                    else:
                        # Sleep for shorter intervals to reduce CPU usage
                        time.sleep(0.01)

                # Process is complete, set to 100% if we know the file size
                if file_size > 0:
                    progress.update(download_task, completed=file_size_mb)
                else:  # pragma: no cover - unknown file size completion
                    # If we didn't know the file size in advance, get it now
                    try:
                        final_size = (
                            file_size  # Default to file_size if local file can't be accessed
                        )
                        if local_file_path and local_file_path.exists():
                            final_size = local_file_path.stat().st_size
                            progress.update(
                                download_task,
                                completed=final_size / (1024 * 1024),
                                total=final_size / (1024 * 1024),
                            )
                            file_size = final_size  # Update file_size for logging
                    except (OSError, FileNotFoundError):
                        pass

                # Get result
                result = process.wait()
                stderr = process.stderr.read() if process.stderr else ""

            # Calculate elapsed time
            elapsed_time = time.time() - start_time
            elapsed_str = f"{elapsed_time:.1f} seconds"
            if elapsed_time > 60:  # pragma: no cover - elapsed time formatting
                minutes = int(elapsed_time // 60)
                seconds = int(elapsed_time % 60)
                elapsed_str = f"{minutes}m {seconds}s"

            if result == 0:  # pragma: no cover - successful download
                # Calculate final file size for display and logging
                final_size = file_size  # Default to file_size if local file can't be accessed
                if local_file_path and local_file_path.exists():
                    final_size = local_file_path.stat().st_size
                    file_size = final_size

                # Log the file transfer
                if self.connection_name:
                    log_file_transfer(
                        connection_name=str(self.connection_name) if self.connection_name else "",
                        source=remote_path,
                        destination=str(local_path) if local_path else "",
                        size=file_size,
                        operation="download",
                    )
                    # Update transfer stats
                    update_transfer_stats(self.connection_name, 1, file_size)

                display_success(
                    f"Downloaded {remote_path} ({format_size(file_size)}) in {elapsed_str}"
                )
            else:  # pragma: no cover - download error
                display_error(f"Download failed: {stderr}")
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover - download exception
            display_error(f"Download error: {str(e)}")

    def cmd_ls(self, args: list[str]) -> bool:
        """List contents of a remote directory"""
        path = self.current_remote_dir
        if args:
            path = self._resolve_remote_path(args[0])

        try:
            # Use ls -la command via SSH for detailed listing
            result = self._execute_ssh_command(f"ls -la {shlex.quote(path)}")

            if not result or result.returncode != 0:
                display_error(
                    f"Error listing directory: {result.stderr if result else 'Unknown error'}"
                )
                return False

            # Format and display the output
            output = result.stdout.strip()
            if not output:  # pragma: no cover - empty directory
                display_info(f"Directory [highlight]{path}[/] is empty")
                return True

            display_info(f"Contents of [highlight]{path}[/]:")

            # Create a Rich table with standardized styling
            table = create_standard_table()

            # Add columns with consistent styling
            table.add_column("Permissions", style="dim")
            table.add_column("Links", justify="right", style="dim")
            table.add_column("Owner", style="table.row")
            table.add_column("Group", style="table.row")
            table.add_column("Size", justify="right", style="accent")
            table.add_column("Modified", style="info")
            table.add_column("Name", style="table.row")

            # Parse ls output and add rows
            lines = output.split("\n")
            for line in lines:
                # Skip total line
                if line.startswith("total "):  # pragma: no cover - skip total line
                    continue

                # Parse the ls -la output, which follows a standard format
                # Example: -rw-r--r-- 1 username group 12345 Jan 01 12:34 filename
                parts = line.split(maxsplit=8)
                if len(parts) < 9:
                    continue

                perms, links, owner, group, size_str, date1, date2, date3, name = (
                    parts  # pragma: no cover - ls output parsing
                )

                # Format the size to be human readable  # pragma: no cover
                try:  # pragma: no cover
                    size_bytes = int(size_str)  # pragma: no cover
                    human_size = self._format_file_size(size_bytes)  # pragma: no cover
                except ValueError:  # pragma: no cover
                    human_size = size_str  # pragma: no cover

                # Format the date in a consistent way - attempt to convert to a standard format  # pragma: no cover
                try:  # pragma: no cover
                    # Try to parse the date parts into a consistent format  # pragma: no cover
                    # Handle different date formats from ls  # pragma: no cover
                    date_str = f"{date1} {date2} {date3}"  # pragma: no cover

                    # Parse the date - try different formats  # pragma: no cover
                    date_formats = [  # pragma: no cover
                        "%b %d %Y",  # Jan 01 2023  # pragma: no cover
                        "%b %d %H:%M",  # Jan 01 12:34  # pragma: no cover
                        "%Y-%m-%d %H:%M",  # 2023-01-01 12:34  # pragma: no cover
                    ]  # pragma: no cover

                    parsed_date = None  # pragma: no cover
                    for fmt in date_formats:  # pragma: no cover
                        try:  # pragma: no cover
                            parsed_date = time.strptime(date_str, fmt)  # pragma: no cover
                            break  # pragma: no cover
                        except ValueError:  # pragma: no cover
                            continue  # pragma: no cover

                    if parsed_date:  # pragma: no cover
                        # Format in a consistent way  # pragma: no cover
                        date = time.strftime("%b %d %Y %H:%M", parsed_date)  # pragma: no cover
                    else:  # pragma: no cover
                        # Fall back to original if parsing fails  # pragma: no cover
                        date = date_str  # pragma: no cover
                except (ValueError, OverflowError):  # pragma: no cover
                    # If any date-parsing error, just use the original  # pragma: no cover
                    date = f"{date1} {date2} {date3}"  # pragma: no cover

                # Color the filename based on type  # pragma: no cover
                name_text = Text(name)  # pragma: no cover
                if perms.startswith("d"):  # Directory  # pragma: no cover
                    name_text.stylize("bold blue")  # pragma: no cover
                elif perms.startswith("l"):  # Symlink  # pragma: no cover
                    name_text.stylize("cyan")  # pragma: no cover
                elif (
                    perms.startswith("-")
                    and (  # pragma: no cover
                        "x" in perms[1:4]
                        or "x" in perms[4:7]
                        or "x" in perms[7:10]  # pragma: no cover
                    )
                ):  # Executable  # pragma: no cover
                    name_text.stylize("green")  # pragma: no cover

                table.add_row(
                    perms, links, owner, group, human_size, date, name_text
                )  # pragma: no cover

            # Display the table
            console.print(table)

            return True
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover
            display_error(f"Error listing directory: {str(e)}")
            return False

    def cmd_cd(self, args: list[str]) -> bool:
        """Change remote directory"""
        if not args:
            display_error("Usage: cd <remote_path>")
            return False

        target_dir = self._resolve_remote_path(args[0])

        # Check if we're already in the target directory
        if target_dir == self.current_remote_dir:  # pragma: no cover - same directory
            display_info(f"Already in directory: {self.current_remote_dir}")
            return True

        try:
            # Check if directory exists and is accessible
            result = self._execute_ssh_command(f"cd {shlex.quote(target_dir)} && pwd")

            if not result or result.returncode != 0:
                display_error(
                    f"Failed to change directory: {result.stderr if result else 'Directory may not exist'}"
                )
                return False

            # Update current directory
            self.current_remote_dir = result.stdout.strip()

            # Invalidate all cache on directory change
            self._invalidate_cache()

            display_success(f"Changed to directory: {self.current_remote_dir}")
            return True
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover - exception handling
            display_error(f"Failed to change directory: {str(e)}")
            return False

    def cmd_pwd(self, args: list[str]) -> bool:
        """Print current remote directory"""
        display_info(f"Current remote directory: [number]{self.current_remote_dir}[/number]")
        return True

    def cmd_mget(self, args: list[str]) -> bool:
        """Download multiple files from the remote server using wildcards"""
        if not args:
            display_error("Usage: mget <pattern>")
            return False

        if not self.conn:  # pragma: no cover - no connection
            display_error("Not connected to an SSH server")
            return False

        pattern = args[0]

        try:
            matched_files = self._mget_discover_files(pattern)
            if matched_files is None:
                return False

            file_sizes, total_size = self._mget_calculate_size(matched_files)

            # Confirm download using Rich's Confirm.ask for a color-coded prompt
            if not Confirm.ask(
                f"Download [info]{len(matched_files)}[/] files to [highlight]{self.local_download_dir}[/]?"
            ):
                display_info("Download cancelled")
                return False

            return self._mget_download(matched_files, file_sizes, total_size)
        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover - mget exception
            display_error(f"Error during mget: {str(e)}")
            return False

    def _mget_discover_files(self, pattern: str) -> list[str] | None:
        """Find files matching the given pattern on the remote server.

        Returns the list of matched filenames, or None on error/no matches.
        """
        result = self._execute_ssh_command(
            f"find {self.current_remote_dir} -maxdepth 1 -type f -name '{pattern}' -printf '%f\\n'"
        )

        if not result or result.returncode != 0:  # pragma: no cover - find error
            display_error(f"Error finding files: {result.stderr if result else 'Unknown error'}")
            return None

        matched_files = [f for f in result.stdout.strip().split("\n") if f]

        if not matched_files:
            display_error(f"No files match pattern: {pattern}")
            return None

        return matched_files

    def _mget_calculate_size(self, matched_files: list[str]) -> tuple[dict[str, int], int]:
        """Query remote file sizes, display a summary table, and return sizes.

        Returns a tuple of (file_sizes dict, total_size).
        """
        total_size = 0
        file_sizes: dict[str, int] = {}

        display_info(f"Found {len(matched_files)} matching files:")

        table = create_standard_table()
        table.add_column("Filename", style="table.row")
        table.add_column("Size", justify="right", style="accent")

        # Batch file size queries for better performance
        file_paths = [
            shlex.quote(f"{self.current_remote_dir}/{filename}") for filename in matched_files
        ]
        size_command = f"stat -c '%n %s' {' '.join(file_paths)}"

        size_result = self._execute_ssh_command(size_command)
        if size_result and size_result.returncode == 0:
            for line in size_result.stdout.strip().split("\n"):
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) == 2:
                        filename_with_path = parts[0]
                        size_str = parts[1]
                        filename = filename_with_path.split("/")[-1]
                        try:
                            size = int(size_str)
                            file_sizes[filename] = size
                            total_size += size
                            human_size = self._format_file_size(size)
                            table.add_row(filename, human_size)
                        except ValueError:  # pragma: no cover - parse error
                            table.add_row(filename, "unknown size")
                    else:  # pragma: no cover - malformed output
                        filename = filename_with_path.split("/")[-1]
                        table.add_row(filename, "unknown size")
        else:  # pragma: no cover - batch query fallback
            for filename in matched_files:
                quoted_path = shlex.quote(f"{self.current_remote_dir}/{filename}")
                size_result = self._execute_ssh_command(f"stat -c %s {quoted_path}")
                if size_result and size_result.returncode == 0:
                    try:
                        size = int(size_result.stdout.strip())
                        file_sizes[filename] = size
                        total_size += size
                        human_size = self._format_file_size(size)
                        table.add_row(filename, human_size)
                    except ValueError:
                        table.add_row(filename, "unknown size")
                else:
                    table.add_row(filename, "unknown size")

        console.print(table)

        human_total = self._format_file_size(total_size)
        display_info(f"Total download size: [success]{human_total}[/]")

        return file_sizes, total_size

    def _mget_download(
        self,
        matched_files: list[str],
        file_sizes: dict[str, int],
        total_size: int,
    ) -> bool:
        """Download the matched files with progress tracking.

        Returns True if at least one file was downloaded successfully.
        """
        if not self.conn:  # pragma: no cover - no connection
            return False

        # Ensure download directory exists with proper permissions
        download_dir_path = Path(self.local_download_dir) if self.local_download_dir else Path(".")
        if not download_dir_path.exists():  # pragma: no cover - directory creation
            download_dir_path.mkdir(parents=True, exist_ok=True)
            download_dir_path.chmod(0o755)

        success_count = 0
        total_downloaded_bytes = 0
        start_time = time.time()

        with create_multi_file_progress_bar(self.console) as progress:
            overall_task = progress.add_task("Overall progress", total=total_size)

            for _idx, filename in enumerate(matched_files):
                remote_file = str(Path(self.current_remote_dir) / filename)
                local_file = (
                    str(Path(str(self.local_download_dir)) / filename)
                    if self.local_download_dir
                    else filename
                )
                file_size = file_sizes.get(filename, 0)

                try:
                    file_task = progress.add_task(
                        f"[info]Downloading {truncate_filename(filename)}", total=file_size
                    )

                    remote_path = f"{self.conn.username}@{self.conn.host}:{remote_file}"
                    cmd = self._get_scp_command(remote_path, local_file)

                    process = subprocess.Popen(  # noqa: S603  # args are constructed from validated SSH parameters
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )

                    time.sleep(0.1)

                    downloaded_file = Path(local_file)
                    last_size = 0
                    last_update_time = time.time()
                    file_exists = False
                    base_interval = (
                        0.1 if file_size > 100 * 1024 * 1024 else 0.05
                    )  # 100MB threshold
                    update_interval = base_interval

                    while process.poll() is None:  # pragma: no cover - download loop
                        current_time = time.time()
                        if current_time - last_update_time >= update_interval:
                            if not file_exists:
                                file_exists = downloaded_file.exists()

                            if file_exists:
                                try:
                                    current_size = downloaded_file.stat().st_size
                                    progress.update(file_task, completed=current_size)

                                    if current_size > last_size:
                                        progress.update(
                                            overall_task, advance=current_size - last_size
                                        )
                                        last_size = current_size

                                        if current_size > 0 and file_size > 0:
                                            progress_ratio = current_size / file_size
                                            if progress_ratio > 0.5:
                                                update_interval = base_interval * 0.5
                                            elif progress_ratio > 0.1:
                                                update_interval = base_interval * 0.7
                                except (OSError, FileNotFoundError):
                                    pass

                            last_update_time = current_time
                        else:
                            time.sleep(0.01)

                    final_size = file_size
                    if downloaded_file.exists():  # pragma: no cover - file check
                        final_size = downloaded_file.stat().st_size

                    progress.update(file_task, completed=final_size)

                    if final_size > last_size:
                        progress.update(overall_task, advance=final_size - last_size)

                    process_result = process.wait()
                    stderr = process.stderr.read() if process.stderr else ""

                    if process_result != 0:  # pragma: no cover - download error
                        display_error(f"Failed to download {filename}: {stderr}")
                    else:
                        success_count += 1
                        log_file_transfer(
                            connection_name=(
                                str(self.connection_name) if self.connection_name else ""
                            ),
                            source=remote_file,
                            destination=local_file,
                            size=final_size,
                            operation="download",
                        )
                        total_downloaded_bytes += final_size

                except (
                    OSError,
                    subprocess.SubprocessError,
                ) as e:  # pragma: no cover - download exception
                    display_error(f"Failed to download {filename}: {str(e)}")

        elapsed_time = time.time() - start_time
        elapsed_str = f"{elapsed_time:.1f} seconds"
        if elapsed_time > 60:  # pragma: no cover - elapsed time formatting
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            elapsed_str = f"{minutes}m {seconds}s"

        if success_count > 0:
            if self.connection_name:
                update_transfer_stats(
                    str(self.connection_name), success_count, total_downloaded_bytes
                )

            display_success(  # pragma: no cover - success message
                f"Successfully downloaded [info]{success_count}[/] of [info]{len(matched_files)}[/] files ([success]{self._format_file_size(total_downloaded_bytes)}[/] in [header]{elapsed_str}[/])"
            )

        return success_count > 0

    def cmd_local(self, args: list[str]) -> bool:
        """Set or display local download and upload directories"""
        if not args:
            display_info(
                f"Current local download directory: [number]{self.local_download_dir}[/number]"
            )
            display_info(
                f"Current local upload directory: [number]{self.local_upload_dir}[/number]"
            )
            return True

        if len(args) >= 2 and args[0] in ["download", "upload"]:
            # Handle specific directory type
            dir_type = args[0]
            new_path = args[1]

            try:
                # Resolve path (make absolute if needed)
                path_obj = Path(new_path)
                if not path_obj.is_absolute():  # pragma: no cover - relative path
                    path_obj = path_obj.absolute()

                new_path = str(path_obj)

                # Create directory if it doesn't exist
                if not path_obj.exists():  # pragma: no cover - directory creation
                    display_info(f"Local directory does not exist, creating: {new_path}")
                    path_obj.mkdir(parents=True, exist_ok=True)
                    # Ensure proper permissions
                    path_obj.chmod(0o755)
                elif not path_obj.is_dir():  # pragma: no cover - not a directory
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
            except OSError as e:  # pragma: no cover - exception
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
                if not path_obj.exists():  # pragma: no cover - directory creation
                    display_info(f"Local directory does not exist, creating: {new_path}")
                    path_obj.mkdir(parents=True, exist_ok=True)
                    # Ensure proper permissions
                    path_obj.chmod(0o755)
                elif not path_obj.is_dir():  # pragma: no cover - not a directory
                    display_error(f"Path exists but is not a directory: {new_path}")
                    return False

                self.local_download_dir = new_path
                display_success(f"Local download directory set to: {new_path}")
                display_info(
                    "Note: Use 'local download <path>' or 'local upload <path>' to set specific directories"
                )
                return True
            except OSError as e:  # pragma: no cover - exception
                display_error(f"Failed to set local directory: {str(e)}")
                return False

    def cmd_help(self, args: list[str]) -> bool:
        """Display help information"""
        if args:
            cmd = args[0].lower()
            if cmd == "put":
                display_info("[header]\nUpload a file to the remote server:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]put[/highlight] [number]<local_file>[/number] [[number]<remote_file>[/number]]"
                )
                display_info(
                    "If [number]<remote_file>[/number] is not specified, the file will be uploaded with the same name"
                )
                display_info(
                    "[dim]Local files are read from the upload directory shown in the prompt[/dim]"
                )
                display_info(
                    "[dim]Use tab completion to see available files in the upload directory[/dim]"
                )
            elif cmd == "get":
                display_info("[header]\nDownload a file from the remote server:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]get[/highlight] [number]<remote_file>[/number] [[number]<local_file>[/number]]"
                )
                display_info(
                    "If [number]<local_file>[/number] is not specified, the file will be downloaded to the current local directory"
                )
            elif cmd == "ls":
                display_info("[header]\nList files in a remote directory:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]ls[/highlight] [[number]<remote_path>[/number]]"
                )
                display_info(
                    "If [number]<remote_path>[/number] is not specified, lists the current remote directory"
                )
            elif cmd == "pwd":
                display_info("[header]\nShow current remote working directory:[/header]")
                display_info("[number]Usage:[/number] [highlight]pwd[/highlight]")
            elif cmd == "cd":
                display_info("[header]\nChange remote working directory:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]cd[/highlight] [number]<remote_path>[/number]"
                )
            elif cmd == "local":
                display_info(
                    "[header]\nSet or display local download and upload directories:[/header]"
                )
                display_info(
                    "[number]Usage:[/number] [highlight]local[/highlight] [[number]<local_path>[/number]]"
                )
                display_info(
                    "If [number]<local_path>[/number] is not specified, displays both the download and upload directories"
                )
                display_info("[highlight]To set a specific directory type:[/highlight]")
                display_info(
                    "  [highlight]local download[/highlight] [number]<path>[/number] - Set the download directory"
                )
                display_info(
                    "  [highlight]local upload[/highlight] [number]<path>[/number]   - Set the upload directory"
                )
            elif cmd == "lcd":
                display_info("[header]\nChange local download directory:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]lcd[/highlight] [number]<local_path>[/number]"
                )
                display_info("Change the directory where files are downloaded to")
            elif cmd == "exit":
                display_info("[header]\nExit SCP mode and return to lazyssh prompt:[/header]")
                display_info("[number]Usage:[/number] [highlight]exit[/highlight]")
            elif cmd == "lls":
                display_info("[header]\nList contents of the local download directory:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]lls[/highlight] [[number]<local_path>[/number]]"
                )
                display_info(
                    "If [number]<local_path>[/number] is not specified, lists the current local download directory"
                )
                display_info("Shows file sizes and directory summary information")
            elif cmd == "tree":
                display_info(
                    "[header]\nDisplay a tree view of the remote directory structure:[/header]"
                )
                display_info(
                    "[number]Usage:[/number] [highlight]tree[/highlight] [[number]<remote_path>[/number]]"
                )
                display_info(
                    "If [number]<remote_path>[/number] is not specified, displays the current remote directory"
                )
            elif cmd == "debug":
                display_info("[header]\nToggle debug logging to console:[/header]")
                display_info(
                    "[number]Usage:[/number] [highlight]debug[/highlight] [[number]on|off|enable|disable|true|false|1|0[/number]]"
                )
                display_info("\n[header]Description:[/header]")
                display_info("  Toggles debug logging output to the console.")
                display_info(
                    "  Logs are always saved to /tmp/lazyssh/logs regardless of this setting."
                )
                display_info("  When enabled, all log messages will be displayed in the console.")
                display_info("\n[header]Examples:[/header]")
                display_info(
                    "  [success]debug[/success]      [dim]# Toggle debug mode (on if off, off if on)[/dim]"
                )
                display_info(
                    "  [success]debug on[/success]   [dim]# Explicitly enable debug mode[/dim]"
                )
                display_info(
                    "  [success]debug off[/success]  [dim]# Explicitly disable debug mode[/dim]"
                )
            else:
                display_error(f"Unknown command: {cmd}")
                self.cmd_help([])
            return True

        display_info("[header]\nAvailable SCP mode commands:[/header]")
        display_info("  [highlight]put[/highlight]     - Upload a file to the remote server")
        display_info("  [highlight]get[/highlight]     - Download a file from the remote server")
        display_info("  [highlight]ls[/highlight]      - List files in a remote directory")
        display_info(
            "  [highlight]lls[/highlight]     - List files in the local download directory"
        )
        display_info(
            "  [highlight]tree[/highlight]    - Display a tree view of the remote directory structure"
        )
        display_info("  [highlight]pwd[/highlight]     - Show current remote working directory")
        display_info("  [highlight]cd[/highlight]      - Change remote working directory")
        display_info("  [highlight]lcd[/highlight]     - Change local download directory")
        display_info("  [highlight]local[/highlight]   - Set or display local download directory")
        display_info("  [highlight]debug[/highlight]   - Toggle debug logging to console")
        display_info("  [highlight]exit[/highlight]    - Exit SCP mode")
        display_info(
            "  [highlight]help[/highlight]    - Show this help message or help for a specific command"
        )
        display_info(
            "\n[dim]Use 'help [number]<command>[/number]' for detailed help on a specific command[/dim]"
        )
        return True

    def cmd_exit(self, args: list[str]) -> bool:
        """Exit SCP mode"""
        return True

    def _format_file_size(self, size_bytes: int) -> str:
        """Format a file size in bytes to a human-readable string"""
        return format_size(size_bytes)

    def cmd_lls(self, args: list[str]) -> bool:
        """List contents of the local download directory with total size and file count"""
        try:
            # Determine which directory to list
            target_dir_path = (
                Path(str(self.local_download_dir)) if self.local_download_dir else Path(".")
            )
            if args:
                # Allow listing other directories relative to the download dir
                path = args[0]
                path_obj = Path(path)
                if path_obj.is_absolute():  # pragma: no cover - absolute path
                    target_dir_path = path_obj
                else:
                    target_dir_path = (  # pragma: no cover - relative path
                        Path(str(self.local_download_dir) if self.local_download_dir else ".")
                        / path
                    )

            # Check if directory exists
            if not target_dir_path.exists() or not target_dir_path.is_dir():
                display_error(f"Directory not found: {target_dir_path}")
                return False

            display_info(f"Contents of [highlight]{target_dir_path}[/]:")

            # Create a Rich table with standardized styling
            table = create_standard_table()

            # Add columns with consistent styling - removed Type column
            table.add_column("Permissions", style="dim")
            table.add_column("Size", justify="right", style="accent")
            table.add_column("Modified", style="info")
            table.add_column("Name", style="table.row")

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

                if item.is_dir():  # pragma: no cover - display formatting
                    dir_count += 1
                    name_text = Text(f"{item.name}/")
                    name_text.stylize("bold blue")
                    size_text = "--"
                    table.add_row(perms, size_text, mtime, name_text)
                else:  # pragma: no cover - display formatting
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
            console.print(table)

            # Show summary footer
            human_total = self._format_file_size(total_size)
            console.print(
                f"\nTotal: [info]{file_count}[/] files, [info]{dir_count}[/] directories, [success]{human_total}[/] total size"
            )

            return True

        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover
            display_error(f"Error listing directory: {str(e)}")
            return False

    def cmd_tree(self, args: list[str]) -> bool:
        """Display a tree view of the remote directory structure"""
        try:
            # Determine which remote directory to show
            if args:  # pragma: no cover - tree with path arg
                remote_path = self._resolve_remote_path(args[0])
            else:
                remote_path = self.current_remote_dir

            # First check if the path exists and is a directory
            check_cmd = f"[ -d {shlex.quote(remote_path)} ] && echo 'DIR_EXISTS' || echo 'NOT_DIR'"
            result = self._execute_ssh_command(check_cmd)
            if not result or result.returncode != 0 or "NOT_DIR" in result.stdout:
                display_error(f"Remote path is not a directory: {remote_path}")
                return False

            # Get listing of files recursively with find, including file type information
            # The format string will give us: <type><path> where type is 'd' for directory, 'f' for file
            find_cmd = f"""find {shlex.quote(remote_path)} \\( -type f -printf "f%p\\n" , -type d -printf "d%p\\n" \\) | sort"""
            result = self._execute_ssh_command(find_cmd)

            if not result or result.returncode != 0:  # pragma: no cover - find error
                display_error(
                    f"Failed to list directory contents: {result.stderr if result else 'Unknown error'}"
                )
                return False

            # Create the root tree node
            tree = Tree(f"[header]{remote_path}[/]")
            path_to_node = {remote_path: tree}

            # Track statistics
            file_count = 0
            dir_count = 1  # Start with 1 for the root directory

            # Process each entry from the find results, which already includes type information
            for line in result.stdout.strip().split("\n"):  # pragma: no cover - tree display
                if not line or len(line) <= 1:
                    continue

                # Extract type and path
                entry_type = line[0]
                path = line[1:]

                # Skip the root path itself
                if path == remote_path:  # pragma: no cover - skip root
                    continue

                # Determine the parent path
                parent_path = str(Path(path).parent)

                # Skip if parent not found (shouldn't happen with sorted find output)
                if parent_path not in path_to_node:
                    continue

                # Get the parent node
                parent_node = path_to_node[parent_path]

                # Create a node for this path
                filename = Path(path).name

                if entry_type == "d":  # Directory  # pragma: no cover - display formatting
                    dir_count += 1
                    node = parent_node.add(f"[highlight]{filename}/[/]")
                    path_to_node[path] = node
                else:  # File  # pragma: no cover - display formatting
                    file_count += 1
                    # Style based on file extension
                    if any(
                        filename.endswith(ext) for ext in [".py", ".js", ".sh", ".bash", ".zsh"]
                    ):
                        node = parent_node.add(f"[success]{filename}[/]")
                    elif any(
                        filename.endswith(ext)
                        for ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff"]
                    ):
                        node = parent_node.add(f"[highlight]{filename}[/]")
                    elif any(
                        filename.endswith(ext) for ext in [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
                    ):
                        node = parent_node.add(f"[info]{filename}[/]")
                    elif any(
                        filename.endswith(ext)
                        for ext in [".tar", ".gz", ".zip", ".rar", ".7z", ".bz2"]
                    ):
                        node = parent_node.add(f"[warning]{filename}[/]")
                    else:
                        node = parent_node.add(filename)

            # Display the tree
            console.print(tree)
            console.print(f"\nTotal: [info]{file_count}[/] files, [info]{dir_count}[/] directories")

            return True

        except (OSError, subprocess.SubprocessError) as e:  # pragma: no cover
            display_error(f"Error displaying directory tree: {str(e)}")
            return False

    def cmd_lcd(self, args: list[str]) -> bool:
        """Change local download directory"""
        if not args:
            display_error("Usage: lcd <local_path>")
            return False

        try:
            # Resolve path (make absolute if needed)
            path = args[0]
            path_obj = Path(path)
            if not path_obj.is_absolute():
                path_obj = path_obj.absolute()

            new_path = str(path_obj)

            # Create directory if it doesn't exist
            if not path_obj.exists():  # pragma: no cover - directory creation
                display_info(f"Local directory does not exist, creating: {new_path}")
                path_obj.mkdir(parents=True, exist_ok=True)
                # Ensure proper permissions
                path_obj.chmod(0o755)
            elif not path_obj.is_dir():
                display_error(f"Path exists but is not a directory: {new_path}")
                return False

            # Set the local download directory
            self.local_download_dir = new_path
            display_success(f"Local download directory set to: {new_path}")
            return True
        except OSError as e:
            display_error(f"Failed to change local directory: {str(e)}")
            return False

    def cmd_debug(self, args: list[str]) -> bool:
        """Enable or disable debug logging"""
        from .logging_module import DEBUG_MODE

        if args and args[0].lower() in ("off", "disable", "false", "0"):
            # Explicitly disable
            set_debug_mode(False)
            display_info("Debug logging disabled")
            if SCP_LOGGER:
                SCP_LOGGER.info("Debug logging disabled")
        elif args and args[0].lower() in ("on", "enable", "true", "1"):
            # Explicitly enable
            set_debug_mode(True)
            display_info("Debug logging enabled")
            if SCP_LOGGER:
                SCP_LOGGER.info("Debug logging enabled")
        else:
            # Toggle current state
            new_mode = not DEBUG_MODE
            set_debug_mode(new_mode)
            status = "enabled" if new_mode else "disabled"
            display_info(f"Debug logging {status}")
            if SCP_LOGGER:
                SCP_LOGGER.info(f"Debug logging {status}")
        return True

    def check_connection(self) -> bool:
        """Check if the SSH connection is still active"""
        if not self.socket_path or not self.conn:
            return False

        # Check if the socket file exists
        if not Path(self.socket_path).exists():
            return False

        # Try a simple command to check connection
        try:
            cmd = [
                "ssh",
                "-o",
                f"ControlPath={self.socket_path}",
                f"{self.conn.username}@{self.conn.host}",
                "echo connected",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)  # noqa: S603  # args are constructed from validated SSH parameters
            return result.returncode == 0
        except (
            OSError,
            subprocess.SubprocessError,
        ):  # pragma: no cover - connection check exception
            return False
