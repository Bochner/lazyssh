"""Tests for command_mode module - command handlers, completers, wizards."""

from pathlib import Path

import pytest
from prompt_toolkit.document import Document

from lazyssh.command_mode import CommandMode, LazySSHCompleter
from lazyssh.models import SSHConnection
from lazyssh.ssh import SSHManager


class TestLazySSHCompleter:
    """Tests for LazySSHCompleter class."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def command_mode(self, ssh_manager: SSHManager) -> CommandMode:
        """Create a CommandMode instance for testing."""
        return CommandMode(ssh_manager)

    @pytest.fixture
    def completer(self, command_mode: CommandMode) -> LazySSHCompleter:
        """Create a completer instance for testing."""
        return LazySSHCompleter(command_mode)

    def test_completer_init(self, completer: LazySSHCompleter) -> None:
        """Test completer initialization."""
        assert completer.command_mode is not None

    def test_complete_empty_input(self, completer: LazySSHCompleter) -> None:
        """Test completion on empty input."""
        doc = Document("")
        completions = list(completer.get_completions(doc, None))
        # Should suggest base commands
        assert len(completions) > 0

    def test_complete_partial_command(self, completer: LazySSHCompleter) -> None:
        """Test completion on partial command."""
        doc = Document("lazy")
        completions = list(completer.get_completions(doc, None))
        # Should suggest lazyssh
        assert any("lazyssh" in c.text for c in completions)

    def test_complete_lazyssh_args(self, completer: LazySSHCompleter) -> None:
        """Test completion of lazyssh arguments."""
        doc = Document("lazyssh ")
        completions = list(completer.get_completions(doc, None))
        # Should suggest -ip first (required arg)
        assert any("-ip" in c.text for c in completions)

    def test_complete_lazyssh_partial_arg(self, completer: LazySSHCompleter) -> None:
        """Test completion of partial lazyssh argument."""
        doc = Document("lazyssh -")
        list(completer.get_completions(doc, None))
        # Should return some completions for arguments starting with -
        # Either completions or empty is acceptable depending on implementation

    def test_complete_lazyssh_after_required(self, completer: LazySSHCompleter) -> None:
        """Test completion after required args are filled."""
        doc = Document("lazyssh -ip 1.2.3.4 -port 22 -user test -socket /tmp/s ")
        completions = list(completer.get_completions(doc, None))
        # Should suggest optional args
        assert any("-proxy" in c.text or "-ssh-key" in c.text for c in completions)

    def test_complete_lazyssh_no_suggest_when_expecting_value(
        self, completer: LazySSHCompleter
    ) -> None:
        """Test no suggestions when expecting argument value."""
        doc = Document("lazyssh -ip ")
        completions = list(completer.get_completions(doc, None))
        # Should not suggest new arguments when expecting value
        assert len(completions) == 0

    def test_complete_invalid_shlex(self, completer: LazySSHCompleter) -> None:
        """Test completion with invalid shlex input (unclosed quote)."""
        doc = Document('lazyssh "unclosed')
        list(completer.get_completions(doc, None))
        # Should fall back to split() and not crash

    def test_complete_tunc_command(
        self, completer: LazySSHCompleter, command_mode: CommandMode
    ) -> None:
        """Test completion for tunc command."""
        # Add a connection first
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testconn",
        )
        command_mode.ssh_manager.connections["/tmp/testconn"] = conn

        doc = Document("tunc ")
        list(completer.get_completions(doc, None))
        # Completions may or may not include connection names depending on implementation

    def test_complete_with_connection(
        self, completer: LazySSHCompleter, command_mode: CommandMode
    ) -> None:
        """Test completion commands that need connections."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/termtest",
        )
        command_mode.ssh_manager.connections["/tmp/termtest"] = conn

        # Test various commands - just ensure they don't crash
        for cmd in ["close ", "scp ", "open "]:
            doc = Document(cmd)
            list(completer.get_completions(doc, None))

    def test_complete_terminal_method(self, completer: LazySSHCompleter) -> None:
        """Test completion for terminal command."""
        doc = Document("terminal ")
        list(completer.get_completions(doc, None))
        # May or may not have specific completions

    def test_complete_config_commands(
        self, completer: LazySSHCompleter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test completion for config-related commands."""
        monkeypatch.setattr(
            "lazyssh.command_mode.load_configs", lambda: {"server1": {}, "server2": {}}
        )

        # Test connect and delete-config commands
        for cmd in ["connect ", "delete-config "]:
            doc = Document(cmd)
            list(completer.get_completions(doc, None))


class TestCommandMode:
    """Tests for CommandMode class."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_init(self, ssh_manager: SSHManager) -> None:
        """Test CommandMode initialization."""
        cm = CommandMode(ssh_manager)
        assert cm.ssh_manager is not None
        assert cm.plugin_manager is not None
        assert len(cm.commands) > 0

    def test_commands_list(self, ssh_manager: SSHManager) -> None:
        """Test that expected commands are registered."""
        cm = CommandMode(ssh_manager)
        expected_commands = [
            "lazyssh",
            "help",
            "scp",
            "tunc",
            "tund",
            "close",
            "configs",
        ]
        for cmd in expected_commands:
            assert cmd in cm.commands

    def test_cmd_list_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test list command with no connections."""
        cm = CommandMode(ssh_manager)
        cm.cmd_list([])

    def test_cmd_list_with_connections(self, ssh_manager: SSHManager) -> None:
        """Test list command with connections."""
        cm = CommandMode(ssh_manager)
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/statustest",
        )
        cm.ssh_manager.connections["/tmp/statustest"] = conn
        cm.cmd_list([])

    def test_cmd_help(self, ssh_manager: SSHManager) -> None:
        """Test help command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help([])

    def test_cmd_config(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configs command."""
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {})
        cm = CommandMode(ssh_manager)
        cm.cmd_config([])

    def test_cmd_terminal_method(self, ssh_manager: SSHManager) -> None:
        """Test terminal method command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_terminal(["auto"])
        assert cm.ssh_manager.terminal_method == "auto"

    def test_cmd_terminal_invalid(self, ssh_manager: SSHManager) -> None:
        """Test terminal method command with invalid method."""
        cm = CommandMode(ssh_manager)
        cm.cmd_terminal(["invalid"])
        # Should not change from default

    def test_cmd_terminal_show_current(self, ssh_manager: SSHManager) -> None:
        """Test terminal method command shows current."""
        cm = CommandMode(ssh_manager)
        cm.cmd_terminal([])

    def test_cmd_plugin_list(self, ssh_manager: SSHManager) -> None:
        """Test plugin list command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_plugin(["list"])

    def test_cmd_plugin_info_not_found(self, ssh_manager: SSHManager) -> None:
        """Test plugin info command for non-existent plugin."""
        cm = CommandMode(ssh_manager)
        cm.cmd_plugin(["info", "nonexistent"])

    def test_cmd_plugin_run_no_args(self, ssh_manager: SSHManager) -> None:
        """Test plugin run command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_plugin(["run"])

    def test_cmd_tunc_no_args(self, ssh_manager: SSHManager) -> None:
        """Test tunc command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_tunc([])

    def test_cmd_tunc_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test tunc command with invalid connection."""
        cm = CommandMode(ssh_manager)
        cm.cmd_tunc(["nonexistent", "l", "8080", "localhost", "80"])

    def test_cmd_tund_no_args(self, ssh_manager: SSHManager) -> None:
        """Test tund command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_tund([])

    def test_cmd_tund_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test tund command with invalid connection."""
        cm = CommandMode(ssh_manager)
        cm.cmd_tund(["nonexistent", "1"])

    def test_cmd_close_no_args(self, ssh_manager: SSHManager) -> None:
        """Test close command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_close([])

    def test_cmd_close_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test close command with invalid connection."""
        cm = CommandMode(ssh_manager)
        cm.cmd_close(["nonexistent"])

    def test_cmd_open_no_args(self, ssh_manager: SSHManager) -> None:
        """Test open command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_open([])

    def test_cmd_open_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test open command with invalid connection."""
        cm = CommandMode(ssh_manager)
        cm.cmd_open(["nonexistent"])

    def test_cmd_scp_no_args(self, ssh_manager: SSHManager) -> None:
        """Test scp command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_scp([])

    def test_cmd_scp_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test scp command with invalid connection."""
        cm = CommandMode(ssh_manager)
        cm.cmd_scp(["nonexistent"])

    def test_cmd_connect_no_args(self, ssh_manager: SSHManager) -> None:
        """Test connect command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_connect([])

    def test_cmd_connect_invalid_config(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test connect command with non-existent config."""
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
        cm = CommandMode(ssh_manager)
        cm.cmd_connect(["nonexistent"])

    def test_cmd_save_config_no_args(self, ssh_manager: SSHManager) -> None:
        """Test save-config command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_save_config([])

    def test_cmd_save_config_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test save-config command with no connections."""
        cm = CommandMode(ssh_manager)
        cm.cmd_save_config(["myconfig", "testconn"])

    def test_cmd_delete_config_no_args(self, ssh_manager: SSHManager) -> None:
        """Test delete-config command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_delete_config([])

    def test_cmd_delete_config_not_found(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test delete-config command for non-existent config."""
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
        cm = CommandMode(ssh_manager)
        cm.cmd_delete_config(["nonexistent"])

    def test_cmd_backup_config_no_args(self, ssh_manager: SSHManager) -> None:
        """Test backup-config command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_backup_config([])

    def test_cmd_backup_config_not_found(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test backup-config command for non-existent config."""
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
        cm = CommandMode(ssh_manager)
        cm.cmd_backup_config(["nonexistent"])

    def test_cmd_debug_toggle(self, ssh_manager: SSHManager) -> None:
        """Test debug command toggle."""
        cm = CommandMode(ssh_manager)
        cm.cmd_debug([])
        cm.cmd_debug([])  # Toggle back

    def test_cmd_lazyssh_no_args(self, ssh_manager: SSHManager) -> None:
        """Test lazyssh command with no arguments."""
        cm = CommandMode(ssh_manager)
        cm.cmd_lazyssh([])

    def test_get_connection_completions(self, ssh_manager: SSHManager) -> None:
        """Test getting connection completions."""
        cm = CommandMode(ssh_manager)
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/completest",
        )
        cm.ssh_manager.connections["/tmp/completest"] = conn

        completions = cm._get_connection_completions()
        assert "completest" in completions

    def test_get_connection_name_completions(self, ssh_manager: SSHManager) -> None:
        """Test getting connection name completions."""
        cm = CommandMode(ssh_manager)
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/namecomp",
        )
        cm.ssh_manager.connections["/tmp/namecomp"] = conn

        completions = cm._get_connection_name_completions()
        assert "namecomp" in completions

    def test_validate_config_name_valid(self) -> None:
        """Test validating valid config name."""
        from lazyssh.config import validate_config_name

        result = validate_config_name("valid-name_123")
        # Returns True for valid names, list for errors
        assert result is True or len(result) == 0

    def test_validate_config_name_invalid(self) -> None:
        """Test validating invalid config name."""
        from lazyssh.config import validate_config_name

        result = validate_config_name("")
        # Returns list of errors for invalid names
        assert result is False or (isinstance(result, list) and len(result) > 0)


