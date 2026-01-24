"""Tests for ssh module - SSHManager, connection lifecycle, tunnels, terminal methods."""

from pathlib import Path
from unittest import mock

import pytest

from lazyssh.models import SSHConnection
from lazyssh.ssh import SSHManager


class MockLogger:
    """Mock logger with all required methods."""

    def __init__(self):
        self.messages: list[tuple[str, str]] = []

    def debug(self, msg):
        self.messages.append(("debug", msg))

    def info(self, msg):
        self.messages.append(("info", msg))

    def warning(self, msg):
        self.messages.append(("warning", msg))

    def error(self, msg):
        self.messages.append(("error", msg))

    def exception(self, msg):
        self.messages.append(("exception", msg))


class TestSSHManagerInit:
    """Tests for SSHManager initialization."""

    def test_initializes_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSHManager initializes with default values."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setenv("LAZYSSH_TERMINAL_METHOD", "auto")

        manager = SSHManager()

        assert manager.connections == {}
        assert manager.control_path_base == "/tmp/"
        assert manager.terminal_method == "auto"

    def test_initializes_with_custom_terminal_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSHManager respects terminal method from config."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setenv("LAZYSSH_TERMINAL_METHOD", "native")

        manager = SSHManager()

        assert manager.terminal_method == "native"

    def test_logs_initialization(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSHManager logs during initialization."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(msg)

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())

        SSHManager()

        assert any("initialized" in msg.lower() for msg in messages)


class TestCreateConnection:
    """Tests for create_connection method."""

    def test_cancelled_by_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connection cancelled by user."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: False)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_info", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-cancel",
        )

        result = manager.create_connection(conn)

        assert result is False

    def test_cancelled_by_user_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connection cancelled by user with logging."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(("debug", msg))

            def info(self, msg):
                messages.append(("info", msg))

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: False)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_info", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-cancel-log",
        )

        result = manager.create_connection(conn)

        assert result is False
        assert any("cancelled" in msg.lower() for level, msg in messages)

    def test_ssh_command_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when SSH command returns non-zero."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Connection refused"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-fail",
        )

        result = manager.create_connection(conn)

        assert result is False

    def test_ssh_command_fails_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when SSH command fails with logging enabled."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(("debug", msg))

            def info(self, msg):
                messages.append(("info", msg))

            def error(self, msg):
                messages.append(("error", msg))

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Connection refused"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-fail-log",
        )

        result = manager.create_connection(conn)

        assert result is False
        assert any("error" in msg.lower() for level, msg in messages if level == "error")

    def test_ssh_command_succeeds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful SSH connection."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        # Mock open_terminal to avoid actually opening one
        manager.open_terminal = mock.Mock(return_value=True)

        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-success",
        )

        result = manager.create_connection(conn)

        assert result is True
        assert conn.socket_path in manager.connections

    def test_ssh_with_all_options(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SSH connection with all optional parameters."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.extend(cmd)
            return mock_result

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        manager.open_terminal = mock.Mock(return_value=True)

        conn = SSHConnection(
            host="192.168.1.1",
            port=2222,
            username="admin",
            socket_path="/tmp/test-options",
            dynamic_port=1080,
            identity_file="~/.ssh/id_rsa",
        )

        result = manager.create_connection(conn)

        assert result is True
        assert "-p" in captured_cmd
        assert "2222" in captured_cmd
        assert "-D" in captured_cmd
        assert "1080" in captured_cmd
        assert "-i" in captured_cmd

    def test_no_term_skips_terminal(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that no_term=True skips terminal opening."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        terminal_opened = []
        manager.open_terminal = lambda x: terminal_opened.append(x) or True

        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-noterm",
            no_term=True,
        )

        result = manager.create_connection(conn)

        assert result is True
        assert len(terminal_opened) == 0

    def test_exception_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception handling during connection creation."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Command failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-exception",
        )

        result = manager.create_connection(conn)

        assert result is False

    def test_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception logging during connection creation."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(("debug", msg))

            def exception(self, msg):
                messages.append(("exception", msg))

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Command failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-exception-log",
        )

        result = manager.create_connection(conn)

        assert result is False
        assert any("exception" in level for level, msg in messages)

    def test_creates_directories_when_not_exists(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that connection and download directories are created."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(msg)

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())
        monkeypatch.setattr("lazyssh.ssh.Confirm.ask", lambda x: True)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.log_ssh_connection", lambda *args, **kwargs: None)
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        manager.open_terminal = mock.Mock(return_value=True)

        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-dirs",
        )

        # Remove directories if they exist (they were created by SSHConnection)
        import shutil

        if Path(conn.connection_dir).exists():
            shutil.rmtree(conn.connection_dir)

        manager.create_connection(conn)

        # Directory creation is logged
        assert any("directory" in msg.lower() for msg in messages)


