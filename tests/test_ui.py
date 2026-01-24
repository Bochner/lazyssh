"""Tests for ui module - display functions, tables, panels, status rendering."""

from pathlib import Path
from unittest import mock

import pytest
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from lazyssh import ui
from lazyssh.models import SSHConnection


class TestDisplayBanner:
    """Tests for display_banner function."""

    def test_display_banner(self) -> None:
        """Test banner displays without error."""
        ui.display_banner()


class TestDisplayMenu:
    """Tests for display_menu function."""

    def test_display_menu(self) -> None:
        """Test menu displays correctly."""
        options = {"1": "Option 1", "2": "Option 2"}
        ui.display_menu(options)


class TestGetUserInput:
    """Tests for get_user_input function."""

    def test_get_user_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test user input prompting."""
        monkeypatch.setattr("rich.prompt.Prompt.ask", lambda x: "test input")
        result = ui.get_user_input("Enter something")
        assert result == "test input"


class TestDisplaySSHStatus:
    """Tests for display_ssh_status function."""

    def test_empty_connections(self) -> None:
        """Test display with no connections."""
        ui.display_ssh_status({})

    def test_with_connections(self) -> None:
        """Test display with active connections."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testsock",
        )
        connections = {"/tmp/testsock": conn}
        ui.display_ssh_status(connections)

    def test_with_terminal_method(self) -> None:
        """Test display with custom terminal method."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testsock2",
        )
        connections = {"/tmp/testsock2": conn}
        ui.display_ssh_status(connections, terminal_method="native")

    def test_with_dynamic_port(self) -> None:
        """Test display with dynamic port."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testsock3",
            dynamic_port=1080,
        )
        connections = {"/tmp/testsock3": conn}
        ui.display_ssh_status(connections)