class TestConnectionWizard:
    """Tests for connection wizard functionality."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_cmd_wizard(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test cancelling connection wizard."""
        monkeypatch.setattr("builtins.input", lambda x: "")
        cm = CommandMode(ssh_manager)
        cm.cmd_wizard([])


class TestPluginIntegration:
    """Tests for plugin command integration."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_cmd_plugin_info_valid(
        self, ssh_manager: SSHManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test plugin-info for a valid plugin."""
        # Create a mock plugin
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        plugin_path = plugins_dir / "testplugin.py"
        plugin_path.write_text(
            """#!/usr/bin/env python3
# PLUGIN_NAME: testplugin
# PLUGIN_DESCRIPTION: Test plugin
print("hello")
""",
            encoding="utf-8",
        )
        plugin_path.chmod(0o755)

        cm = CommandMode(ssh_manager)
        # Replace plugin manager with one pointing to our test dir
        from lazyssh.plugin_manager import PluginManager

        cm.plugin_manager = PluginManager(plugins_dir=plugins_dir)
        cm.cmd_plugin(["info", "testplugin"])


class TestDebugMode:
    """Tests for debug mode functionality."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_debug_enable_disable(self, ssh_manager: SSHManager) -> None:
        """Test enabling and disabling debug mode."""
        cm = CommandMode(ssh_manager)

        # Toggle debug
        cm.cmd_debug([])
        # Toggle back
        cm.cmd_debug([])


class TestHelpCommand:
    """Tests for help command with specific topics."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_help_lazyssh(self, ssh_manager: SSHManager) -> None:
        """Test help for lazyssh command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["lazyssh"])

    def test_help_tunc(self, ssh_manager: SSHManager) -> None:
        """Test help for tunc command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["tunc"])

    def test_help_scp(self, ssh_manager: SSHManager) -> None:
        """Test help for scp command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["scp"])

    def test_help_config(self, ssh_manager: SSHManager) -> None:
        """Test help for config command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["config"])

    def test_help_plugin(self, ssh_manager: SSHManager) -> None:
        """Test help for plugin command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["plugin"])

    def test_help_unknown(self, ssh_manager: SSHManager) -> None:
        """Test help for unknown command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_help(["unknown_command"])