class TestCheckConnection:
    """Tests for check_connection method."""

    def test_socket_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check when socket file doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()

        result = manager.check_connection("/tmp/nonexistent-socket")

        assert result is False

    def test_socket_not_found_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check when socket file doesn't exist with logging."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(msg)

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())

        manager = SSHManager()

        result = manager.check_connection("/tmp/nonexistent-socket-log")

        assert result is False
        assert any("not found" in msg.lower() for msg in messages)

    def test_connection_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check when connection is active."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        # Create a socket file
        socket_path = "/tmp/test-check-active"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()

        result = manager.check_connection(socket_path)

        assert result is True

        # Cleanup
        Path(socket_path).unlink()

    def test_connection_inactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check when connection is not active."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        socket_path = "/tmp/test-check-inactive"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()

        result = manager.check_connection(socket_path)

        assert result is False

        # Cleanup
        Path(socket_path).unlink()

    def test_connection_check_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connection check logging."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(msg)

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())

        socket_path = "/tmp/test-check-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()

        result = manager.check_connection(socket_path)

        assert result is True
        assert any("successful" in msg.lower() for msg in messages)

        # Cleanup
        Path(socket_path).unlink()

    def test_connection_check_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception handling during connection check."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        socket_path = "/tmp/test-check-exception"
        Path(socket_path).touch()

        def mock_run(*args, **kwargs):
            raise OSError("Check failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()

        result = manager.check_connection(socket_path)

        assert result is False

        # Cleanup
        Path(socket_path).unlink()


class TestCreateTunnel:
    """Tests for create_tunnel method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel creation when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.create_tunnel("/tmp/nonexistent", 8080, "localhost", 80)

        assert result is False

    def test_forward_tunnel_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful forward tunnel creation."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.log_tunnel_creation", lambda *args, **kwargs: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-tunnel",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 8080, "localhost", 80, reverse=False)

        assert result is True
        assert len(conn.tunnels) == 1
        assert conn.tunnels[0].type == "forward"

    def test_reverse_tunnel_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful reverse tunnel creation."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.log_tunnel_creation", lambda *args, **kwargs: None)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.append(cmd)
            result = mock.Mock()
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-rtunnel",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 9090, "localhost", 90, reverse=True)

        assert result is True
        assert "-R" in captured_cmd[0]
        assert conn.tunnels[0].type == "reverse"

    def test_tunnel_creation_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel creation failure."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.log_tunnel_creation", lambda *args, **kwargs: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Port already in use"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-tunnel-fail",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 8080, "localhost", 80)

        assert result is False
        assert len(conn.tunnels) == 0

    def test_tunnel_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception handling during tunnel creation."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Tunnel failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-tunnel-exc",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 8080, "localhost", 80)

        assert result is False


class TestCloseTunnel:
    """Tests for close_tunnel method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.close_tunnel("/tmp/nonexistent", "1")

        assert result is False

    def test_tunnel_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel when tunnel doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-notfound",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "999")

        assert result is False

    def test_close_forward_tunnel_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful forward tunnel close."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.append(cmd)
            result = mock.Mock()
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-forward",
        )
        conn.add_tunnel(8080, "localhost", 80, is_reverse=False)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is True
        assert "-L" in captured_cmd[0]
        assert len(conn.tunnels) == 0

    def test_close_reverse_tunnel_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful reverse tunnel close."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        captured_cmd = []

        def mock_run(cmd, **kwargs):
            captured_cmd.append(cmd)
            result = mock.Mock()
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-reverse",
        )
        conn.add_tunnel(9090, "localhost", 90, is_reverse=True)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is True
        assert "-R" in captured_cmd[0]

    def test_close_tunnel_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel close failure."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Failed to cancel"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-fail",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is False

    def test_close_tunnel_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception handling during tunnel close."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Close failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-exc",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is False