class TestDisplayTunnels:
    """Tests for display_tunnels function."""

    def test_no_tunnels(self) -> None:
        """Test display with no tunnels."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testtunnel",
        )
        ui.display_tunnels("/tmp/testtunnel", conn)

    def test_with_tunnels(self) -> None:
        """Test display with active tunnels."""
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testtunnel2",
        )
        conn.add_tunnel(8080, "localhost", 80)
        conn.add_tunnel(9090, "localhost", 90, is_reverse=True)
        ui.display_tunnels("/tmp/testtunnel2", conn)


class TestDisplaySavedConfigs:
    """Tests for display_saved_configs function."""

    def test_no_configs(self) -> None:
        """Test display with no configs."""
        ui.display_saved_configs({})

    def test_with_configs(self) -> None:
        """Test display with saved configs."""
        configs = {
            "server1": {
                "host": "192.168.1.1",
                "username": "user",
                "port": 22,
            }
        }
        ui.display_saved_configs(configs)

    def test_with_all_fields(self) -> None:
        """Test display with all config fields."""
        configs = {
            "server2": {
                "host": "192.168.1.1",
                "username": "admin",
                "port": 2222,
                "ssh_key": "~/.ssh/id_rsa",
                "shell": "/bin/zsh",
                "proxy_port": 1080,
                "no_term": True,
            }
        }
        ui.display_saved_configs(configs)

    def test_with_long_ssh_key(self) -> None:
        """Test display truncates long SSH key path."""
        configs = {
            "server3": {
                "host": "192.168.1.1",
                "username": "user",
                "ssh_key": "/home/user/.ssh/very_long_path_to_key_file",
            }
        }
        ui.display_saved_configs(configs)


class TestCreateStandardTable:
    """Tests for create_standard_table function."""

    def test_default_table(self) -> None:
        """Test creating default table."""
        table = ui.create_standard_table()
        assert isinstance(table, Table)

    def test_table_with_title(self) -> None:
        """Test creating table with title."""
        table = ui.create_standard_table(title="Test Table")
        assert table.title == "Test Table"

    def test_table_without_header(self) -> None:
        """Test creating table without header."""
        table = ui.create_standard_table(show_header=False)
        assert table.show_header is False


class TestPanelFunctions:
    """Tests for panel creation functions."""

    def test_create_info_panel(self) -> None:
        """Test creating info panel."""
        panel = ui.create_info_panel("Test content")
        assert isinstance(panel, Panel)

    def test_create_info_panel_with_title(self) -> None:
        """Test creating info panel with title."""
        panel = ui.create_info_panel("Test content", "Custom Title")
        assert isinstance(panel, Panel)

    def test_create_success_panel(self) -> None:
        """Test creating success panel."""
        panel = ui.create_success_panel("Test content")
        assert isinstance(panel, Panel)

    def test_create_error_panel(self) -> None:
        """Test creating error panel."""
        panel = ui.create_error_panel("Test content")
        assert isinstance(panel, Panel)

    def test_create_warning_panel(self) -> None:
        """Test creating warning panel."""
        panel = ui.create_warning_panel("Test content")
        assert isinstance(panel, Panel)


class TestUIConfigFunctions:
    """Tests for UI config functions."""

    def test_get_current_ui_config(self) -> None:
        """Test getting current UI config."""
        config = ui.get_current_ui_config()
        assert isinstance(config, dict)

    def test_update_console_config(self) -> None:
        """Test updating console config."""
        ui.update_console_config()

    def test_get_console(self) -> None:
        """Test getting console instance."""
        console = ui.get_console()
        assert console is not None


class TestStatusFunctions:
    """Tests for status display functions."""

    def test_create_spinner(self) -> None:
        """Test creating spinner text."""
        result = ui.create_spinner()
        assert "Processing" in result

    def test_create_spinner_custom_text(self) -> None:
        """Test creating spinner with custom text."""
        result = ui.create_spinner("Loading...")
        assert "Loading" in result

    def test_create_status_indicator_success(self) -> None:
        """Test creating success status indicator."""
        result = ui.create_status_indicator("success", "Operation completed")
        assert "SUCCESS" in result

    def test_create_status_indicator_error(self) -> None:
        """Test creating error status indicator."""
        result = ui.create_status_indicator("error", "Operation failed")
        assert "ERROR" in result

    def test_create_status_indicator_warning(self) -> None:
        """Test creating warning status indicator."""
        result = ui.create_status_indicator("warning", "Check this")
        assert "WARNING" in result

    def test_create_status_indicator_info(self) -> None:
        """Test creating info status indicator."""
        result = ui.create_status_indicator("info", "Note")
        assert "INFO" in result

    def test_create_status_indicator_processing(self) -> None:
        """Test creating processing status indicator."""
        result = ui.create_status_indicator("processing", "Working")
        assert "PROCESSING" in result

    def test_create_status_indicator_unknown(self) -> None:
        """Test creating unknown status indicator defaults to info."""
        result = ui.create_status_indicator("unknown", "Something")
        assert "UNKNOWN" in result


class TestLayoutFunctions:
    """Tests for layout creation functions."""

    def test_create_main_layout(self) -> None:
        """Test creating main layout."""
        layout = ui.create_main_layout()
        assert isinstance(layout, Layout)

    def test_create_sidebar_layout(self) -> None:
        """Test creating sidebar layout."""
        layout = ui.create_sidebar_layout()
        assert isinstance(layout, Layout)

    def test_create_dashboard_layout(self) -> None:
        """Test creating dashboard layout."""
        layout = ui.create_dashboard_layout()
        assert isinstance(layout, Layout)

    def test_create_progress_layout(self) -> None:
        """Test creating progress layout."""
        layout = ui.create_progress_layout()
        assert isinstance(layout, Layout)

    def test_update_layout_header(self) -> None:
        """Test updating layout header."""
        layout = ui.create_main_layout()
        ui.update_layout_header(layout, "Test Header")

    def test_update_layout_footer(self) -> None:
        """Test updating layout footer."""
        layout = ui.create_main_layout()
        ui.update_layout_footer(layout, "Test Footer")

    def test_render_layout(self) -> None:
        """Test rendering layout."""
        layout = ui.create_main_layout()
        ui.render_layout(layout)


class TestMarkdownFunctions:
    """Tests for markdown rendering functions."""

    def test_render_markdown(self) -> None:
        """Test rendering markdown."""
        ui.render_markdown("# Test\n\nSome content")

    def test_render_markdown_with_title(self) -> None:
        """Test rendering markdown with title."""
        ui.render_markdown("# Test\n\nSome content", title="Test Title")

    def test_render_help_markdown(self) -> None:
        """Test rendering help markdown."""
        ui.render_help_markdown("# Help\n\nHelp content")

    def test_render_documentation_markdown(self) -> None:
        """Test rendering documentation markdown."""
        ui.render_documentation_markdown("# Docs\n\nDocumentation")

    def test_render_documentation_markdown_with_section(self) -> None:
        """Test rendering documentation markdown with section."""
        ui.render_documentation_markdown("# Docs\n\nDocumentation", section="Overview")

    def test_create_markdown_panel(self) -> None:
        """Test creating markdown panel."""
        panel = ui.create_markdown_panel("# Test", title="Test")
        assert isinstance(panel, Panel)

    def test_create_markdown_panel_types(self) -> None:
        """Test creating markdown panel with different types."""
        for panel_type in ["info", "success", "error", "warning", "accent", "unknown"]:
            panel = ui.create_markdown_panel("# Test", panel_type=panel_type)
            assert isinstance(panel, Panel)


class TestLiveDisplayFunctions:
    """Tests for live display functions."""

    def test_create_live_progress(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating live progress."""
        monkeypatch.delenv("LAZYSSH_NO_ANIMATIONS", raising=False)
        live, progress = ui.create_live_progress("Testing...")
        assert isinstance(live, Live)
        assert isinstance(progress, Progress)

    def test_create_live_progress_no_animations(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating live progress without animations."""
        monkeypatch.setenv("LAZYSSH_NO_ANIMATIONS", "true")
        live, progress = ui.create_live_progress("Testing...")
        assert isinstance(live, Live)
        assert isinstance(progress, Progress)

    def test_create_live_status_display(self) -> None:
        """Test creating live status display."""
        live = ui.create_live_status_display()
        assert isinstance(live, Live)

    def test_update_live_status(self) -> None:
        """Test updating live status with main layout."""
        # Use create_main_layout which has 'main' section
        layout = ui.create_main_layout()
        live = Live(layout, console=ui.console)
        ui.update_live_status(live, "Status text", "Details")

    def test_update_live_status_no_renderable(self) -> None:
        """Test updating live status when renderable has no update."""
        live = mock.Mock()
        live.renderable = "not a layout"
        ui.update_live_status(live, "Status text")

    def test_create_live_table(self) -> None:
        """Test creating live table."""
        live, table = ui.create_live_table("Test Table")
        assert isinstance(live, Live)
        assert isinstance(table, Table)

    def test_create_live_connection_monitor(self) -> None:
        """Test creating live connection monitor."""
        live = ui.create_live_connection_monitor()
        assert isinstance(live, Live)

    def test_update_live_connections(self) -> None:
        """Test updating live connections."""
        live = ui.create_live_connection_monitor()
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="user",
            socket_path="/tmp/testlive",
        )
        ui.update_live_connections(live, {"/tmp/testlive": conn})

    def test_update_live_connections_no_renderable(self) -> None:
        """Test updating live connections when renderable not present."""
        live = mock.Mock(spec=[])  # No renderable attribute
        ui.update_live_connections(live, {})


class TestAccessibilityFunctions:
    """Tests for accessibility functions."""

    def test_create_readable_table(self) -> None:
        """Test creating readable table."""
        table = ui.create_readable_table()
        assert isinstance(table, Table)
        assert table.show_lines is True

    def test_create_accessible_panel(self) -> None:
        """Test creating accessible panel."""
        panel = ui.create_accessible_panel("Test content")
        assert isinstance(panel, Panel)

    def test_create_accessible_panel_types(self) -> None:
        """Test creating accessible panel with different types."""
        for panel_type in ["info", "success", "error", "warning", "accent", "unknown"]:
            panel = ui.create_accessible_panel("Test", panel_type=panel_type)
            assert isinstance(panel, Panel)

    def test_create_status_with_indicators(self) -> None:
        """Test creating status with indicators."""
        for status in ["success", "error", "warning", "info", "processing", "unknown"]:
            result = ui.create_status_with_indicators(status, "Message")
            assert status.upper() in result

    def test_ensure_terminal_compatibility(self) -> None:
        """Test terminal compatibility check."""
        result = ui.ensure_terminal_compatibility()
        assert isinstance(result, bool)

    def test_ensure_terminal_compatibility_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test terminal compatibility check when Console fails."""
        from rich.console import Console

        def mock_init(self, *args, **kwargs):
            raise Exception("Console failed")

        monkeypatch.setattr(Console, "__init__", mock_init)
        result = ui.ensure_terminal_compatibility()
        assert result is False

    def test_create_fallback_display(self, capsys) -> None:
        """Test fallback display."""
        ui.create_fallback_display("[info]Test[/info] message")
        captured = capsys.readouterr()
        assert "Test" in captured.out
        assert "message" in captured.out


class TestPerformanceFunctions:
    """Tests for performance functions."""

    def test_benchmark_rich_rendering(self) -> None:
        """Test benchmark rendering."""
        results = ui.benchmark_rich_rendering()
        assert isinstance(results, dict)
        assert "table_100_rows" in results
        assert "panel" in results
        assert "markdown" in results

    def test_optimize_console_performance(self) -> None:
        """Test optimized console creation."""
        console = ui.optimize_console_performance()
        assert console is not None

    def test_create_cached_table_template(self) -> None:
        """Test cached table template."""
        table = ui.create_cached_table_template("Test")
        assert isinstance(table, Table)

    def test_measure_render_time_decorator(self) -> None:
        """Test render time decorator."""

        @ui.measure_render_time
        def fast_func() -> str:
            return "fast"

        result = fast_func()
        assert result == "fast"

    def test_measure_render_time_slow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test render time decorator with slow function."""
        import time

        @ui.measure_render_time
        def slow_func() -> str:
            time.sleep(0.15)  # Sleep for 150ms to exceed threshold
            return "slow"

        result = slow_func()
        assert result == "slow"

    def test_create_efficient_progress_bar(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test efficient progress bar creation."""
        monkeypatch.delenv("LAZYSSH_NO_ANIMATIONS", raising=False)
        progress = ui.create_efficient_progress_bar()
        assert isinstance(progress, Progress)

    def test_create_efficient_progress_bar_no_animations(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test efficient progress bar without animations."""
        monkeypatch.setenv("LAZYSSH_NO_ANIMATIONS", "true")
        progress = ui.create_efficient_progress_bar()
        assert isinstance(progress, Progress)

    def test_batch_render_updates(self) -> None:
        """Test batch render updates."""
        updates = [
            ("info", "Info message"),
            ("success", "Success message"),
            ("error", "Error message"),
            ("warning", "Warning message"),
            ("unknown", "Unknown message"),
        ]
        ui.batch_render_updates(updates)

    def test_profile_ui_performance(self) -> None:
        """Test UI performance profiling."""
        ui.profile_ui_performance()

    def test_profile_ui_performance_slow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test UI performance profiling with slow components."""

        # Mock benchmark_rich_rendering to return slow times
        def mock_benchmark() -> dict[str, float]:
            return {
                "table_100_rows": 0.5,  # Slow
                "panel": 0.02,
                "markdown": 0.03,
            }

        monkeypatch.setattr(ui, "benchmark_rich_rendering", mock_benchmark)
        ui.profile_ui_performance()


class TestPluginDisplayFunctions:
    """Tests for plugin display functions."""

    def test_display_plugins_empty(self) -> None:
        """Test displaying empty plugin list."""
        ui.display_plugins({})

    def test_display_plugins(self) -> None:
        """Test displaying plugins."""

        class MockPlugin:
            def __init__(self, name: str, valid: bool = True):
                self.name = name
                self.plugin_type = "python"
                self.description = "Test plugin description"
                self.is_valid = valid
                self.validation_errors = [] if valid else ["Error"]

        plugins = {
            "plugin1": MockPlugin("plugin1"),
            "plugin2": MockPlugin("plugin2", valid=False),
        }
        ui.display_plugins(plugins)

    def test_display_plugins_shell(self) -> None:
        """Test displaying shell plugins."""

        class MockPlugin:
            def __init__(self):
                self.name = "shellplugin"
                self.plugin_type = "shell"
                self.description = "A shell plugin"
                self.is_valid = True
                self.validation_errors = []

        plugins = {"shellplugin": MockPlugin()}
        ui.display_plugins(plugins)

    def test_display_plugins_long_description(self) -> None:
        """Test displaying plugins with long description."""

        class MockPlugin:
            def __init__(self):
                self.name = "longdesc"
                self.plugin_type = "python"
                self.description = "A" * 100  # Long description
                self.is_valid = True
                self.validation_errors = []

        plugins = {"longdesc": MockPlugin()}
        ui.display_plugins(plugins)

    def test_display_plugin_info(self) -> None:
        """Test displaying plugin info."""

        class MockPlugin:
            def __init__(self):
                self.name = "testplugin"
                self.plugin_type = "python"
                self.version = "1.0.0"
                self.description = "Test plugin"
                self.requirements = "python3"
                self.file_path = Path("/tmp/test.py")
                self.is_valid = True
                self.validation_errors = []
                self.validation_warnings = []

        ui.display_plugin_info(MockPlugin())

    def test_display_plugin_info_with_warnings(self) -> None:
        """Test displaying plugin info with warnings."""

        class MockPlugin:
            def __init__(self):
                self.name = "warnplugin"
                self.plugin_type = "python"
                self.version = "1.0.0"
                self.description = "Test plugin"
                self.requirements = "python3"
                self.file_path = Path("/tmp/test.py")
                self.is_valid = True
                self.validation_errors = []
                self.validation_warnings = ["Missing shebang"]

        ui.display_plugin_info(MockPlugin())

    def test_display_plugin_info_invalid(self) -> None:
        """Test displaying invalid plugin info."""

        class MockPlugin:
            def __init__(self):
                self.name = "invalidplugin"
                self.plugin_type = "shell"
                self.version = "1.0.0"
                self.description = "Test plugin"
                self.requirements = "bash"
                self.file_path = Path("/tmp/test.sh")
                self.is_valid = False
                self.validation_errors = ["Not executable"]
                self.validation_warnings = []

        ui.display_plugin_info(MockPlugin())

    def test_display_plugin_output(self) -> None:
        """Test displaying plugin output."""
        ui.display_plugin_output("Output text", 1.5, success=True)

    def test_display_plugin_output_failed(self) -> None:
        """Test displaying failed plugin output."""
        ui.display_plugin_output("Error output", 0.5, success=False)

    def test_display_plugin_output_empty(self) -> None:
        """Test displaying empty plugin output."""
        ui.display_plugin_output("", 0.1, success=True)

    def test_display_plugin_output_with_ansi(self) -> None:
        """Test displaying plugin output with ANSI codes."""
        output = "\x1b[32mGreen text\x1b[0m\r\nNew line"
        ui.display_plugin_output(output, 0.5, success=True)
