"""Tests for __main__ module - CLI entry point, status display, connection handling."""

from unittest import mock

import pytest
from click.testing import CliRunner

from lazyssh import __main__ as main_module
from lazyssh.__main__ import main
from lazyssh.models import SSHConnection


class TestShowStatus:
    """Tests for show_status function."""

    def test_show_status_no_configs_no_connections(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test show_status with no configs or connections."""
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda: {})
        main_module.ssh_manager.connections.clear()
        main_module.show_status()

    def test_show_status_with_configs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test show_status with saved configs."""
        monkeypatch.setattr(
            "lazyssh.__main__.load_configs",
            lambda: {"server1": {"host": "192.168.1.1", "port": 22}},
        )
        main_module.ssh_manager.connections.clear()
        main_module.show_status()

    def test_show_status_with_connections(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test show_status with active connections."""
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda: {})
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/teststatus",
        )
        main_module.ssh_manager.connections["/tmp/teststatus"] = conn
        try:
            main_module.show_status()
        finally:
            main_module.ssh_manager.connections.clear()

    def test_show_status_with_tunnels(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test show_status with connections that have tunnels."""
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda: {})
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testtunnels",
        )
        conn.add_tunnel(8080, "localhost", 80)
        main_module.ssh_manager.connections["/tmp/testtunnels"] = conn
        try:
            main_module.show_status()
        finally:
            main_module.ssh_manager.connections.clear()