class TestOpenTerminalNative:
    """Tests for open_terminal_native method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal open when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.open_terminal_native("/tmp/nonexistent")

        assert result is False

    def test_connection_not_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal open when connection not active."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-inactive",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=False)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False

    def test_terminal_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful terminal session."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-success",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is True

    def test_terminal_with_shell(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal with custom shell."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        captured_args = []

        def mock_run(args, **kwargs):
            captured_args.extend(args)
            result = mock.Mock()
            result.returncode = 0
            return result

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-shell",
            shell="/bin/zsh",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is True
        assert "/bin/zsh" in captured_args

    def test_terminal_non_zero_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal session with non-zero exit code."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-exit",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False

    def test_terminal_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception during terminal session."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Terminal failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-exc",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False


class TestOpenTerminalTerminator:
    """Tests for open_terminal_terminator method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminator open when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.open_terminal_terminator("/tmp/nonexistent")

        assert result is False

    def test_terminator_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when terminator is not installed."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("shutil.which", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-noterm",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False

    def test_terminator_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful terminator launch."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_process = mock.Mock()
        mock_process.poll.return_value = None  # Still running

        monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: mock_process)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-terminator",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is True

    def test_terminator_with_shell(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminator launch with custom shell."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")
        monkeypatch.setattr("time.sleep", lambda x: None)

        captured_args = []

        def mock_popen(args, **kwargs):
            captured_args.extend(args)
            proc = mock.Mock()
            proc.poll.return_value = None
            return proc

        monkeypatch.setattr("subprocess.Popen", mock_popen)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-shell2",
            shell="/bin/zsh",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is True
        assert any("/bin/zsh" in str(arg) for arg in captured_args)

    def test_terminator_immediate_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when terminator exits immediately."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_process = mock.Mock()
        mock_process.poll.return_value = 1  # Already exited
        mock_process.communicate.return_value = (b"", b"Error starting")

        monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: mock_process)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-fail",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False

    def test_terminator_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception during terminator launch."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        def mock_popen(*args, **kwargs):
            raise OSError("Popen failed")

        monkeypatch.setattr("subprocess.Popen", mock_popen)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-exc2",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False


