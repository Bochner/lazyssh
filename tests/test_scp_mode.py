"""Tests for scp_mode module - file transfer interface, completions, commands."""

from pathlib import Path
from unittest import mock

import pytest
from prompt_toolkit.document import Document
from rich.console import Console
from rich.progress import Progress

from lazyssh import scp_mode
from lazyssh.models import SSHConnection
from lazyssh.scp_mode import SCPMode, SCPModeCompleter
from lazyssh.ssh import SSHManager


class TestTruncateFilename:
    """Tests for truncate_filename function."""

    def test_short_filename_unchanged(self) -> None:
        """Test that short filenames are not truncated."""
        result = scp_mode.truncate_filename("short.txt", max_length=30)
        assert result == "short.txt"

    def test_exact_length_unchanged(self) -> None:
        """Test that filenames at exact max length are not truncated."""
        filename = "a" * 30
        result = scp_mode.truncate_filename(filename, max_length=30)
        assert result == filename

    def test_long_filename_with_extension(self) -> None:
        """Test truncation preserves extension."""
        filename = "very_long_filename_that_needs_truncating.txt"
        result = scp_mode.truncate_filename(filename, max_length=30)
        assert result.endswith(".txt")
        assert "..." in result
        # The function preserves extension and adds ellipsis
        assert len(result) < len(filename)

    def test_long_filename_without_extension(self) -> None:
        """Test truncation of filename without extension."""
        filename = "a" * 50
        result = scp_mode.truncate_filename(filename, max_length=20)
        assert result.endswith("...")
        assert len(result) <= 20

    def test_extension_too_long(self) -> None:
        """Test truncation when extension is too long to preserve."""
        filename = "file.verylongextension"
        result = scp_mode.truncate_filename(filename, max_length=10)
        assert result.endswith("...")
        assert len(result) <= 10


class TestCreateProgressBar:
    """Tests for create_progress_bar function."""

    def test_creates_progress_instance(self) -> None:
        """Test that progress bar is created."""
        console_instance = Console(force_terminal=True)
        progress = scp_mode.create_progress_bar(console_instance)
        assert isinstance(progress, Progress)

    def test_progress_bar_has_columns(self) -> None:
        """Test that progress bar has expected columns."""
        console_instance = Console(force_terminal=True)
        progress = scp_mode.create_progress_bar(console_instance)
        # Progress should have columns
        assert len(progress.columns) > 0


class TestCreateMultiFileProgressBar:
    """Tests for create_multi_file_progress_bar function."""

    def test_creates_progress_instance(self) -> None:
        """Test that multi-file progress bar is created."""
        console_instance = Console(force_terminal=True)
        progress = scp_mode.create_multi_file_progress_bar(console_instance)
        assert isinstance(progress, Progress)

    def test_progress_bar_configuration(self) -> None:
        """Test progress bar configuration."""
        console_instance = Console(force_terminal=True)
        progress = scp_mode.create_multi_file_progress_bar(console_instance)
        # Just verify it's a valid Progress instance with columns
        assert len(progress.columns) > 0


class TestSCPModeInit:
    """Tests for SCPMode initialization."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_init_basic(self, ssh_manager: SSHManager) -> None:
        """Test basic SCPMode initialization."""
        mode = SCPMode(ssh_manager)
        assert mode.ssh_manager is ssh_manager
        assert mode.socket_path is None
        assert mode.conn is None
        assert mode.download_count == 0
        assert mode.upload_count == 0

    def test_init_with_connection_name(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test SCPMode initialization with connection name."""
        # Mock the connect method to avoid actual connection
        monkeypatch.setattr(SCPMode, "connect", lambda self: False)
        mode = SCPMode(ssh_manager, selected_connection="testconn")
        assert mode.connection_name == "testconn"
        assert mode.socket_path == "/tmp/testconn"

    def test_commands_registered(self, ssh_manager: SSHManager) -> None:
        """Test that expected commands are registered."""
        mode = SCPMode(ssh_manager)
        expected_commands = [
            "get",
            "put",
            "ls",
            "cd",
            "pwd",
            "mget",
            "local",
            "lls",
            "help",
            "exit",
            "tree",
            "lcd",
            "debug",
        ]
        for cmd in expected_commands:
            assert cmd in mode.commands

    def test_directories_created(self, ssh_manager: SSHManager) -> None:
        """Test that required directories are created."""
        mode = SCPMode(ssh_manager)
        assert mode.log_dir.exists()
        assert mode.history_dir.exists()


class TestSCPModeCompleter:
    """Tests for SCPModeCompleter class."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    @pytest.fixture
    def completer(self, scp_mode_instance: SCPMode) -> SCPModeCompleter:
        """Create a completer instance for testing."""
        return SCPModeCompleter(scp_mode_instance)

    def test_completer_init(self, completer: SCPModeCompleter) -> None:
        """Test completer initialization."""
        assert completer.scp_mode is not None

    def test_complete_empty_input(self, completer: SCPModeCompleter) -> None:
        """Test completion on empty input."""
        doc = Document("")
        completions = list(completer.get_completions(doc, None))
        # Should suggest base commands
        assert len(completions) > 0
        command_names = [c.text for c in completions]
        assert "get" in command_names
        assert "put" in command_names
        assert "help" in command_names

    def test_complete_partial_command(self, completer: SCPModeCompleter) -> None:
        """Test completion on partial command."""
        doc = Document("ge")
        completions = list(completer.get_completions(doc, None))
        assert any("get" in c.text for c in completions)

    def test_complete_put_local_path(self, completer: SCPModeCompleter, tmp_path: Path) -> None:
        """Test completion for put command with local files."""
        # Create test files
        (tmp_path / "testfile1.txt").touch()
        (tmp_path / "testfile2.txt").touch()
        (tmp_path / "subdir").mkdir()

        # Change to temp directory for the test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            doc = Document("put ")
            completions = list(completer.get_completions(doc, None))
            # Should list local files
            completion_texts = [c.text for c in completions]
            assert any("testfile1.txt" in t for t in completion_texts)
        finally:
            os.chdir(original_cwd)

    def test_complete_lcd_directories(self, completer: SCPModeCompleter, tmp_path: Path) -> None:
        """Test completion for lcd command shows only directories."""
        # Create test structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()
        (tmp_path / "file.txt").touch()

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            doc = Document("lcd ")
            completions = list(completer.get_completions(doc, None))
            # Should list directories only
            completion_texts = [c.text for c in completions]
            assert any("dir1" in t for t in completion_texts)
            assert any("dir2" in t for t in completion_texts)
        finally:
            os.chdir(original_cwd)

    def test_complete_invalid_shlex(self, completer: SCPModeCompleter) -> None:
        """Test completion with invalid shlex input."""
        doc = Document('get "unclosed')
        # Should not crash
        list(completer.get_completions(doc, None))


class TestSCPModeConnect:
    """Tests for SCPMode connection methods."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_connect_no_socket(self, ssh_manager: SSHManager) -> None:
        """Test connect without socket path."""
        mode = SCPMode(ssh_manager)
        assert mode.connect() is False

    def test_connect_invalid_socket(self, ssh_manager: SSHManager) -> None:
        """Test connect with invalid socket path."""
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/nonexistent"
        assert mode.connect() is False