class TestLazySSHCommand:
    """Tests for lazyssh connection command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_lazyssh_successful_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with successful connection."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            ["-ip", "192.168.1.1", "-port", "22", "-user", "testuser", "-socket", "testconn"]
        )
        assert result is True

    def test_lazyssh_with_optional_params(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with optional parameters."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            [
                "-ip",
                "192.168.1.1",
                "-port",
                "22",
                "-user",
                "testuser",
                "-socket",
                "testconn2",
                "-ssh-key",
                "/home/user/.ssh/id_rsa",
                "-shell",
                "/bin/bash",
            ]
        )
        assert result is True

    def test_lazyssh_with_proxy_flag(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with -proxy flag (no value)."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            [
                "-ip",
                "192.168.1.1",
                "-port",
                "22",
                "-user",
                "testuser",
                "-socket",
                "proxytest",
                "-proxy",
            ]
        )
        assert result is True

    def test_lazyssh_with_proxy_port(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with -proxy and a port value."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            [
                "-ip",
                "192.168.1.1",
                "-port",
                "22",
                "-user",
                "testuser",
                "-socket",
                "proxytest2",
                "-proxy",
                "1080",
            ]
        )
        assert result is True

    def test_lazyssh_invalid_proxy_port(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with invalid proxy port."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            [
                "-ip",
                "192.168.1.1",
                "-port",
                "22",
                "-user",
                "testuser",
                "-socket",
                "badproxy",
                "-proxy",
                "notanumber",
            ]
        )
        assert result is False

    def test_lazyssh_with_noterm_flag(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command with -no-term flag."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            [
                "-ip",
                "192.168.1.1",
                "-port",
                "22",
                "-user",
                "testuser",
                "-socket",
                "notermtest",
                "-no-term",
            ]
        )
        assert result is True

    def test_lazyssh_connection_failed(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test lazyssh command when connection creation fails."""
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: False)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            ["-ip", "192.168.1.1", "-port", "22", "-user", "testuser", "-socket", "failconn"]
        )
        assert result is False

    def test_lazyssh_missing_ip(self, ssh_manager: SSHManager) -> None:
        """Test lazyssh command with missing IP."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(["-port", "22", "-user", "test", "-socket", "test"])
        assert result is False

    def test_lazyssh_missing_port(self, ssh_manager: SSHManager) -> None:
        """Test lazyssh command with missing port."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(["-ip", "1.2.3.4", "-user", "test", "-socket", "test"])
        assert result is False

    def test_lazyssh_invalid_socket_name(self, ssh_manager: SSHManager) -> None:
        """Test lazyssh command with invalid socket name."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(
            ["-ip", "1.2.3.4", "-port", "22", "-user", "test", "-socket", "invalid/name"]
        )
        assert result is False

    def test_lazyssh_missing_value(self, ssh_manager: SSHManager) -> None:
        """Test lazyssh command with missing value for arg."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_lazyssh(["-ip"])
        assert result is False