class TestOpenTerminal:
    """Tests for open_terminal method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal open when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.open_terminal("/tmp/nonexistent")

        assert result is False

    def test_connection_not_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal open when connection not active."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-inactive",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=False)

        result = manager.open_terminal(conn.socket_path)

        assert result is False

    def test_terminator_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with terminal_method='terminator'."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.display_info", lambda x: None)

        manager = SSHManager()
        manager.terminal_method = "terminator"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-term",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=False)

        result = manager.open_terminal(conn.socket_path)

        assert result is False
        manager.open_terminal_terminator.assert_called_once()

    def test_terminator_method_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminator method success."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()
        manager.terminal_method = "terminator"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-term-ok",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True

    def test_native_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test with terminal_method='native'."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()
        manager.terminal_method = "native"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-native",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        manager.open_terminal_native.assert_called_once()

    def test_auto_with_terminator_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test auto mode with terminator available."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-auto-term",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        manager.open_terminal_terminator.assert_called_once()

    def test_auto_terminator_fails_fallback_native(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test auto mode fallback to native when terminator fails."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-auto-fallback",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=False)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        manager.open_terminal_native.assert_called_once()

    def test_auto_no_terminator_uses_native(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test auto mode uses native when terminator not available."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("shutil.which", lambda x: None)

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-auto-native",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        manager.open_terminal_native.assert_called_once()

    def test_exception_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception handling in open_terminal."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)

        manager = SSHManager()
        manager.terminal_method = "native"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-exc",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(side_effect=OSError("Failed"))

        result = manager.open_terminal(conn.socket_path)

        assert result is False


class TestCloseConnection:
    """Tests for close_connection method."""

    def test_connection_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close when connection doesn't exist."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()

        result = manager.close_connection("/tmp/nonexistent")

        assert result is False

    def test_socket_already_gone(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close when socket file no longer exists."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-gone",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert conn.socket_path not in manager.connections

    def test_close_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful connection close."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        socket_path = "/tmp/test-close-success"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert conn.socket_path not in manager.connections

        # Cleanup
        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_with_tunnels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close connection also closes tunnels."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        socket_path = "/tmp/test-close-tunnels"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        close_tunnel_calls = []
        manager.close_tunnel = lambda s, t: close_tunnel_calls.append((s, t)) or True

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert len(close_tunnel_calls) == 1

        # Cleanup
        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_fails_no_such_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close when SSH command fails with 'No such file'."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        socket_path = "/tmp/test-close-nosuch"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No such file or directory"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert conn.socket_path not in manager.connections

        # Cleanup
        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_fails_other_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close when SSH command fails with other error."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        socket_path = "/tmp/test-close-error"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True  # Still returns True for cleanup
        assert conn.socket_path not in manager.connections

        # Cleanup
        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test exception during close."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        socket_path = "/tmp/test-close-exc"
        Path(socket_path).touch()

        def mock_run(*args, **kwargs):
            raise OSError("Close failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True  # Still returns True for cleanup
        assert conn.socket_path not in manager.connections

        # Cleanup
        if Path(socket_path).exists():
            Path(socket_path).unlink()


class TestListConnections:
    """Tests for list_connections method."""

    def test_returns_copy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that list_connections returns a copy."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-list",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.list_connections()

        assert result is not manager.connections
        assert result == manager.connections

    def test_logs_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that list_connections logs the count."""
        messages: list[str] = []

        class MockLogger:
            def debug(self, msg):
                messages.append(msg)

        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", MockLogger())

        manager = SSHManager()

        manager.list_connections()

        assert any("listing" in msg.lower() for msg in messages)


class TestSetTerminalMethod:
    """Tests for set_terminal_method method."""

    def test_valid_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test setting valid terminal method."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        manager = SSHManager()

        result = manager.set_terminal_method("native")

        assert result is True
        assert manager.terminal_method == "native"

    def test_invalid_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test setting invalid terminal method."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.display_info", lambda x: None)

        manager = SSHManager()
        manager.terminal_method = "auto"

        result = manager.set_terminal_method("invalid")

        assert result is False
        assert manager.terminal_method == "auto"  # Unchanged