class TestSCPModeCommands:
    """Tests for SCPMode command handlers."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_help(self, scp_mode_instance: SCPMode) -> None:
        """Test help command."""
        scp_mode_instance.cmd_help([])

    def test_cmd_exit(self, scp_mode_instance: SCPMode) -> None:
        """Test exit command returns True."""
        result = scp_mode_instance.cmd_exit([])
        assert result is True

    def test_cmd_debug_toggle(self, scp_mode_instance: SCPMode) -> None:
        """Test debug command toggles debug mode."""
        # First call enables debug
        scp_mode_instance.cmd_debug([])
        # Second call disables debug
        scp_mode_instance.cmd_debug([])

    def test_cmd_get_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test get command without connection."""
        scp_mode_instance.cmd_get([])

    def test_cmd_get_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test get command with no arguments."""
        scp_mode_instance.conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testget",
        )
        scp_mode_instance.cmd_get([])

    def test_cmd_put_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test put command without connection."""
        scp_mode_instance.cmd_put([])

    def test_cmd_put_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test put command with no arguments."""
        scp_mode_instance.conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testput",
        )
        scp_mode_instance.cmd_put([])

    def test_cmd_ls_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test ls command without connection."""
        scp_mode_instance.cmd_ls([])

    def test_cmd_cd_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test cd command with no arguments shows usage."""
        result = scp_mode_instance.cmd_cd([])
        assert result is False

    def test_cmd_pwd_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test pwd command without connection."""
        scp_mode_instance.cmd_pwd([])

    def test_cmd_pwd_with_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test pwd command with connection."""
        scp_mode_instance.conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testpwd",
        )
        scp_mode_instance.current_remote_dir = "/home/user/docs"
        scp_mode_instance.cmd_pwd([])

    def test_cmd_lls(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test lls command lists local files."""
        (tmp_path / "test.txt").touch()
        scp_mode_instance.local_download_dir = str(tmp_path)
        scp_mode_instance.cmd_lls([])

    def test_cmd_lls_with_path(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test lls command with specific path."""
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "file.txt").touch()
        scp_mode_instance.cmd_lls([str(tmp_path / "subdir")])

    def test_cmd_lls_invalid_path(self, scp_mode_instance: SCPMode) -> None:
        """Test lls command with invalid path."""
        scp_mode_instance.cmd_lls(["/nonexistent/path"])

    def test_cmd_local_shows_info(self, scp_mode_instance: SCPMode) -> None:
        """Test local command shows directory info."""
        scp_mode_instance.local_download_dir = "/tmp/downloads"
        scp_mode_instance.local_upload_dir = "/tmp/uploads"
        scp_mode_instance.cmd_local([])

    def test_cmd_lcd_change_directory(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test lcd command changes local directory."""
        scp_mode_instance.local_download_dir = str(tmp_path)
        new_dir = tmp_path / "newdir"
        new_dir.mkdir()
        scp_mode_instance.cmd_lcd([str(new_dir)])
        assert scp_mode_instance.local_download_dir == str(new_dir)

    def test_cmd_lcd_invalid_path(self, scp_mode_instance: SCPMode) -> None:
        """Test lcd command with invalid path."""
        scp_mode_instance.cmd_lcd(["/nonexistent/directory"])

    def test_cmd_lcd_file_not_directory(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test lcd command with file path instead of directory."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        scp_mode_instance.cmd_lcd([str(file_path)])

    def test_cmd_mget_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test mget command without connection."""
        scp_mode_instance.cmd_mget([])

    def test_cmd_tree_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test tree command without connection."""
        scp_mode_instance.cmd_tree([])


class TestSCPModeCache:
    """Tests for SCPMode caching functionality."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_update_cache(self, scp_mode_instance: SCPMode) -> None:
        """Test caching directory listing."""
        test_data = ["file1.txt", "file2.txt"]
        scp_mode_instance._update_cache("/home/user", "ls", test_data)

        result = scp_mode_instance._get_cached_result("/home/user", "ls")
        assert result == test_data

    def test_cache_miss_wrong_type(self, scp_mode_instance: SCPMode) -> None:
        """Test cache miss when type doesn't match."""
        test_data = ["file1.txt"]
        scp_mode_instance._update_cache("/home/user", "ls", test_data)

        result = scp_mode_instance._get_cached_result("/home/user", "tree")
        assert result is None

    def test_cache_expired(self, scp_mode_instance: SCPMode) -> None:
        """Test cache expiration."""
        from datetime import datetime, timedelta

        test_data = ["file1.txt"]
        scp_mode_instance._update_cache("/home/user", "ls", test_data)

        # Manually expire the cache by modifying timestamp
        normalized = scp_mode_instance._normalize_cache_path("/home/user")
        cache_key = f"{normalized}:ls"
        if cache_key in scp_mode_instance.directory_cache:
            # Set timestamp to past the TTL
            scp_mode_instance.directory_cache[cache_key]["timestamp"] = datetime.now() - timedelta(
                seconds=scp_mode.CACHE_TTL_SECONDS + 1
            )

        result = scp_mode_instance._get_cached_result("/home/user", "ls")
        assert result is None

    def test_invalidate_cache_all(self, scp_mode_instance: SCPMode) -> None:
        """Test cache invalidation for all paths."""
        scp_mode_instance._update_cache("/home/user", "ls", ["file1.txt"])
        scp_mode_instance._update_cache("/home/other", "ls", ["file2.txt"])
        scp_mode_instance._invalidate_cache()  # Invalidate all

        assert scp_mode_instance._get_cached_result("/home/user", "ls") is None
        assert scp_mode_instance._get_cached_result("/home/other", "ls") is None

    def test_normalize_cache_path(self, scp_mode_instance: SCPMode) -> None:
        """Test cache path normalization."""
        # Trailing slashes should be stripped
        result = scp_mode_instance._normalize_cache_path("/home/user/")
        assert result == "/home/user"

        # Multiple slashes should be normalized
        result = scp_mode_instance._normalize_cache_path("/home//user")
        assert "//" not in result


class TestSCPModeThrottling:
    """Tests for SCPMode completion throttling."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_should_throttle_explicit_tab(self, scp_mode_instance: SCPMode) -> None:
        """Test that explicit tab press is not throttled."""
        scp_mode_instance._update_completion_time()
        result = scp_mode_instance._should_throttle_completion(explicit_tab=True)
        assert result is False

    def test_should_throttle_rapid_typing(self, scp_mode_instance: SCPMode) -> None:
        """Test that rapid typing is throttled."""
        scp_mode_instance._update_completion_time()
        result = scp_mode_instance._should_throttle_completion(explicit_tab=False)
        assert result is True

    def test_should_not_throttle_after_delay(self, scp_mode_instance: SCPMode) -> None:
        """Test that typing after delay is not throttled."""
        import time

        scp_mode_instance._update_completion_time()
        # Wait longer than throttle period
        time.sleep(scp_mode.COMPLETION_THROTTLE_MS / 1000 + 0.1)
        result = scp_mode_instance._should_throttle_completion(explicit_tab=False)
        assert result is False


class TestSCPModeHelpers:
    """Tests for SCPMode helper methods."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_resolve_remote_path_absolute(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving absolute remote path."""
        result = scp_mode_instance._resolve_remote_path("/absolute/path")
        assert result == "/absolute/path"

    def test_resolve_remote_path_tilde_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving tilde without connection returns original path."""
        # Without SSH connection, tilde can't be expanded
        result = scp_mode_instance._resolve_remote_path("~/documents")
        assert result == "~/documents"

    def test_resolve_remote_path_relative(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving relative remote path."""
        scp_mode_instance.current_remote_dir = "/home/user"
        result = scp_mode_instance._resolve_remote_path("documents")
        assert result == "/home/user/documents"

    def test_resolve_remote_path_empty(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving empty path returns current directory."""
        scp_mode_instance.current_remote_dir = "/home/user"
        result = scp_mode_instance._resolve_remote_path("")
        assert result == "/home/user"


class TestSCPModeSSHCommand:
    """Tests for SCPMode SSH command execution."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing with connection."""
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/testsock"
        mode.connection_name = "testsock"  # Required for _execute_ssh_command
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testsock",
        )
        mode.conn = conn
        # Also add to connections dict so connection check passes
        ssh_manager.connections["/tmp/testsock"] = conn
        return mode

    def test_execute_ssh_command_success(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful SSH command execution."""

        def mock_run(*args, **kwargs):
            result = mock.Mock()
            result.returncode = 0
            result.stdout = "command output"
            result.stderr = ""
            return result

        monkeypatch.setattr("subprocess.run", mock_run)
        result = scp_mode_instance._execute_ssh_command("echo test")
        # The function returns a CompletedProcess, so check the stdout
        assert result is not None and result.stdout == "command output"

    def test_execute_ssh_command_failure(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test failed SSH command execution."""

        def mock_run(*args, **kwargs):
            result = mock.Mock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = "error message"
            return result

        monkeypatch.setattr("subprocess.run", mock_run)
        result = scp_mode_instance._execute_ssh_command("invalid command")
        # Function returns the result object even on failure
        assert result is not None and result.returncode == 1

    def test_execute_ssh_command_no_connection(self, ssh_manager: SSHManager) -> None:
        """Test SSH command execution without connection."""
        mode = SCPMode(ssh_manager)
        result = mode._execute_ssh_command("echo test")
        assert result is None


class TestSCPModeRun:
    """Tests for SCPMode run loop."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_run_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test run with no connections available exits early."""
        mode = SCPMode(ssh_manager)
        # Without connections, run should exit early
        mode.run()

    def test_command_dispatch(self, ssh_manager: SSHManager) -> None:
        """Test that commands are properly dispatched."""
        mode = SCPMode(ssh_manager)

        # All commands should be callable
        for _cmd_name, cmd_func in mode.commands.items():
            assert callable(cmd_func)


class TestSCPModeDebugCommand:
    """Tests for SCPMode debug command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_debug_toggle(self, scp_mode_instance: SCPMode) -> None:
        """Test debug toggle command."""
        scp_mode_instance.cmd_debug([])
        scp_mode_instance.cmd_debug([])

    def test_cmd_debug_on(self, scp_mode_instance: SCPMode) -> None:
        """Test debug on command."""
        scp_mode_instance.cmd_debug(["on"])

    def test_cmd_debug_off(self, scp_mode_instance: SCPMode) -> None:
        """Test debug off command."""
        scp_mode_instance.cmd_debug(["off"])


class TestSCPModeConnectEdgeCases:
    """Tests for SCPMode connect edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_connect_no_socket_path(self, ssh_manager: SSHManager) -> None:
        """Test connect with no socket path."""
        mode = SCPMode(ssh_manager)
        result = mode.connect()
        assert result is False

    def test_connect_socket_not_found(self, ssh_manager: SSHManager) -> None:
        """Test connect when socket is not in connections."""
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/nonexistent"
        result = mode.connect()
        assert result is False


class TestSCPModeCompleterEdgeCases:
    """Tests for SCPModeCompleter edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    @pytest.fixture
    def completer(self, scp_mode_instance: SCPMode) -> SCPModeCompleter:
        """Create a completer instance."""
        return SCPModeCompleter(scp_mode_instance)

    def test_completer_lcd_command(self, completer: SCPModeCompleter, tmp_path: Path) -> None:
        """Test lcd command completion."""
        doc = Document("lcd ")
        list(completer.get_completions(doc, None))

    def test_completer_lcd_with_partial(self, completer: SCPModeCompleter, tmp_path: Path) -> None:
        """Test lcd command with partial path."""
        doc = Document(f"lcd {tmp_path}/")
        list(completer.get_completions(doc, None))

    def test_completer_lput_command(self, completer: SCPModeCompleter, tmp_path: Path) -> None:
        """Test lput command completion (same as put)."""
        completer.scp_mode.local_upload_dir = str(tmp_path)
        doc = Document("put ")
        list(completer.get_completions(doc, None))

    def test_completer_invalid_shlex(self, completer: SCPModeCompleter) -> None:
        """Test completion with invalid shlex input."""
        doc = Document('get "unclosed')
        list(completer.get_completions(doc, None))


class TestSCPModeInitWithConnection:
    """Tests for SCPMode initialization with a pre-selected connection."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance with connection."""
        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/preselect",
        )
        manager.connections["/tmp/preselect"] = conn
        return manager

    def test_init_with_selected_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialization with pre-selected connection."""
        # Mock subprocess.run to avoid actual SSH calls
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "/home/user"
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        mode = SCPMode(ssh_manager, selected_connection="preselect")
        assert mode.socket_path == "/tmp/preselect"

    def test_init_with_invalid_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialization with invalid connection name."""
        # Mock subprocess.run to avoid actual SSH calls (though connect will fail early)
        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        mode = SCPMode(ssh_manager, selected_connection="nonexistent")
        assert mode.socket_path == "/tmp/nonexistent"


class TestSCPModeCommandsWithConnection:
    """Tests for SCPMode commands that require connection."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance with connection."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/cmdtest",
        )
        ssh_manager.connections["/tmp/cmdtest"] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/cmdtest"
        mode.conn = conn
        mode.connection_name = "cmdtest"
        return mode

    def test_cmd_get_with_connection(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get command with connection."""
        # Just test that it doesn't crash
        scp_mode_instance.cmd_get([])

    def test_cmd_get_with_path(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get command with path argument."""
        # Mock the _execute_ssh_command to return False/None
        monkeypatch.setattr(scp_mode_instance, "_execute_ssh_command", lambda x: None)
        scp_mode_instance.cmd_get(["test.txt"])

    def test_cmd_ls_with_connection(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test ls command with connection."""

        def mock_exec(cmd: str):
            result = mock.Mock()
            result.returncode = 0
            result.stdout = "file1.txt\nfile2.txt"
            result.stderr = ""
            return result

        monkeypatch.setattr(scp_mode_instance, "_execute_ssh_command", mock_exec)
        scp_mode_instance.cmd_ls([])

    def test_cmd_cd_with_connection(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cd command with connection."""

        def mock_exec(cmd: str):
            result = mock.Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        monkeypatch.setattr(scp_mode_instance, "_execute_ssh_command", mock_exec)
        scp_mode_instance.cmd_cd(["/home/user"])


class TestSCPModeResolveRemotePath:
    """Tests for remote path resolution edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_resolve_path_with_dots(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving path with . and .. components."""
        scp_mode_instance.current_remote_dir = "/home/user/docs"
        # Relative path starting with ./
        result = scp_mode_instance._resolve_remote_path("./file.txt")
        assert "file.txt" in result

    def test_resolve_path_current_dir_tilde(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving relative path when current dir is ~."""
        scp_mode_instance.current_remote_dir = "~"
        result = scp_mode_instance._resolve_remote_path("documents")
        assert result == "~/documents"

    def test_resolve_path_with_home(self, scp_mode_instance: SCPMode) -> None:
        """Test resolving path when remote home is known."""
        scp_mode_instance.remote_home_dir = "/home/testuser"
        result = scp_mode_instance._resolve_remote_path("~/documents")
        # Without connection, tilde may not expand
        assert "documents" in result


class TestSCPModeCacheInvalidation:
    """Tests for cache invalidation scenarios."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_invalidate_specific_path(self, scp_mode_instance: SCPMode) -> None:
        """Test invalidating cache for specific path."""
        scp_mode_instance._update_cache("/home/user", "ls", ["file1.txt"])
        scp_mode_instance._update_cache("/home/other", "ls", ["file2.txt"])
        scp_mode_instance._invalidate_cache("/home/user")

        # /home/user should be invalidated
        assert scp_mode_instance._get_cached_result("/home/user", "ls") is None
        # /home/other should still be cached
        assert scp_mode_instance._get_cached_result("/home/other", "ls") is not None

    def test_invalidate_exact_path(self, scp_mode_instance: SCPMode) -> None:
        """Test invalidating cache for exact path."""
        scp_mode_instance._update_cache("/home/user/docs", "ls", ["file1.txt"])
        scp_mode_instance._invalidate_cache("/home/user/docs")

        # The exact path should be invalidated
        assert scp_mode_instance._get_cached_result("/home/user/docs", "ls") is None


class TestSCPModeTreeCommand:
    """Tests for SCPMode tree command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_tree_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test tree command with no args and no connection."""
        scp_mode_instance.cmd_tree([])


class TestSCPModeMgetCommand:
    """Tests for SCPMode mget command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_mget_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test mget command with no args."""
        scp_mode_instance.cmd_mget([])


class TestSCPModeGetCommand:
    """Tests for SCPMode get command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        mode = SCPMode(ssh_manager)
        return mode

    def test_cmd_get_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test get command without connection."""
        scp_mode_instance.cmd_get(["file.txt"])


class TestSCPModePutCommand:
    """Tests for SCPMode put command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_put_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test put command without connection."""
        scp_mode_instance.cmd_put(["file.txt"])

    def test_cmd_put_file_not_found(
        self, scp_mode_instance: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test put command with non-existent file."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/puttest"
        )
        scp_mode_instance.conn = conn
        scp_mode_instance.cmd_put(["/nonexistent/file.txt"])


class TestSCPModeGetPromptText:
    """Tests for SCPMode get_prompt_text method."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_get_prompt_text_no_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test prompt without connection."""
        prompt = scp_mode_instance.get_prompt_text()
        assert prompt is not None

    def test_get_prompt_text_with_connection(self, scp_mode_instance: SCPMode) -> None:
        """Test prompt with connection."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/prompttest"
        )
        scp_mode_instance.conn = conn
        scp_mode_instance.connection_name = "prompttest"
        prompt = scp_mode_instance.get_prompt_text()
        assert prompt is not None


class TestSCPModeSelectConnection:
    """Tests for SCPMode connection selection."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_no_connections_available(self, ssh_manager: SSHManager) -> None:
        """Test when no connections are available."""
        mode = SCPMode(ssh_manager)
        # run() should exit early with no connections
        mode.run()

    def test_single_connection_auto_select(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test auto-selection with single connection."""
        import subprocess

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/singleconn"
        )
        ssh_manager.connections["/tmp/singleconn"] = conn

        # Mock IntPrompt.ask to return 1 (select first connection)
        monkeypatch.setattr("lazyssh.scp_mode.IntPrompt.ask", lambda *args, **kwargs: 1)

        # Mock subprocess.run to avoid actual SSH calls
        mock_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        # Mock the prompt session to immediately exit
        mode = SCPMode(ssh_manager)
        monkeypatch.setattr(mode.session, "prompt", lambda *args, **kwargs: "exit")
        mode.run()


class TestSCPModeCompleterRemote:
    """Tests for SCPModeCompleter remote completions."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    @pytest.fixture
    def completer(self, scp_mode_instance: SCPMode) -> SCPModeCompleter:
        """Create a completer instance."""
        return SCPModeCompleter(scp_mode_instance)

    def test_completer_get_command(self, completer: SCPModeCompleter) -> None:
        """Test completion for get command."""
        doc = Document("get ")
        list(completer.get_completions(doc, None))

    def test_completer_cd_command(self, completer: SCPModeCompleter) -> None:
        """Test completion for cd command."""
        doc = Document("cd ")
        list(completer.get_completions(doc, None))

    def test_completer_mget_command(self, completer: SCPModeCompleter) -> None:
        """Test completion for mget command."""
        doc = Document("mget ")
        list(completer.get_completions(doc, None))

    def test_completer_tree_command(self, completer: SCPModeCompleter) -> None:
        """Test completion for tree command."""
        doc = Document("tree ")
        list(completer.get_completions(doc, None))


class TestSCPModeFileTransfers:
    """Tests for SCPMode file transfer operations with mocking."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def connected_scp_mode(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance with a mocked connection."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/transfer",
        )
        ssh_manager.connections["/tmp/transfer"] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/transfer"
        mode.conn = conn
        mode.connection_name = "transfer"
        mode.local_download_dir = "/tmp/downloads"
        mode.local_upload_dir = "/tmp/uploads"
        mode.current_remote_dir = "/home/user"
        return mode

    def test_cmd_put_success(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful file upload."""
        from unittest import mock

        # Create a local file
        test_file = tmp_path / "upload.txt"
        test_file.write_text("test content")

        # Mock check_connection
        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        # Mock subprocess.Popen for the SCP process
        mock_process = mock.Mock()
        mock_process.poll.side_effect = [None, 0]  # Running, then done
        mock_process.wait.return_value = 0
        mock_process.stdout = mock.Mock()
        mock_process.stderr = mock.Mock()
        mock_process.stderr.read.return_value = ""

        with mock.patch("subprocess.Popen", return_value=mock_process):
            with mock.patch("lazyssh.scp_mode.log_file_transfer"):
                with mock.patch("lazyssh.scp_mode.update_transfer_stats"):
                    connected_scp_mode.cmd_put([str(test_file)])

    def test_cmd_put_file_not_found(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test upload when file doesn't exist."""
        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)
        connected_scp_mode.cmd_put(["/nonexistent/file.txt"])

    def test_cmd_put_with_remote_path(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test upload with explicit remote path."""
        from unittest import mock

        test_file = tmp_path / "upload2.txt"
        test_file.write_text("test content")

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        mock_process = mock.Mock()
        mock_process.poll.side_effect = [None, 0]
        mock_process.wait.return_value = 0
        mock_process.stdout = mock.Mock()
        mock_process.stderr = mock.Mock()
        mock_process.stderr.read.return_value = ""

        with mock.patch("subprocess.Popen", return_value=mock_process):
            with mock.patch("lazyssh.scp_mode.log_file_transfer"):
                with mock.patch("lazyssh.scp_mode.update_transfer_stats"):
                    connected_scp_mode.cmd_put([str(test_file), "/remote/path/file.txt"])

    def test_cmd_put_failure(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test upload failure."""
        from unittest import mock

        test_file = tmp_path / "failupload.txt"
        test_file.write_text("test content")

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        mock_process = mock.Mock()
        mock_process.poll.side_effect = [None, 1]
        mock_process.wait.return_value = 1
        mock_process.stdout = mock.Mock()
        mock_process.stderr = mock.Mock()
        mock_process.stderr.read.return_value = "Permission denied"

        with mock.patch("subprocess.Popen", return_value=mock_process):
            connected_scp_mode.cmd_put([str(test_file)])

    def test_cmd_get_success(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful file download."""
        from unittest import mock

        connected_scp_mode.local_download_dir = str(tmp_path)

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        # Mock size check
        size_result = mock.Mock()
        size_result.returncode = 0
        size_result.stdout = "1024"
        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: size_result)

        # Mock Confirm.ask
        with mock.patch("lazyssh.scp_mode.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = True

            # Mock subprocess.Popen
            mock_process = mock.Mock()
            mock_process.poll.side_effect = [None, 0]
            mock_process.wait.return_value = 0
            mock_process.stdout = mock.Mock()
            mock_process.stderr = mock.Mock()
            mock_process.stderr.read.return_value = ""

            with mock.patch("subprocess.Popen", return_value=mock_process):
                with mock.patch("lazyssh.scp_mode.log_file_transfer"):
                    with mock.patch("lazyssh.scp_mode.update_transfer_stats"):
                        connected_scp_mode.cmd_get(["remote_file.txt"])

    def test_cmd_get_cancelled(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download cancelled by user."""
        from unittest import mock

        connected_scp_mode.local_download_dir = str(tmp_path)

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        size_result = mock.Mock()
        size_result.returncode = 0
        size_result.stdout = "1024"
        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: size_result)

        with mock.patch("lazyssh.scp_mode.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False  # Cancel
            connected_scp_mode.cmd_get(["remote_file.txt"])

    def test_cmd_get_file_not_found(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download when remote file not found."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        size_result = mock.Mock()
        size_result.returncode = 1
        size_result.stdout = ""
        size_result.stderr = "No such file"
        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: size_result)

        connected_scp_mode.cmd_get(["nonexistent.txt"])

    def test_cmd_get_no_download_dir(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download when no download directory set."""
        from unittest import mock

        connected_scp_mode.local_download_dir = None

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        size_result = mock.Mock()
        size_result.returncode = 0
        size_result.stdout = "1024"
        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: size_result)

        connected_scp_mode.cmd_get(["remote_file.txt"])

    def test_cmd_mget_success(
        self, connected_scp_mode: SCPMode, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful multi-file download."""
        from unittest import mock

        connected_scp_mode.local_download_dir = str(tmp_path)

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        # Mock find command
        find_result = mock.Mock()
        find_result.returncode = 0
        find_result.stdout = "file1.txt\nfile2.txt"
        find_result.stderr = ""

        # Mock stat command for sizes
        stat_result = mock.Mock()
        stat_result.returncode = 0
        stat_result.stdout = "/home/user/file1.txt 100\n/home/user/file2.txt 200"
        stat_result.stderr = ""

        def mock_ssh_cmd(cmd):
            if "find" in cmd:
                return find_result
            elif "stat" in cmd:
                return stat_result
            return None

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", mock_ssh_cmd)

        with mock.patch("lazyssh.scp_mode.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = True

            mock_process = mock.Mock()
            mock_process.poll.side_effect = [None, 0] * 2  # For each file
            mock_process.wait.return_value = 0
            mock_process.stdout = mock.Mock()
            mock_process.stderr = mock.Mock()
            mock_process.stderr.read.return_value = ""

            with mock.patch("subprocess.Popen", return_value=mock_process):
                with mock.patch("lazyssh.scp_mode.log_file_transfer"):
                    with mock.patch("lazyssh.scp_mode.update_transfer_stats"):
                        connected_scp_mode.cmd_mget(["*.txt"])

    def test_cmd_mget_no_matches(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test mget with no matching files."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        find_result = mock.Mock()
        find_result.returncode = 0
        find_result.stdout = ""
        find_result.stderr = ""

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: find_result)

        connected_scp_mode.cmd_mget(["*.xyz"])

    def test_cmd_mget_cancelled(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test mget cancelled by user."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        find_result = mock.Mock()
        find_result.returncode = 0
        find_result.stdout = "file1.txt"
        find_result.stderr = ""

        stat_result = mock.Mock()
        stat_result.returncode = 0
        stat_result.stdout = "/home/user/file1.txt 100"
        stat_result.stderr = ""

        def mock_ssh_cmd(cmd):
            if "find" in cmd:
                return find_result
            elif "stat" in cmd:
                return stat_result
            return None

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", mock_ssh_cmd)

        with mock.patch("lazyssh.scp_mode.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False  # Cancel
            connected_scp_mode.cmd_mget(["*.txt"])

    def test_cmd_ls_success(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful ls command."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        ls_result = mock.Mock()
        ls_result.returncode = 0
        ls_result.stdout = "file1.txt\nfile2.txt\ndir1"
        ls_result.stderr = ""

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: ls_result)

        connected_scp_mode.cmd_ls([])

    def test_cmd_ls_with_path(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test ls command with specific path."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        ls_result = mock.Mock()
        ls_result.returncode = 0
        ls_result.stdout = "subfile.txt"
        ls_result.stderr = ""

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: ls_result)

        connected_scp_mode.cmd_ls(["/home/user/subdir"])

    def test_cmd_cd_success(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful cd command."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        cd_result = mock.Mock()
        cd_result.returncode = 0
        cd_result.stdout = "/home/user/subdir"  # pwd command returns the new directory
        cd_result.stderr = ""

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: cd_result)

        connected_scp_mode.cmd_cd(["/home/user/subdir"])
        assert "subdir" in connected_scp_mode.current_remote_dir

    def test_cmd_cd_invalid_directory(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cd to invalid directory."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        cd_result = mock.Mock()
        cd_result.returncode = 1
        cd_result.stdout = ""
        cd_result.stderr = "No such directory"

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: cd_result)

        original_dir = connected_scp_mode.current_remote_dir
        connected_scp_mode.cmd_cd(["/nonexistent"])
        assert connected_scp_mode.current_remote_dir == original_dir

    def test_cmd_tree_success(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful tree command."""
        from unittest import mock

        monkeypatch.setattr(connected_scp_mode, "check_connection", lambda: True)

        tree_result = mock.Mock()
        tree_result.returncode = 0
        tree_result.stdout = "/home/user\n├── file1.txt\n└── dir1"
        tree_result.stderr = ""

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: tree_result)

        connected_scp_mode.cmd_tree([])


class TestSCPModeRunExtended:
    """Tests for SCPMode run method - extended scenarios."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_run_no_connections_extended(self, ssh_manager: SSHManager) -> None:
        """Test run exits when no connections."""
        mode = SCPMode(ssh_manager)
        mode.run()

    def test_run_with_preselected_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test run with preselected connection that fails to connect."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/presel"
        )
        ssh_manager.connections["/tmp/presel"] = conn

        # Create mode without preselected connection, then manually set it
        mode = SCPMode(ssh_manager)
        mode.connection_name = "presel"
        mode.socket_path = "/tmp/presel"

        # Mock connect to fail - this will work because mode wasn't created with selected_connection
        monkeypatch.setattr(mode, "connect", lambda: False)

        mode.run()

    def test_run_single_connection_autoselect(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test run auto-selects single connection."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/single"
        )
        ssh_manager.connections["/tmp/single"] = conn

        mode = SCPMode(ssh_manager)

        # Mock IntPrompt for selection
        with mock.patch("lazyssh.scp_mode.IntPrompt") as mock_int:
            mock_int.ask.return_value = 1

            # Mock connect and session
            monkeypatch.setattr(mode, "connect", lambda: True)
            mock_session = mock.Mock()
            mock_session.prompt.return_value = "exit"
            mode.session = mock_session

            mode.run()

    def test_run_multiple_connections_selection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test run with multiple connections shows selection."""
        from unittest import mock

        conn1 = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/multi1"
        )
        conn2 = SSHConnection(
            host="192.168.1.2", port=22, username="user", socket_path="/tmp/multi2"
        )
        ssh_manager.connections["/tmp/multi1"] = conn1
        ssh_manager.connections["/tmp/multi2"] = conn2

        mode = SCPMode(ssh_manager)

        # Mock IntPrompt for selection
        with mock.patch("lazyssh.scp_mode.IntPrompt") as mock_int:
            mock_int.ask.return_value = 1

            monkeypatch.setattr(mode, "connect", lambda: True)
            mock_session = mock.Mock()
            mock_session.prompt.return_value = "exit"
            mode.session = mock_session

            mode.run()


class TestSCPModeCompleterWithConnection:
    """Tests for SCPModeCompleter with active connection."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def connected_scp_mode(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode with connection."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/compconn",
        )
        ssh_manager.connections["/tmp/compconn"] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/compconn"
        mode.conn = conn
        mode.connection_name = "compconn"
        mode.current_remote_dir = "/home/user"
        return mode

    def test_completer_get_with_connection(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test get completion with active connection."""
        from unittest import mock

        completer = SCPModeCompleter(connected_scp_mode)

        # Mock SSH command for ls
        ls_result = mock.Mock()
        ls_result.returncode = 0
        ls_result.stdout = "file1.txt\nfile2.txt"

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: ls_result)

        doc = Document("get ")
        list(completer.get_completions(doc, None))
        # May or may not have completions depending on throttling

    def test_completer_cd_with_connection(
        self, connected_scp_mode: SCPMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test cd completion with active connection."""
        from unittest import mock

        completer = SCPModeCompleter(connected_scp_mode)

        # Mock SSH command for find
        find_result = mock.Mock()
        find_result.returncode = 0
        find_result.stdout = "dir1\ndir2"

        monkeypatch.setattr(connected_scp_mode, "_execute_ssh_command", lambda cmd: find_result)

        doc = Document("cd ")
        list(completer.get_completions(doc, None))

    def test_completer_local_download_upload(
        self, connected_scp_mode: SCPMode, tmp_path: Path
    ) -> None:
        """Test local command completions."""
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir2").mkdir()

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            completer = SCPModeCompleter(connected_scp_mode)

            doc = Document("local ")
            completions = list(completer.get_completions(doc, None))
            names = [c.text for c in completions]
            assert "download" in names
            assert "upload" in names

            # Test directory completion after download/upload
            doc = Document("local download ")
            completions = list(completer.get_completions(doc, None))
        finally:
            os.chdir(original_cwd)


class TestSCPModeFormatSize:
    """Tests for file size formatting."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_format_bytes(self, scp_mode_instance: SCPMode) -> None:
        """Test formatting bytes."""
        result = scp_mode_instance._format_file_size(500)
        assert "B" in result

    def test_format_kilobytes(self, scp_mode_instance: SCPMode) -> None:
        """Test formatting kilobytes."""
        result = scp_mode_instance._format_file_size(1024 * 5)
        assert "KB" in result or "K" in result

    def test_format_megabytes(self, scp_mode_instance: SCPMode) -> None:
        """Test formatting megabytes."""
        result = scp_mode_instance._format_file_size(1024 * 1024 * 5)
        assert "MB" in result or "M" in result

    def test_format_gigabytes(self, scp_mode_instance: SCPMode) -> None:
        """Test formatting gigabytes."""
        result = scp_mode_instance._format_file_size(1024 * 1024 * 1024 * 2)
        assert "GB" in result or "G" in result


class TestSCPModeLocalCommand:
    """Tests for local command variations."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_local_download_subcommand(
        self, scp_mode_instance: SCPMode, tmp_path: Path
    ) -> None:
        """Test local download subcommand."""
        scp_mode_instance.local_download_dir = str(tmp_path)
        scp_mode_instance.cmd_local(["download", str(tmp_path)])
        assert scp_mode_instance.local_download_dir == str(tmp_path)

    def test_cmd_local_upload_subcommand(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test local upload subcommand."""
        scp_mode_instance.local_upload_dir = str(tmp_path)
        scp_mode_instance.cmd_local(["upload", str(tmp_path)])
        assert scp_mode_instance.local_upload_dir == str(tmp_path)

    def test_cmd_local_invalid_subcommand(self, scp_mode_instance: SCPMode) -> None:
        """Test local with invalid subcommand."""
        scp_mode_instance.cmd_local(["invalid"])


class TestSCPModeLcdCommand:
    """Tests for lcd command edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_cmd_lcd_no_args(self, scp_mode_instance: SCPMode) -> None:
        """Test lcd without arguments."""
        result = scp_mode_instance.cmd_lcd([])
        assert result is False

    def test_cmd_lcd_relative_path(self, scp_mode_instance: SCPMode, tmp_path: Path) -> None:
        """Test lcd with relative path."""
        import os

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            scp_mode_instance.local_download_dir = str(tmp_path)
            scp_mode_instance.cmd_lcd(["subdir"])
        finally:
            os.chdir(original_cwd)


class TestSCPModeCheckConnection:
    """Tests for check_connection method."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_check_connection_no_socket(self, ssh_manager: SSHManager) -> None:
        """Test check_connection without socket path."""
        mode = SCPMode(ssh_manager)
        assert mode.check_connection() is False

    def test_check_connection_not_in_manager(self, ssh_manager: SSHManager) -> None:
        """Test check_connection when not in connection manager."""
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/notexist"
        assert mode.check_connection() is False

    def test_check_connection_valid(
        self, ssh_manager: SSHManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test check_connection with valid connection."""
        # Create a temporary socket file
        socket_file = tmp_path / "checkconn"
        socket_file.touch()

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path=str(socket_file)
        )
        ssh_manager.connections[str(socket_file)] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = str(socket_file)
        mode.conn = conn
        mode.connection_name = "checkconn"

        # Mock the subprocess.run to simulate successful SSH check
        from unittest import mock

        mock_result = mock.Mock()
        mock_result.returncode = 0
        monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

        assert mode.check_connection() is True


class TestSCPModeGetScpCommand:
    """Tests for _get_scp_command method."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_get_scp_command_basic(self, ssh_manager: SSHManager) -> None:
        """Test basic SCP command generation."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/scpcmd"
        )
        ssh_manager.connections["/tmp/scpcmd"] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/scpcmd"
        mode.conn = conn

        cmd = mode._get_scp_command("user@host:file.txt", "/local/file.txt")
        assert isinstance(cmd, list)
        assert "scp" in cmd[0] or cmd[0] == "scp"

    def test_get_scp_command_with_identity(self, ssh_manager: SSHManager) -> None:
        """Test SCP command with identity file (uses control socket, not -i)."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/scpid",
            identity_file="/home/user/.ssh/id_rsa",
        )
        ssh_manager.connections["/tmp/scpid"] = conn
        mode = SCPMode(ssh_manager)
        mode.socket_path = "/tmp/scpid"
        mode.conn = conn

        # Note: SCP via control socket doesn't need -i flag since
        # the master connection already handles authentication
        cmd = mode._get_scp_command("user@host:file.txt", "/local/file.txt")
        assert "-o" in cmd
        assert "ControlPath=/tmp/scpid" in cmd


class TestSCPModeDebugVariations:
    """Tests for debug command variations."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_debug_enable(self, scp_mode_instance: SCPMode) -> None:
        """Test debug enable."""
        scp_mode_instance.cmd_debug(["enable"])

    def test_debug_disable(self, scp_mode_instance: SCPMode) -> None:
        """Test debug disable."""
        scp_mode_instance.cmd_debug(["disable"])

    def test_debug_invalid_arg(self, scp_mode_instance: SCPMode) -> None:
        """Test debug with invalid argument."""
        scp_mode_instance.cmd_debug(["invalid"])


class TestSCPModeHelpCommandSpecific:
    """Tests for help command with specific subcommands."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def scp_mode_instance(self, ssh_manager: SSHManager) -> SCPMode:
        """Create an SCPMode instance for testing."""
        return SCPMode(ssh_manager)

    def test_help_put(self, scp_mode_instance: SCPMode) -> None:
        """Test help put."""
        scp_mode_instance.cmd_help(["put"])

    def test_help_get(self, scp_mode_instance: SCPMode) -> None:
        """Test help get."""
        scp_mode_instance.cmd_help(["get"])

    def test_help_ls(self, scp_mode_instance: SCPMode) -> None:
        """Test help ls."""
        scp_mode_instance.cmd_help(["ls"])

    def test_help_pwd(self, scp_mode_instance: SCPMode) -> None:
        """Test help pwd."""
        scp_mode_instance.cmd_help(["pwd"])

    def test_help_cd(self, scp_mode_instance: SCPMode) -> None:
        """Test help cd."""
        scp_mode_instance.cmd_help(["cd"])

    def test_help_local(self, scp_mode_instance: SCPMode) -> None:
        """Test help local."""
        scp_mode_instance.cmd_help(["local"])

    def test_help_lcd(self, scp_mode_instance: SCPMode) -> None:
        """Test help lcd."""
        scp_mode_instance.cmd_help(["lcd"])

    def test_help_lls(self, scp_mode_instance: SCPMode) -> None:
        """Test help lls."""
        scp_mode_instance.cmd_help(["lls"])

    def test_help_mget(self, scp_mode_instance: SCPMode) -> None:
        """Test help mget."""
        scp_mode_instance.cmd_help(["mget"])

    def test_help_tree(self, scp_mode_instance: SCPMode) -> None:
        """Test help tree."""
        scp_mode_instance.cmd_help(["tree"])

    def test_help_debug(self, scp_mode_instance: SCPMode) -> None:
        """Test help debug."""
        scp_mode_instance.cmd_help(["debug"])

    def test_help_exit(self, scp_mode_instance: SCPMode) -> None:
        """Test help exit."""
        scp_mode_instance.cmd_help(["exit"])

    def test_help_unknown(self, scp_mode_instance: SCPMode) -> None:
        """Test help with unknown command."""
        scp_mode_instance.cmd_help(["unknown"])