class TestCloseAllConnections:
    """Tests for close_all_connections function."""

    def test_close_all_no_connections(self) -> None:
        """Test close_all_connections with no connections."""
        main_module.ssh_manager.connections.clear()
        main_module.close_all_connections()

    def test_close_all_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_all_connections with successful closure."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testclose",
        )
        main_module.ssh_manager.connections["/tmp/testclose"] = conn

        # Mock close_connection to return True
        monkeypatch.setattr(main_module.ssh_manager, "close_connection", lambda x: True)

        try:
            main_module.close_all_connections()
        finally:
            main_module.ssh_manager.connections.clear()

    def test_close_all_partial_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_all_connections with partial failure."""
        conn1 = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testclose1",
        )
        conn2 = SSHConnection(
            host="192.168.1.2",
            port=22,
            username="user",
            socket_path="/tmp/testclose2",
        )
        main_module.ssh_manager.connections["/tmp/testclose1"] = conn1
        main_module.ssh_manager.connections["/tmp/testclose2"] = conn2

        call_count = 0

        def mock_close(path):
            nonlocal call_count
            call_count += 1
            return call_count == 1  # First succeeds, second fails

        monkeypatch.setattr(main_module.ssh_manager, "close_connection", mock_close)

        try:
            main_module.close_all_connections()
        finally:
            main_module.ssh_manager.connections.clear()

    def test_close_all_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close_all_connections with exception during closure."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testexc",
        )
        main_module.ssh_manager.connections["/tmp/testexc"] = conn

        def mock_close(path: str) -> bool:
            raise OSError("Close failed")

        monkeypatch.setattr(main_module.ssh_manager, "close_connection", mock_close)

        try:
            main_module.close_all_connections()
        finally:
            main_module.ssh_manager.connections.clear()


class TestCheckActiveConnections:
    """Tests for check_active_connections function."""

    def test_no_connections(self) -> None:
        """Test check_active_connections with no connections."""
        main_module.ssh_manager.connections.clear()
        result = main_module.check_active_connections()
        assert result is True

    def test_connections_user_confirms(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check_active_connections when user confirms."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testcheck",
        )
        main_module.ssh_manager.connections["/tmp/testcheck"] = conn

        monkeypatch.setattr("rich.prompt.Confirm.ask", lambda x: True)

        try:
            result = main_module.check_active_connections()
            assert result is True
        finally:
            main_module.ssh_manager.connections.clear()

    def test_connections_user_declines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test check_active_connections when user declines."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testdecline",
        )
        main_module.ssh_manager.connections["/tmp/testdecline"] = conn

        monkeypatch.setattr("rich.prompt.Confirm.ask", lambda x: False)

        try:
            result = main_module.check_active_connections()
            assert result is False
        finally:
            main_module.ssh_manager.connections.clear()


class TestMainCLI:
    """Tests for main CLI function."""

    def test_main_help(self) -> None:
        """Test main --help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "LazySSH" in result.output

    def test_main_debug_flag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with --debug flag."""
        runner = CliRunner()

        # Mock dependencies
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))

        # Mock CommandMode.run to exit immediately
        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, ["--debug"])
        assert result.exit_code == 0

    def test_main_with_config_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with --config flag."""
        runner = CliRunner()

        # Mock dependencies
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))
        monkeypatch.setattr(
            "lazyssh.__main__.load_configs",
            lambda x=None: {"server1": {"host": "test"}},
        )
        monkeypatch.setattr("lazyssh.__main__.display_saved_configs", lambda x: None)

        # Mock CommandMode.run to exit immediately
        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, ["--config", "/tmp/test.conf"])
        assert result.exit_code == 0

    def test_main_config_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with empty config file."""
        runner = CliRunner()

        # Mock dependencies
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda x=None: {})

        # Mock CommandMode.run to exit immediately
        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, ["--config", "/tmp/empty.conf"])
        assert result.exit_code == 0

    def test_main_missing_optional_deps(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with missing optional dependencies."""
        runner = CliRunner()

        # Mock dependencies
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr(
            "lazyssh.__main__.check_dependencies",
            lambda: ([], ["Terminator"]),
        )

        # Mock CommandMode.run to exit immediately
        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_main_missing_required_deps(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main with missing required dependencies."""
        runner = CliRunner()

        # Mock dependencies
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr(
            "lazyssh.__main__.check_dependencies",
            lambda: (["OpenSSH"], []),
        )

        result = runner.invoke(main, [])
        assert result.exit_code == 1

    def test_main_exception_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main exception handling."""
        runner = CliRunner()

        def raise_exception():
            raise Exception("Test exception")

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", raise_exception)

        result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "unexpected error" in result.output.lower()


class TestSafeExit:
    """Tests for safe_exit function."""

    def test_safe_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test safe_exit calls close_all_connections and exits."""
        close_called = False

        def mock_close_all():
            nonlocal close_called
            close_called = True

        monkeypatch.setattr(main_module, "close_all_connections", mock_close_all)

        with pytest.raises(SystemExit) as exc_info:
            main_module.safe_exit()

        assert close_called
        assert exc_info.value.code == 0


class TestShowStatusWithConfigs:
    """Tests for show_status with saved configurations."""

    def test_show_status_with_saved_configs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test show_status displays saved configs."""
        # Patch at the source module since show_status imports from config
        monkeypatch.setattr(
            "lazyssh.config.load_configs",
            lambda *args, **kwargs: {"server1": {"host": "192.168.1.1", "port": 22}},
        )
        main_module.ssh_manager.connections.clear()
        main_module.show_status()


class TestMainWithNoConfigs:
    """Tests for main when no configs are found."""

    def test_main_no_configs_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main displays warning when no configs found."""
        runner = CliRunner()

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))
        # Return empty configs
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda x=None: {})

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_main_config_file_not_found_warning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main displays warning when config file not found."""
        runner = CliRunner()

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))
        # Return empty configs when path is provided
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda x=None: {})

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        result = runner.invoke(main, ["--config", "/nonexistent/path.conf"])
        assert result.exit_code == 0

    def test_main_config_flag_empty_string_no_configs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test main with --config flag but empty value and no configs found."""
        runner = CliRunner()

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))
        # Return empty configs when called
        monkeypatch.setattr("lazyssh.__main__.load_configs", lambda x=None: {})

        warning_messages: list[str] = []

        def mock_display_warning(msg):
            warning_messages.append(msg)

        monkeypatch.setattr("lazyssh.__main__.display_warning", mock_display_warning)

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock()
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        # Use --config="" to trigger the empty string case
        result = runner.invoke(main, ["--config="])
        assert result.exit_code == 0
        assert any("No saved configurations found" in msg for msg in warning_messages)


class TestMainKeyboardInterrupt:
    """Tests for KeyboardInterrupt handling in main."""

    def test_keyboard_interrupt_first_time_continue(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test first KeyboardInterrupt shows warning and continues on Enter."""
        runner = CliRunner()

        # Mock everything up to CommandMode.run which will raise KeyboardInterrupt
        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock(side_effect=KeyboardInterrupt)
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        # Mock input to simulate pressing Enter (raises EOFError in Click testing)
        monkeypatch.setattr("builtins.input", lambda x: "")

        result = runner.invoke(main, [])
        # Should return None (exit code 0) after pressing Enter
        assert result.exit_code == 0

    def test_keyboard_interrupt_second_time_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test second KeyboardInterrupt exits the application."""
        runner = CliRunner()

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock(side_effect=KeyboardInterrupt)
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        # Mock input to raise KeyboardInterrupt (simulates Ctrl+C during prompt)
        monkeypatch.setattr("builtins.input", mock.Mock(side_effect=KeyboardInterrupt))

        # Mock check_active_connections to return True (allow exit)
        monkeypatch.setattr(main_module, "check_active_connections", lambda: True)

        # Mock safe_exit to avoid actual sys.exit
        exit_called = False

        def mock_safe_exit():
            nonlocal exit_called
            exit_called = True
            raise SystemExit(0)

        monkeypatch.setattr(main_module, "safe_exit", mock_safe_exit)

        runner.invoke(main, [])
        assert exit_called

    def test_keyboard_interrupt_user_declines_exit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test second KeyboardInterrupt but user declines to exit."""
        runner = CliRunner()

        monkeypatch.setattr("lazyssh.__main__.ensure_log_directory", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.initialize_config_file", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.ensure_runtime_plugins_dir", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.display_banner", lambda: None)
        monkeypatch.setattr("lazyssh.__main__.check_dependencies", lambda: ([], []))

        mock_cmd_mode = mock.Mock()
        mock_cmd_mode.run = mock.Mock(side_effect=KeyboardInterrupt)
        monkeypatch.setattr("lazyssh.__main__.CommandMode", lambda x: mock_cmd_mode)

        # Mock input to raise KeyboardInterrupt
        monkeypatch.setattr("builtins.input", mock.Mock(side_effect=KeyboardInterrupt))

        # Mock check_active_connections to return False (user declines exit)
        monkeypatch.setattr(main_module, "check_active_connections", lambda: False)

        result = runner.invoke(main, [])
        # Should complete without calling safe_exit
        assert result.exit_code == 0