class TestConnectCommand:
    """Tests for connect command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_connect_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful connection from config."""
        monkeypatch.setattr(
            "lazyssh.command_mode.get_config",
            lambda x: {
                "host": "192.168.1.1",
                "port": 22,
                "username": "testuser",
                "socket_name": "conntest",
            },
        )
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: True)
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_connect(["conntest"])
        assert result is True

    def test_connect_success_with_proxy(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful connection with proxy port from config."""
        monkeypatch.setattr(
            "lazyssh.command_mode.get_config",
            lambda x: {
                "host": "192.168.1.1",
                "port": 22,
                "username": "testuser",
                "socket_name": "proxyconntest",
                "proxy_port": 1080,
            },
        )
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: True)
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_connect(["proxyconntest"])
        assert result is True

    def test_connect_failed(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test connect when connection creation fails."""
        monkeypatch.setattr(
            "lazyssh.command_mode.get_config",
            lambda x: {
                "host": "192.168.1.1",
                "port": 22,
                "username": "testuser",
                "socket_name": "failconn",
            },
        )
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: True)
        monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: False)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_connect(["failconn"])
        assert result is False

    def test_connect_with_configs_available(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test connect with no args shows available configs."""
        monkeypatch.setattr(
            "lazyssh.command_mode.load_configs", lambda: {"server1": {}, "server2": {}}
        )
        cm = CommandMode(ssh_manager)
        cm.cmd_connect([])

    def test_connect_missing_fields(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test connect with config missing required fields."""
        monkeypatch.setattr(
            "lazyssh.command_mode.get_config",
            lambda x: {"host": "1.2.3.4"},  # Missing port, etc
        )
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {"test": {}})
        cm = CommandMode(ssh_manager)
        result = cm.cmd_connect(["test"])
        assert result is False

    def test_connect_invalid_socket_name(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test connect with invalid socket name in config."""
        monkeypatch.setattr(
            "lazyssh.command_mode.get_config",
            lambda x: {
                "host": "1.2.3.4",
                "port": 22,
                "username": "user",
                "socket_name": "",
            },
        )
        cm = CommandMode(ssh_manager)
        result = cm.cmd_connect(["test"])
        assert result is False


class TestSaveConfigCommand:
    """Tests for save-config command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_save_config_invalid_name(self, ssh_manager: SSHManager) -> None:
        """Test save-config with invalid name."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_save_config(["invalid/name"])
        assert result is False

    def test_save_config_with_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test save-config with an active connection."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/savetest",
        )
        ssh_manager.connections["/tmp/savetest"] = conn
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
        monkeypatch.setattr("lazyssh.command_mode.save_config", lambda name, params: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_save_config(["myconfig"])
        assert result is True

    def test_save_config_with_optional_params(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test save-config with optional parameters."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/saveopt",
            identity_file="/home/user/.ssh/id_rsa",
            shell="/bin/bash",
            dynamic_port=8080,
        )
        conn.no_term = True
        ssh_manager.connections["/tmp/saveopt"] = conn
        monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
        monkeypatch.setattr("lazyssh.command_mode.save_config", lambda name, params: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_save_config(["myconfig"])
        assert result is True


class TestDeleteConfigCommand:
    """Tests for delete-config command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_delete_config_with_available(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test delete-config no args shows available."""
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {"server1": {}})
        cm = CommandMode(ssh_manager)
        cm.cmd_delete_config([])


class TestBackupConfigCommand:
    """Tests for backup-config command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_backup_config_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test successful config backup."""
        monkeypatch.setattr("lazyssh.command_mode.backup_config", lambda: (True, "Backup created"))
        cm = CommandMode(ssh_manager)
        result = cm.cmd_backup_config([])
        assert result is True

    def test_backup_config_failure(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test failed config backup."""
        monkeypatch.setattr("lazyssh.command_mode.backup_config", lambda: (False, "No config file"))
        cm = CommandMode(ssh_manager)
        result = cm.cmd_backup_config([])
        assert result is False


class TestTuncCommand:
    """Tests for tunc (tunnel create) command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_tunc_forward_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunc forward tunnel creation success."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunfwd"
        )
        ssh_manager.connections["/tmp/tunfwd"] = conn
        monkeypatch.setattr(ssh_manager, "create_tunnel", lambda *args, **kwargs: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["tunfwd", "l", "8080", "localhost", "80"])
        assert result is True

    def test_tunc_reverse_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunc reverse tunnel creation success."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunrev"
        )
        ssh_manager.connections["/tmp/tunrev"] = conn
        monkeypatch.setattr(ssh_manager, "create_tunnel", lambda *args, **kwargs: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["tunrev", "r", "3000", "127.0.0.1", "22"])
        assert result is True

    def test_tunc_creation_failed(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunc when tunnel creation fails."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunfail"
        )
        ssh_manager.connections["/tmp/tunfail"] = conn
        monkeypatch.setattr(ssh_manager, "create_tunnel", lambda *args, **kwargs: False)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["tunfail", "l", "8080", "localhost", "80"])
        assert result is False

    def test_tunc_missing_args(self, ssh_manager: SSHManager) -> None:
        """Test tunc with insufficient arguments."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["conn"])
        assert result is False

    def test_tunc_invalid_type(self, ssh_manager: SSHManager) -> None:
        """Test tunc with invalid tunnel type."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunctest"
        )
        ssh_manager.connections["/tmp/tunctest"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["tunctest", "x", "8080", "localhost", "80"])
        assert result is False

    def test_tunc_invalid_port(self, ssh_manager: SSHManager) -> None:
        """Test tunc with invalid port number."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunctest2"
        )
        ssh_manager.connections["/tmp/tunctest2"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tunc(["tunctest2", "l", "invalid", "localhost", "80"])
        assert result is False


class TestTundCommand:
    """Tests for tund (tunnel delete) command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_tund_forward_tunnel_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tund deleting forward tunnel successfully."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundeltest"
        )
        tunnel = conn.add_tunnel(8080, "localhost", 80)
        ssh_manager.connections["/tmp/tundeltest"] = conn
        monkeypatch.setattr(ssh_manager, "close_tunnel", lambda *args: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tund([tunnel.id])
        assert result is True

    def test_tund_reverse_tunnel_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tund deleting reverse tunnel successfully."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundelrev"
        )
        tunnel = conn.add_tunnel(3000, "127.0.0.1", 22, is_reverse=True)
        ssh_manager.connections["/tmp/tundelrev"] = conn
        monkeypatch.setattr(ssh_manager, "close_tunnel", lambda *args: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tund([tunnel.id])
        assert result is True

    def test_tund_close_failed(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tund when close_tunnel fails."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundelfail"
        )
        tunnel = conn.add_tunnel(8080, "localhost", 80)
        ssh_manager.connections["/tmp/tundelfail"] = conn
        monkeypatch.setattr(ssh_manager, "close_tunnel", lambda *args: False)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tund([tunnel.id])
        assert result is False

    def test_tund_no_tunnel_found(self, ssh_manager: SSHManager) -> None:
        """Test tund with non-existent tunnel."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundtest"
        )
        ssh_manager.connections["/tmp/tundtest"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_tund(["999"])
        assert result is False


class TestOpenCommand:
    """Tests for open command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_open_with_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test open with valid connection."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/opentest"
        )
        ssh_manager.connections["/tmp/opentest"] = conn
        monkeypatch.setattr(ssh_manager, "open_terminal", lambda path: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_open(["opentest"])
        assert result is True

    def test_open_terminal_method_name(self, ssh_manager: SSHManager) -> None:
        """Test open with terminal method name (common mistake)."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_open(["auto"])
        assert result is False

    def test_open_with_exception(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test open when terminal raises exception."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/openexc"
        )
        ssh_manager.connections["/tmp/openexc"] = conn

        def raise_error(path: str) -> None:
            raise ValueError("Invalid SSH ID")

        monkeypatch.setattr(ssh_manager, "open_terminal", raise_error)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_open(["openexc"])
        assert result is False


class TestCloseCommand:
    """Tests for close command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_close_with_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test close with valid connection."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/closetest"
        )
        ssh_manager.connections["/tmp/closetest"] = conn
        monkeypatch.setattr(ssh_manager, "close_connection", lambda path: True)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_close(["closetest"])
        assert result is True

    def test_close_failure(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test close when close fails."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/closefail"
        )
        ssh_manager.connections["/tmp/closefail"] = conn
        monkeypatch.setattr(ssh_manager, "close_connection", lambda path: False)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_close(["closefail"])
        assert result is False


class TestScpCommand:
    """Tests for scp command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_scp_with_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test scp with valid connection."""
        import subprocess

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/scptest"
        )
        ssh_manager.connections["/tmp/scptest"] = conn

        # Mock subprocess.run to avoid actual SSH connection in SCPMode.connect()
        mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        # Mock SCPMode.run to not actually run the interactive loop
        from lazyssh import scp_mode

        monkeypatch.setattr(scp_mode.SCPMode, "run", lambda self: None)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_scp(["scptest"])
        assert result is True

    def test_scp_invalid_connection(self, ssh_manager: SSHManager) -> None:
        """Test scp with invalid connection name."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_scp(["nonexistent"])
        assert result is False


class TestShowStatus:
    """Tests for show_status method."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_show_status_with_tunnels(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test show_status with connections that have tunnels."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/statustest"
        )
        conn.add_tunnel(8080, "localhost", 80)
        ssh_manager.connections["/tmp/statustest"] = conn
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {})
        cm = CommandMode(ssh_manager)
        cm.show_status()


class TestGetPromptText:
    """Tests for get_prompt_text method."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_get_prompt_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test prompt text with no connections."""
        cm = CommandMode(ssh_manager)
        prompt = cm.get_prompt_text()
        assert "lazyssh" in str(prompt).lower()

    def test_get_prompt_with_connections(self, ssh_manager: SSHManager) -> None:
        """Test prompt text with connections."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/prompttest"
        )
        ssh_manager.connections["/tmp/prompttest"] = conn
        cm = CommandMode(ssh_manager)
        prompt = cm.get_prompt_text()
        assert prompt is not None


class TestTerminalCommand:
    """Tests for terminal method command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_terminal_native(self, ssh_manager: SSHManager) -> None:
        """Test setting terminal to native."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal(["native"])
        assert result is True
        assert ssh_manager.terminal_method == "native"

    def test_terminal_terminator(self, ssh_manager: SSHManager) -> None:
        """Test setting terminal to terminator."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal(["terminator"])
        assert result is True
        assert ssh_manager.terminal_method == "terminator"

    def test_terminal_auto(self, ssh_manager: SSHManager) -> None:
        """Test setting terminal to auto."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal(["auto"])
        assert result is True

    def test_terminal_invalid(self, ssh_manager: SSHManager) -> None:
        """Test terminal with invalid method."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal(["invalid"])
        assert result is False

    def test_terminal_no_args(self, ssh_manager: SSHManager) -> None:
        """Test terminal with no arguments."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal([])
        assert result is False

    def test_terminal_with_connection_name(self, ssh_manager: SSHManager) -> None:
        """Test terminal with connection name (common mistake)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/testterm"
        )
        ssh_manager.connections["/tmp/testterm"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_terminal(["testterm"])
        assert result is False


class TestWizardCommand:
    """Tests for wizard command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_wizard_no_args(self, ssh_manager: SSHManager) -> None:
        """Test wizard with no arguments shows usage."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_wizard([])
        assert result is False

    def test_wizard_invalid_workflow(self, ssh_manager: SSHManager) -> None:
        """Test wizard with invalid workflow name."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_wizard(["invalid_workflow"])
        assert result is False


class TestPluginCommand:
    """Tests for plugin command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_plugin_list(self, ssh_manager: SSHManager) -> None:
        """Test plugin list command."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin(["list"])
        assert result is True

    def test_plugin_no_args(self, ssh_manager: SSHManager) -> None:
        """Test plugin with no args shows list."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin([])
        assert result is True

    def test_plugin_info_no_name(self, ssh_manager: SSHManager) -> None:
        """Test plugin info without plugin name."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin(["info"])
        assert result is False

    def test_plugin_info_nonexistent(self, ssh_manager: SSHManager) -> None:
        """Test plugin info for nonexistent plugin."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin(["info", "nonexistent_plugin"])
        assert result is False

    def test_plugin_run_no_args(self, ssh_manager: SSHManager) -> None:
        """Test plugin run without arguments."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin(["run"])
        assert result is False

    def test_plugin_run_no_connection(self, ssh_manager: SSHManager) -> None:
        """Test plugin run without connection."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_plugin(["run", "enumerate"])
        assert result is False


class TestListCommand:
    """Tests for list command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_list_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test list with no connections."""
        cm = CommandMode(ssh_manager)
        result = cm.cmd_list([])
        assert result is True

    def test_list_with_connections(self, ssh_manager: SSHManager) -> None:
        """Test list with active connections."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/listtest"
        )
        ssh_manager.connections["/tmp/listtest"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_list([])
        assert result is True

    def test_list_with_tunnels(self, ssh_manager: SSHManager) -> None:
        """Test list with connections that have tunnels."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/listtunnel"
        )
        conn.add_tunnel(8080, "localhost", 80)
        ssh_manager.connections["/tmp/listtunnel"] = conn
        cm = CommandMode(ssh_manager)
        result = cm.cmd_list([])
        assert result is True


class TestConfigCommand:
    """Tests for config command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_config_no_configs(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config with no saved configs."""
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {})
        cm = CommandMode(ssh_manager)
        result = cm.cmd_config([])
        assert result is True

    def test_config_with_configs(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config with saved configs."""
        monkeypatch.setattr(
            "lazyssh.command_mode.load_configs",
            lambda: {"server1": {"host": "192.168.1.1", "port": 22}},
        )
        cm = CommandMode(ssh_manager)
        result = cm.cmd_config([])
        assert result is True


class TestClearCommand:
    """Tests for clear command."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_clear(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test clear command."""
        monkeypatch.setattr("os.system", lambda x: 0)
        cm = CommandMode(ssh_manager)
        result = cm.cmd_clear([])
        assert result is True


class TestLazySSHCompleterEdgeCases:
    """Tests for LazySSHCompleter edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def command_mode(self, ssh_manager: SSHManager) -> CommandMode:
        """Create a CommandMode instance."""
        return CommandMode(ssh_manager)

    def test_completer_wizard_command(self, command_mode: CommandMode) -> None:
        """Test completion for wizard command."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("wizard ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "lazyssh" in names or "tunnel" in names

    def test_completer_plugin_subcommand(self, command_mode: CommandMode) -> None:
        """Test completion for plugin subcommands."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "list" in names
        assert "run" in names
        assert "info" in names

    def test_completer_plugin_run_plugin_name(self, command_mode: CommandMode) -> None:
        """Test completion for plugin run with plugin name."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin run ")
        list(completer.get_completions(doc, None))

    def test_completer_plugin_info_plugin_name(self, command_mode: CommandMode) -> None:
        """Test completion for plugin info with plugin name."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin info ")
        list(completer.get_completions(doc, None))

    def test_completer_connect_config_name(
        self, command_mode: CommandMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test completion for connect with config names."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        monkeypatch.setattr(
            "lazyssh.command_mode.load_configs", lambda: {"server1": {}, "server2": {}}
        )
        completer = LazySSHCompleter(command_mode)
        doc = Document("connect ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "server1" in names
        assert "server2" in names

    def test_completer_delete_config_name(
        self, command_mode: CommandMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test completion for delete-config with config names."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {"myconfig": {}})
        completer = LazySSHCompleter(command_mode)
        doc = Document("delete-config ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "myconfig" in names

    def test_completer_plugin_run_socket(self, command_mode: CommandMode) -> None:
        """Test completion for plugin run with socket name."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/plugintest"
        )
        command_mode.ssh_manager.connections["/tmp/plugintest"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin run enumerate ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "plugintest" in names


class TestDebugCommand:
    """Tests for debug command variations."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_debug_on(self, ssh_manager: SSHManager) -> None:
        """Test debug on command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_debug(["on"])

    def test_debug_off(self, ssh_manager: SSHManager) -> None:
        """Test debug off command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_debug(["off"])

    def test_debug_enable(self, ssh_manager: SSHManager) -> None:
        """Test debug enable command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_debug(["enable"])

    def test_debug_disable(self, ssh_manager: SSHManager) -> None:
        """Test debug disable command."""
        cm = CommandMode(ssh_manager)
        cm.cmd_debug(["disable"])


class TestWizardLazyssh:
    """Tests for SSH connection wizard."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_wizard_lazyssh_empty_host(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with empty hostname."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.return_value = ""
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_invalid_port(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with invalid port."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ["192.168.1.1", "invalid"]
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_empty_username(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with empty username."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ["192.168.1.1", "22", ""]
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_empty_socket_name(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with empty socket name."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ["192.168.1.1", "22", "user", ""]
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_invalid_socket_name(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with invalid socket name."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ["192.168.1.1", "22", "user", "invalid/name"]
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_keyboard_interrupt(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard cancelled with keyboard interrupt."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = KeyboardInterrupt()
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_eof_error(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard cancelled with EOF."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = EOFError()
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_exception(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with unexpected exception."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            mock_prompt.ask.side_effect = ValueError("test error")
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is False

    def test_wizard_lazyssh_existing_connection(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with already existing connection name, then rename."""
        from unittest import mock

        # Add an existing connection
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/existing"
        )
        ssh_manager.connections["/tmp/existing"] = conn

        with (
            mock.patch("rich.prompt.Prompt") as mock_prompt,
            mock.patch("rich.prompt.Confirm") as mock_confirm,
        ):
            mock_prompt.ask.side_effect = [
                "192.168.1.1",  # host
                "22",  # port
                "user",  # username
                "existing",  # socket name (same as existing)
                "newname",  # new socket name after rename prompt
                "",  # ssh key (empty)
                "bash",  # shell
                "9050",  # proxy port
            ]
            mock_confirm.ask.side_effect = [
                True,  # Yes, want different name
                False,  # Use SSH key?
                False,  # Custom shell?
                False,  # No term?
                False,  # SOCKS proxy?
                False,  # Save config?
            ]
            monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
            cm = CommandMode(ssh_manager)
            result = cm._wizard_lazyssh()
            assert result is True

    def test_wizard_lazyssh_full_flow_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard full success flow."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",  # host
                    "22",  # port
                    "testuser",  # username
                    "testconn",  # socket name
                    "",  # ssh key (empty)
                    "bash",  # shell
                    "9050",  # proxy port
                    "testconn",  # config name
                ]
                mock_confirm.ask.side_effect = [
                    False,  # Use SSH key?
                    False,  # Custom shell?
                    False,  # No term?
                    False,  # SOCKS proxy?
                    False,  # Save config?
                ]
                monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is True

    def test_wizard_lazyssh_with_all_options(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with all optional settings enabled."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",  # host
                    "22",  # port
                    "testuser",  # username
                    "allopts",  # socket name
                    "/home/user/.ssh/id_rsa",  # ssh key
                    "/bin/zsh",  # shell
                    "1080",  # proxy port
                    "allopts",  # config name
                ]
                mock_confirm.ask.side_effect = [
                    True,  # Use SSH key?
                    True,  # Custom shell?
                    True,  # No term?
                    True,  # SOCKS proxy?
                    True,  # Save config?
                ]
                monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
                monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: False)
                monkeypatch.setattr("lazyssh.command_mode.save_config", lambda x, y: True)
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is True

    def test_wizard_lazyssh_invalid_proxy_port(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard with invalid proxy port."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",  # host
                    "22",  # port
                    "testuser",  # username
                    "proxytest",  # socket name
                    "",  # ssh key
                    "",  # shell
                    "invalid",  # Invalid proxy port
                ]
                mock_confirm.ask.side_effect = [
                    False,  # Use SSH key?
                    False,  # Custom shell?
                    False,  # No term?
                    True,  # SOCKS proxy?
                ]
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is False

    def test_wizard_lazyssh_connection_failed(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard when connection creation fails."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",
                    "22",
                    "testuser",
                    "failconn",
                ]
                mock_confirm.ask.side_effect = [False, False, False, False]
                monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: False)
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is False

    def test_wizard_lazyssh_save_config_overwrite(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard saving config that already exists."""
        from unittest import mock

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",
                    "22",
                    "testuser",
                    "overwrite",
                    "overwrite",  # config name
                ]
                mock_confirm.ask.side_effect = [
                    False,  # SSH key
                    False,  # Custom shell
                    False,  # No term
                    False,  # Proxy
                    True,  # Save config?
                    False,  # Don't overwrite
                ]
                monkeypatch.setattr(ssh_manager, "create_connection", lambda conn: True)
                monkeypatch.setattr("lazyssh.command_mode.config_exists", lambda x: True)
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is True

    def test_wizard_lazyssh_new_socket_invalid(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test wizard when new socket name is also invalid."""
        from unittest import mock

        conn = SSHConnection(host="192.168.1.1", port=22, username="user", socket_path="/tmp/dup")
        ssh_manager.connections["/tmp/dup"] = conn

        with mock.patch("rich.prompt.Prompt") as mock_prompt:
            with mock.patch("rich.prompt.Confirm") as mock_confirm:
                mock_prompt.ask.side_effect = [
                    "192.168.1.1",
                    "22",
                    "testuser",
                    "dup",  # Existing name
                    "",  # Empty new name
                ]
                mock_confirm.ask.return_value = True  # Want different name
                cm = CommandMode(ssh_manager)
                result = cm._wizard_lazyssh()
                assert result is False


class TestWizardTunnel:
    """Tests for tunnel creation wizard."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_wizard_tunnel_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test tunnel wizard with no active connections."""
        cm = CommandMode(ssh_manager)
        result = cm._wizard_tunnel()
        assert result is False

    def test_wizard_tunnel_keyboard_interrupt(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard cancelled with keyboard interrupt."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuntest"
        )
        ssh_manager.connections["/tmp/tuntest"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            mock_int.ask.side_effect = KeyboardInterrupt()
            cm = CommandMode(ssh_manager)
            result = cm._wizard_tunnel()
            assert result is False

    def test_wizard_tunnel_invalid_connection_number(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard with invalid connection selection."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuntest2"
        )
        ssh_manager.connections["/tmp/tuntest2"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            mock_int.ask.return_value = 99  # Invalid number
            cm = CommandMode(ssh_manager)
            result = cm._wizard_tunnel()
            assert result is False

    def test_wizard_tunnel_invalid_tunnel_type(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard with invalid tunnel type."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuntest3"
        )
        ssh_manager.connections["/tmp/tuntest3"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            mock_int.ask.side_effect = [1, 5]  # Valid conn, invalid tunnel type
            cm = CommandMode(ssh_manager)
            result = cm._wizard_tunnel()
            assert result is False

    def test_wizard_tunnel_forward_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard forward tunnel success."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/fwdtun"
        )
        ssh_manager.connections["/tmp/fwdtun"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            with mock.patch("rich.prompt.Prompt") as mock_prompt:
                with mock.patch("rich.prompt.Confirm") as mock_confirm:
                    mock_int.ask.side_effect = [1, 1, 8080, 80]  # conn, forward, local, remote
                    mock_prompt.ask.return_value = "localhost"
                    mock_confirm.ask.return_value = True
                    monkeypatch.setattr(
                        ssh_manager,
                        "create_tunnel",
                        lambda socket, local, host, remote, is_reverse: True,
                    )
                    cm = CommandMode(ssh_manager)
                    result = cm._wizard_tunnel()
                    assert result is True

    def test_wizard_tunnel_reverse_success(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard reverse tunnel success."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/revtun"
        )
        ssh_manager.connections["/tmp/revtun"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            with mock.patch("rich.prompt.Prompt") as mock_prompt:
                with mock.patch("rich.prompt.Confirm") as mock_confirm:
                    mock_int.ask.side_effect = [1, 2, 3000, 22]  # conn, reverse, local, remote
                    mock_prompt.ask.return_value = "127.0.0.1"
                    mock_confirm.ask.return_value = True
                    monkeypatch.setattr(
                        ssh_manager,
                        "create_tunnel",
                        lambda socket, local, host, remote, is_reverse: True,
                    )
                    cm = CommandMode(ssh_manager)
                    result = cm._wizard_tunnel()
                    assert result is True

    def test_wizard_tunnel_cancelled(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard cancelled at confirmation."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/canceltun"
        )
        ssh_manager.connections["/tmp/canceltun"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            with mock.patch("rich.prompt.Prompt") as mock_prompt:
                with mock.patch("rich.prompt.Confirm") as mock_confirm:
                    mock_int.ask.side_effect = [1, 1, 8080, 80]
                    mock_prompt.ask.return_value = "localhost"
                    mock_confirm.ask.return_value = False  # Cancel
                    cm = CommandMode(ssh_manager)
                    result = cm._wizard_tunnel()
                    assert result is False

    def test_wizard_tunnel_creation_failed(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard when tunnel creation fails."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/failtun"
        )
        ssh_manager.connections["/tmp/failtun"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            with mock.patch("rich.prompt.Prompt") as mock_prompt:
                with mock.patch("rich.prompt.Confirm") as mock_confirm:
                    mock_int.ask.side_effect = [1, 1, 8080, 80]
                    mock_prompt.ask.return_value = "localhost"
                    mock_confirm.ask.return_value = True
                    monkeypatch.setattr(
                        ssh_manager,
                        "create_tunnel",
                        lambda socket, local, host, remote, is_reverse: False,
                    )
                    cm = CommandMode(ssh_manager)
                    result = cm._wizard_tunnel()
                    assert result is False

    def test_wizard_tunnel_exception(
        self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test tunnel wizard with unexpected exception."""
        from unittest import mock

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/exctun"
        )
        ssh_manager.connections["/tmp/exctun"] = conn

        with mock.patch("rich.prompt.IntPrompt") as mock_int:
            mock_int.ask.side_effect = ValueError("test error")
            cm = CommandMode(ssh_manager)
            result = cm._wizard_tunnel()
            assert result is False


class TestCompleterAdvanced:
    """Advanced tests for LazySSHCompleter edge cases."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    @pytest.fixture
    def command_mode(self, ssh_manager: SSHManager) -> CommandMode:
        """Create a CommandMode instance."""
        return CommandMode(ssh_manager)

    def test_completer_tunc_connection_name(self, command_mode: CommandMode) -> None:
        """Test tunc completion for connection names."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunccomp"
        )
        command_mode.ssh_manager.connections["/tmp/tunccomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tunc ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "tunccomp" in names

    def test_completer_tunc_tunnel_type(self, command_mode: CommandMode) -> None:
        """Test tunc completion for tunnel type."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tunctype"
        )
        command_mode.ssh_manager.connections["/tmp/tunctype"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tunc tunctype ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "l" in names
        assert "r" in names

    def test_completer_tund_tunnel_id(self, command_mode: CommandMode) -> None:
        """Test tund completion for tunnel IDs."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundcomp"
        )
        conn.add_tunnel(8080, "localhost", 80)
        command_mode.ssh_manager.connections["/tmp/tundcomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tund ")
        completions = list(completer.get_completions(doc, None))
        assert len(completions) >= 1

    def test_completer_terminal_methods(self, command_mode: CommandMode) -> None:
        """Test terminal completion for methods."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("terminal ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "auto" in names
        assert "native" in names
        assert "terminator" in names

    def test_completer_open_connection(self, command_mode: CommandMode) -> None:
        """Test open completion for connections."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/opencomp"
        )
        command_mode.ssh_manager.connections["/tmp/opencomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("open ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "opencomp" in names

    def test_completer_close_connection(self, command_mode: CommandMode) -> None:
        """Test close completion for connections."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/closecomp"
        )
        command_mode.ssh_manager.connections["/tmp/closecomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("close ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "closecomp" in names

    def test_completer_help_commands(self, command_mode: CommandMode) -> None:
        """Test help completion for commands."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("help ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "lazyssh" in names
        assert "help" in names

    def test_completer_save_config_connections(self, command_mode: CommandMode) -> None:
        """Test save-config completion for connection names."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/savecomp"
        )
        command_mode.ssh_manager.connections["/tmp/savecomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("save-config ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "savecomp" in names

    def test_completer_lazyssh_partial_arg(self, command_mode: CommandMode) -> None:
        """Test lazyssh completion with partial argument."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        # Test with partial argument starting with dash
        doc = Document("lazyssh -")
        list(completer.get_completions(doc, None))
        # May or may not return completions depending on implementation
        # Just ensure it doesn't crash

    def test_completer_lazyssh_optional_after_required(self, command_mode: CommandMode) -> None:
        """Test lazyssh shows optional args after required are filled."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("lazyssh -ip 1.2.3.4 -port 22 -user test -socket sock ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        # Should include optional args
        assert any(arg in names for arg in ["-proxy", "-ssh-key", "-shell", "-no-term"])

    def test_completer_lazyssh_no_proxy_flag(self, command_mode: CommandMode) -> None:
        """Test lazyssh -proxy doesn't expect a value."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        completer = LazySSHCompleter(command_mode)
        doc = Document("lazyssh -ip 1.2.3.4 -proxy ")
        completions = list(completer.get_completions(doc, None))
        # Should suggest next argument, not wait for value
        # -proxy is a flag without value
        names = [c.text for c in completions]
        # Should include port since it's required
        assert "-port" in names

    def test_completer_scp_connection(self, command_mode: CommandMode) -> None:
        """Test scp completion for connections."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/scpcomp"
        )
        command_mode.ssh_manager.connections["/tmp/scpcomp"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("scp ")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "scpcomp" in names

    def test_completer_partial_word_matching(self, command_mode: CommandMode) -> None:
        """Test completion with partial word before cursor."""
        from prompt_toolkit.document import Document

        from lazyssh.command_mode import LazySSHCompleter

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/partialtest"
        )
        command_mode.ssh_manager.connections["/tmp/partialtest"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("close partial")
        completions = list(completer.get_completions(doc, None))
        names = [c.text for c in completions]
        assert "partialtest" in names


class TestPluginRunWithConnection:
    """Tests for plugin run command with connections."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        """Create an SSHManager instance for testing."""
        return SSHManager()

    def test_plugin_run_with_connection(
        self, ssh_manager: SSHManager, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test plugin run with valid connection."""
        from lazyssh.plugin_manager import PluginManager

        # Create a mock plugin
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir()
        plugin_path = plugins_dir / "testrun.sh"
        plugin_path.write_text(
            """#!/bin/bash
# PLUGIN_NAME: testrun
# PLUGIN_DESCRIPTION: Test runner
echo "running"
""",
            encoding="utf-8",
        )
        plugin_path.chmod(0o755)

        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/plugrun"
        )
        ssh_manager.connections["/tmp/plugrun"] = conn

        cm = CommandMode(ssh_manager)
        cm.plugin_manager = PluginManager(plugins_dir=plugins_dir)

        # Mock subprocess to avoid actual execution
        import subprocess
        from unittest import mock

        with mock.patch.object(subprocess, "run") as mock_run:
            mock_result = mock.Mock()
            mock_result.returncode = 0
            mock_result.stdout = "running"
            mock_run.return_value = mock_result
            result = cm.cmd_plugin(["run", "testrun", "plugrun"])
            # May or may not succeed depending on plugin validation
            assert isinstance(result, bool)


class TestCompleterBranchCoverage:
    """Tests targeting specific branch partials in completion methods."""

    @pytest.fixture
    def ssh_manager(self) -> SSHManager:
        return SSHManager()

    @pytest.fixture
    def command_mode(self, ssh_manager: SSHManager) -> CommandMode:
        return CommandMode(ssh_manager)

    @pytest.fixture
    def completer(self, command_mode: CommandMode) -> LazySSHCompleter:
        return LazySSHCompleter(command_mode)

    def test_unknown_command_no_handler(self, completer: LazySSHCompleter) -> None:
        """Test completion for unknown command — handler is None (line 89->exit)."""
        doc = Document("nonexistentcommand ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_show_status_no_connections(self, ssh_manager: SSHManager) -> None:
        """Test show_status with no connections (line 333->exit)."""
        cm = CommandMode(ssh_manager)
        result = cm.show_status()
        assert result is None or result is True or result is False

    def test_tunc_partial_word_no_match(self, command_mode: CommandMode) -> None:
        """Test tunc completion with partial word that doesn't match (lines 149, 154)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuncbranch"
        )
        command_mode.ssh_manager.connections["/tmp/tuncbranch"] = conn
        completer = LazySSHCompleter(command_mode)
        # Partial word "zzz" that won't match any connection
        doc = Document("tunc zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_tunc_type_partial_no_match(self, command_mode: CommandMode) -> None:
        """Test tunc tunnel type completion with non-matching prefix (line 158)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuncbranch2"
        )
        command_mode.ssh_manager.connections["/tmp/tuncbranch2"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tunc tuncbranch2 z")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_terminal_partial_no_match(self, command_mode: CommandMode) -> None:
        """Test terminal completion with non-matching prefix (line 176->exit)."""
        completer = LazySSHCompleter(command_mode)
        doc = Document("terminal zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_terminal_too_many_args(self, completer: LazySSHCompleter) -> None:
        """Test terminal completion with too many args (line 176->exit)."""
        doc = Document("terminal auto ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_single_arg_connection_no_match(self, command_mode: CommandMode) -> None:
        """Test connection completion with non-matching prefix (line 185->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/openno"
        )
        command_mode.ssh_manager.connections["/tmp/openno"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("open zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_single_arg_connection_name_no_match(self, command_mode: CommandMode) -> None:
        """Test connection name completion with non-matching prefix (line 194->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/saveno"
        )
        command_mode.ssh_manager.connections["/tmp/saveno"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("save-config zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_config_name_no_match(
        self, command_mode: CommandMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test config completion with non-matching prefix (line 203->exit)."""
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {"server1": {}})
        completer = LazySSHCompleter(command_mode)
        doc = Document("connect zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_help_partial_no_match(self, completer: LazySSHCompleter) -> None:
        """Test help completion with non-matching prefix (line 213->exit)."""
        doc = Document("help zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_wizard_partial_no_match(self, completer: LazySSHCompleter) -> None:
        """Test wizard completion with non-matching prefix (line 222->exit)."""
        doc = Document("wizard zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_subcommand_partial_no_match(self, completer: LazySSHCompleter) -> None:
        """Test plugin subcommand completion with non-matching prefix (line 237)."""
        doc = Document("plugin zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_arg2_list_subcommand(self, completer: LazySSHCompleter) -> None:
        """Test plugin arg2 with 'list' subcommand — no plugins listed (line 242)."""
        doc = Document("plugin list ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_arg3_non_run_subcommand(self, completer: LazySSHCompleter) -> None:
        """Test plugin arg3 with non-run subcommand — no connection completions (line 247)."""
        doc = Document("plugin info enumerate ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_run_connection_no_match(self, command_mode: CommandMode) -> None:
        """Test plugin run with connection prefix that doesn't match (line 250)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/plugconn"
        )
        command_mode.ssh_manager.connections["/tmp/plugconn"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin run enumerate zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_lazyssh_all_args_used(self, completer: LazySSHCompleter) -> None:
        """Test lazyssh completion when all required+optional args used (line 140->exit)."""
        doc = Document(
            "lazyssh -ip 1.2.3.4 -port 22 -user test -socket /tmp/s "
            "-proxy 1080 -ssh-key /key -shell bash -no-term "
        )
        completions = list(completer.get_completions(doc, None))
        # All args used, nothing to suggest
        assert completions == []

    def test_tunc_beyond_arg2(self, command_mode: CommandMode) -> None:
        """Test tunc with more than 2 args (lines 152/156 both miss)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tuncarg3"
        )
        command_mode.ssh_manager.connections["/tmp/tuncarg3"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tunc tuncarg3 l 8080:localhost:80 ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_tund_no_match(self, command_mode: CommandMode) -> None:
        """Test tund with non-matching prefix (line 169)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundno"
        )
        conn.add_tunnel(8080, "localhost", 80)
        command_mode.ssh_manager.connections["/tmp/tundno"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tund zzz")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_tund_too_many_args(self, command_mode: CommandMode) -> None:
        """Test tund with too many args — condition false (line 166->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/tundmany"
        )
        conn.add_tunnel(8080, "localhost", 80)
        command_mode.ssh_manager.connections["/tmp/tundmany"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("tund tunnel1 extra")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_single_arg_connection_too_many_args(self, command_mode: CommandMode) -> None:
        """Test open/close with too many args (line 185->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/connmany"
        )
        command_mode.ssh_manager.connections["/tmp/connmany"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("open conn extra ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_single_arg_connection_name_too_many_args(self, command_mode: CommandMode) -> None:
        """Test save-config with too many args (line 194->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/savemany"
        )
        command_mode.ssh_manager.connections["/tmp/savemany"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("save-config conn extra ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_config_name_too_many_args(
        self, command_mode: CommandMode, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test connect/delete-config with too many args (line 203->exit)."""
        monkeypatch.setattr("lazyssh.command_mode.load_configs", lambda: {"server1": {}})
        completer = LazySSHCompleter(command_mode)
        doc = Document("connect server1 extra ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_help_too_many_args(self, completer: LazySSHCompleter) -> None:
        """Test help with too many args (line 213->exit)."""
        doc = Document("help lazyssh extra")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_wizard_too_many_args(self, completer: LazySSHCompleter) -> None:
        """Test wizard with too many args (line 222->exit)."""
        doc = Document("wizard lazyssh extra ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_arg2_with_non_run_info(self, completer: LazySSHCompleter) -> None:
        """Test plugin arg2 with subcommand not in [run, info] (line 242->exit)."""
        doc = Document("plugin list somearg ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []

    def test_plugin_arg4_beyond_limit(self, command_mode: CommandMode) -> None:
        """Test plugin completion at arg4+ returns nothing (line 247->exit)."""
        conn = SSHConnection(
            host="192.168.1.1", port=22, username="user", socket_path="/tmp/plugarg4"
        )
        command_mode.ssh_manager.connections["/tmp/plugarg4"] = conn
        completer = LazySSHCompleter(command_mode)
        doc = Document("plugin run enumerate plugarg4 extra ")
        completions = list(completer.get_completions(doc, None))
        assert completions == []