class TestGetCurrentTerminalMethod:
    """Tests for get_current_terminal_method method."""

    def test_returns_current_method(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting current terminal method."""
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", None)

        manager = SSHManager()
        manager.terminal_method = "native"

        result = manager.get_current_terminal_method()

        assert result == "native"


class TestLoggingBranches:
    """Tests for logging branches in SSH module."""

    def test_check_connection_failed_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connection check failure logging (line 178)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        socket_path = "/tmp/test-check-fail-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        result = manager.check_connection(socket_path)

        assert result is False
        assert any("failed" in msg.lower() for level, msg in mock_logger.messages)

        Path(socket_path).unlink()

    def test_check_connection_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connection check exception logging (line 184)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        socket_path = "/tmp/test-check-exc-log"
        Path(socket_path).touch()

        def mock_run(*args, **kwargs):
            raise OSError("Check failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        result = manager.check_connection(socket_path)

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

        Path(socket_path).unlink()

    def test_create_tunnel_not_found_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel creation logging when connection not found (line 200)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.create_tunnel("/tmp/nonexistent", 8080, "localhost", 80)

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_create_tunnel_debug_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel command debug logging (line 215)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.log_tunnel_creation", lambda *args, **kwargs: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-tunnel-debug",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 8080, "localhost", 80)

        assert result is True
        assert any(
            "command" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_create_tunnel_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test tunnel creation exception logging (line 237)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Tunnel failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-tunnel-exc-log",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.create_tunnel(conn.socket_path, 8080, "localhost", 80)

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

    def test_close_tunnel_not_found_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel connection not found logging (line 246)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.close_tunnel("/tmp/nonexistent", "1")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_close_tunnel_tunnel_not_found_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test close tunnel when tunnel not found logging (line 256)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-tnl-notfound-log",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "999")

        assert result is False
        assert any("not found" in msg.lower() for level, msg in mock_logger.messages)

    def test_close_tunnel_debug_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel command debug logging (line 271)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-tnl-debug",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is True
        assert any(
            "command" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_close_tunnel_fails_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel failure logging (line 279)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Failed to cancel"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-tnl-fail-log",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_close_tunnel_success_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel success logging (line 285)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-tnl-success-log",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is True
        assert any(level == "info" for level, msg in mock_logger.messages)

    def test_close_tunnel_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close tunnel exception logging (line 291)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Close failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-tnl-exc-log",
        )
        conn.add_tunnel(8080, "localhost", 80)
        manager.connections[conn.socket_path] = conn

        result = manager.close_tunnel(conn.socket_path, "1")

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

    def test_open_terminal_native_not_found_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test native terminal not found logging (line 305)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.open_terminal_native("/tmp/nonexistent")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_open_terminal_native_inactive_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test native terminal inactive logging (line 314)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-inactive-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=False)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False
        assert any("not active" in msg.lower() for level, msg in mock_logger.messages)

    def test_open_terminal_native_info_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test native terminal info logging (line 339)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-info-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is True
        assert any(level == "info" for level, msg in mock_logger.messages)

    def test_open_terminal_native_success_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test native terminal success logging (line 350)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-success-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is True
        assert any("completed" in msg.lower() for level, msg in mock_logger.messages)

    def test_open_terminal_native_warning_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test native terminal warning logging on non-zero exit (line 355)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        mock_result = mock.Mock()
        mock_result.returncode = 1

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-warn-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False
        assert any(level == "warning" for level, msg in mock_logger.messages)

    def test_open_terminal_native_exception_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test native terminal exception logging (line 367)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        def mock_run(*args, **kwargs):
            raise OSError("Terminal failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term-exc-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_native(conn.socket_path)

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

    def test_open_terminal_terminator_not_found_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test terminator terminal not found logging (line 380)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.open_terminal_terminator("/tmp/nonexistent")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_open_terminal_terminator_inactive_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test terminator terminal inactive logging (lines 387-392)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term2-inactive-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=False)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False
        assert any("not active" in msg.lower() for level, msg in mock_logger.messages)

    def test_open_terminal_terminator_not_installed_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test terminator not installed logging (line 398)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("shutil.which", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term2-notfound-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False
        assert any(
            "not found" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_open_terminal_terminator_info_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminator terminal info logging (line 415)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_process = mock.Mock()
        mock_process.poll.return_value = None

        monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: mock_process)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term2-info-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is True
        assert any(level == "info" for level, msg in mock_logger.messages)

    def test_open_terminal_terminator_fail_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test terminator failure logging (line 438)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")
        monkeypatch.setattr("time.sleep", lambda x: None)

        mock_process = mock.Mock()
        mock_process.poll.return_value = 1
        mock_process.communicate.return_value = (b"", b"Error starting")

        monkeypatch.setattr("subprocess.Popen", lambda *args, **kwargs: mock_process)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term2-fail-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_open_terminal_terminator_exception_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test terminator exception logging (line 444)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        def mock_popen(*args, **kwargs):
            raise OSError("Popen failed")

        monkeypatch.setattr("subprocess.Popen", mock_popen)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-term2-exc-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)

        result = manager.open_terminal_terminator(conn.socket_path)

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

    def test_open_terminal_not_found_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test open_terminal not found logging (line 463)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.open_terminal("/tmp/nonexistent")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_open_terminal_inactive_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test open_terminal inactive logging (line 472)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-inactive-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=False)

        result = manager.open_terminal(conn.socket_path)

        assert result is False
        assert any("not active" in msg.lower() for level, msg in mock_logger.messages)

    def test_open_terminal_debug_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test open_terminal debug logging (line 479)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        manager = SSHManager()
        manager.terminal_method = "native"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-debug-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        assert any(
            "configured" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_open_terminal_auto_terminator_debug_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test open_terminal auto mode terminator debug logging (line 496)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-auto-debug-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        assert any(
            "auto mode" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_open_terminal_auto_fallback_debug_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test open_terminal auto mode fallback debug logging (line 500)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/terminator")

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-fallback-debug-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_terminator = mock.Mock(return_value=False)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        assert any(
            "falling back" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

    def test_open_terminal_auto_no_terminator_debug_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test open_terminal auto mode no terminator debug logging (line 507)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("shutil.which", lambda x: None)

        manager = SSHManager()
        manager.terminal_method = "auto"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-noterm-debug-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(return_value=True)

        result = manager.open_terminal(conn.socket_path)

        assert result is True
        assert any(
            "not available" in msg.lower()
            for level, msg in mock_logger.messages
            if level == "debug"
        )

    def test_open_terminal_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test open_terminal exception logging (line 519)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)
        monkeypatch.setattr("lazyssh.ssh.console.print", lambda *args, **kwargs: None)

        manager = SSHManager()
        manager.terminal_method = "native"
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-open-exc-log",
        )
        manager.connections[conn.socket_path] = conn
        manager.check_connection = mock.Mock(return_value=True)
        manager.open_terminal_native = mock.Mock(side_effect=OSError("Failed"))

        result = manager.open_terminal(conn.socket_path)

        assert result is False
        assert any(level == "exception" for level, msg in mock_logger.messages)

    def test_close_connection_not_found_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_connection not found logging (line 528)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_error", lambda x: None)

        manager = SSHManager()
        result = manager.close_connection("/tmp/nonexistent")

        assert result is False
        assert any(level == "error" for level, msg in mock_logger.messages)

    def test_close_connection_socket_gone_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test close_connection socket gone logging (line 541)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/test-close-gone-log",
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any("no longer exists" in msg.lower() for level, msg in mock_logger.messages)

    def test_close_connection_debug_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_connection command debug logging (line 550)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        socket_path = "/tmp/test-close-debug-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any(
            "command" in msg.lower() for level, msg in mock_logger.messages if level == "debug"
        )

        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_connection_no_file_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_connection no such file logging (line 559)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)

        socket_path = "/tmp/test-close-nofile-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "No such file or directory"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any(
            "removed" in msg.lower() for level, msg in mock_logger.messages if level == "info"
        )

        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_connection_other_error_with_logging(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test close_connection other error logging (line 563)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        socket_path = "/tmp/test-close-err-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Permission denied"

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any(level == "warning" for level, msg in mock_logger.messages)

        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_connection_success_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_connection success logging (line 571)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        socket_path = "/tmp/test-close-success-log"
        Path(socket_path).touch()

        mock_result = mock.Mock()
        mock_result.returncode = 0

        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any(
            "closed" in msg.lower() for level, msg in mock_logger.messages if level == "info"
        )

        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_close_connection_exception_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_connection exception logging (line 578)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_warning", lambda x: None)

        socket_path = "/tmp/test-close-exc-log"
        Path(socket_path).touch()

        def mock_run(*args, **kwargs):
            raise OSError("Close failed")

        monkeypatch.setattr("subprocess.run", mock_run)

        manager = SSHManager()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path=socket_path,
        )
        manager.connections[conn.socket_path] = conn

        result = manager.close_connection(conn.socket_path)

        assert result is True
        assert any(level == "exception" for level, msg in mock_logger.messages)

        if Path(socket_path).exists():
            Path(socket_path).unlink()

    def test_set_terminal_method_with_logging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test set_terminal_method logging (line 610)."""
        mock_logger = MockLogger()
        monkeypatch.setattr("lazyssh.ssh.SSH_LOGGER", mock_logger)
        monkeypatch.setattr("lazyssh.ssh.display_success", lambda x: None)

        manager = SSHManager()
        result = manager.set_terminal_method("native")

        assert result is True
        assert any(
            "changed" in msg.lower() for level, msg in mock_logger.messages if level == "info"
        )
