"""Tests for console_instance module - console creation, themes, accessibility."""

import os
from unittest import mock

import pytest

from lazyssh import console_instance


class TestParseBooleanEnvVar:
    """Tests for parse_boolean_env_var function."""

    def test_default_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default value when variable is not set."""
        monkeypatch.delenv("TEST_VAR", raising=False)
        assert console_instance.parse_boolean_env_var("TEST_VAR", False) is False
        assert console_instance.parse_boolean_env_var("TEST_VAR", True) is True

    def test_true_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test recognized true values."""
        for value in ("true", "1", "yes", "on", "TRUE", "Yes", "ON"):
            monkeypatch.setenv("TEST_VAR", value)
            assert console_instance.parse_boolean_env_var("TEST_VAR") is True

    def test_false_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test values that result in false."""
        for value in ("false", "0", "no", "off", "anything", ""):
            monkeypatch.setenv("TEST_VAR", value)
            assert console_instance.parse_boolean_env_var("TEST_VAR") is False


class TestParseIntegerEnvVar:
    """Tests for parse_integer_env_var function."""

    def test_default_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default value when variable is not set."""
        monkeypatch.delenv("TEST_INT", raising=False)
        assert console_instance.parse_integer_env_var("TEST_INT", 5) == 5

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("7", 7),
            ("0", 1),
            ("100", 10),
            ("not-a-number", 5),
            ("", 5),
        ],
        ids=[
            "valid-in-range",
            "below-min-clamped",
            "above-max-clamped",
            "invalid-default",
            "empty-default",
        ],
    )
    def test_parse_with_bounds(
        self, monkeypatch: pytest.MonkeyPatch, env_value: str, expected: int
    ) -> None:
        """Test integer parsing with min/max bounds and invalid inputs."""
        monkeypatch.setenv("TEST_INT", env_value)
        assert console_instance.parse_integer_env_var("TEST_INT", 5, 1, 10) == expected


class TestGetUIConfig:
    """Tests for get_ui_config function."""

    def test_default_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default configuration."""
        # Clear all UI env vars
        for var in [
            "LAZYSSH_HIGH_CONTRAST",
            "LAZYSSH_NO_RICH",
            "LAZYSSH_REFRESH_RATE",
            "LAZYSSH_NO_ANIMATIONS",
            "LAZYSSH_COLORBLIND_MODE",
            "LAZYSSH_PLAIN_TEXT",
        ]:
            monkeypatch.delenv(var, raising=False)

        config = console_instance.get_ui_config()

        assert config["high_contrast"] is False
        assert config["no_rich"] is False
        assert config["refresh_rate"] == 4
        assert config["no_animations"] is False
        assert config["colorblind_mode"] is False
        assert config["plain_text"] is False

    def test_all_enabled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test all features enabled."""
        monkeypatch.setenv("LAZYSSH_HIGH_CONTRAST", "true")
        monkeypatch.setenv("LAZYSSH_NO_RICH", "true")
        monkeypatch.setenv("LAZYSSH_REFRESH_RATE", "8")
        monkeypatch.setenv("LAZYSSH_NO_ANIMATIONS", "true")
        monkeypatch.setenv("LAZYSSH_COLORBLIND_MODE", "true")
        monkeypatch.setenv("LAZYSSH_PLAIN_TEXT", "true")

        config = console_instance.get_ui_config()

        assert config["high_contrast"] is True
        assert config["no_rich"] is True
        assert config["refresh_rate"] == 8
        assert config["no_animations"] is True
        assert config["colorblind_mode"] is True
        assert config["plain_text"] is True


class TestGetTerminalWidth:
    """Tests for get_terminal_width function.

    NOTE: Tests that mock shutil.get_terminal_size use mock.patch context managers
    instead of monkeypatch.setattr to scope the mock tightly. monkeypatch teardown
    runs AFTER pytest-sugar's pytest_runtest_logreport hook, so a monkeypatched
    shutil.get_terminal_size that raises OSError would crash pytest-sugar.
    """

    def test_from_columns_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting width from COLUMNS env var."""
        monkeypatch.setenv("COLUMNS", "120")
        assert console_instance.get_terminal_width() == 120

    def test_invalid_columns_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback when COLUMNS is invalid."""
        monkeypatch.setenv("COLUMNS", "invalid")

        with mock.patch(
            "shutil.get_terminal_size",
            return_value=os.terminal_size((100, 40)),
        ):
            assert console_instance.get_terminal_width() == 100

    def test_from_terminal_size(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting width from terminal size."""
        monkeypatch.delenv("COLUMNS", raising=False)
        with mock.patch(
            "shutil.get_terminal_size",
            return_value=os.terminal_size((90, 30)),
        ):
            assert console_instance.get_terminal_width() == 90

    def test_terminal_size_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback when terminal size is zero."""
        monkeypatch.delenv("COLUMNS", raising=False)
        with (
            mock.patch(
                "shutil.get_terminal_size",
                return_value=os.terminal_size((0, 0)),
            ),
            mock.patch("shutil.which", return_value=None),
        ):
            assert console_instance.get_terminal_width() == 80

    def test_terminal_size_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback when terminal size raises exception."""
        monkeypatch.delenv("COLUMNS", raising=False)

        with (
            mock.patch("shutil.get_terminal_size", side_effect=OSError("No terminal")),
            mock.patch("shutil.which", return_value=None),
        ):
            assert console_instance.get_terminal_width() == 80

    def test_from_tput(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test getting width from tput command."""
        monkeypatch.delenv("COLUMNS", raising=False)
        with (
            mock.patch(
                "shutil.get_terminal_size",
                return_value=os.terminal_size((0, 0)),
            ),
            mock.patch("shutil.which", return_value="/usr/bin/tput"),
            mock.patch("subprocess.check_output", return_value="132\n"),
        ):
            assert console_instance.get_terminal_width() == 132

    def test_tput_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback when tput fails."""
        import subprocess

        monkeypatch.delenv("COLUMNS", raising=False)
        with (
            mock.patch(
                "shutil.get_terminal_size",
                return_value=os.terminal_size((0, 0)),
            ),
            mock.patch("shutil.which", return_value="/usr/bin/tput"),
            mock.patch(
                "subprocess.check_output",
                side_effect=subprocess.CalledProcessError(1, "tput"),
            ),
        ):
            assert console_instance.get_terminal_width() == 80

    def test_tput_invalid_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fallback when tput returns invalid output."""
        monkeypatch.delenv("COLUMNS", raising=False)
        with (
            mock.patch(
                "shutil.get_terminal_size",
                return_value=os.terminal_size((0, 0)),
            ),
            mock.patch("shutil.which", return_value="/usr/bin/tput"),
            mock.patch("subprocess.check_output", return_value="invalid\n"),
        ):
            assert console_instance.get_terminal_width() == 80


class TestThemes:
    """Tests for theme creation functions."""

    def test_high_contrast_theme(self) -> None:
        """Test high contrast theme creation."""
        theme = console_instance.create_high_contrast_theme()
        assert theme is not None
        # Check some key colors
        assert theme.styles.get("error") is not None
        assert theme.styles.get("success") is not None

    def test_colorblind_friendly_theme(self) -> None:
        """Test colorblind friendly theme creation."""
        theme = console_instance.create_colorblind_friendly_theme()
        assert theme is not None
        assert theme.styles.get("error") is not None
        assert theme.styles.get("success") is not None

    def test_default_theme(self) -> None:
        """Test default theme exists."""
        assert console_instance.LAZYSSH_THEME is not None


class TestGetThemeForConfig:
    """Tests for get_theme_for_config function."""

    def test_plain_text_theme(self) -> None:
        """Test plain text theme."""
        config = {"plain_text": True, "high_contrast": False, "colorblind_mode": False}
        theme = console_instance.get_theme_for_config(config)
        assert theme is not None

    def test_high_contrast_theme(self) -> None:
        """Test high contrast theme selection."""
        config = {"plain_text": False, "high_contrast": True, "colorblind_mode": False}
        theme = console_instance.get_theme_for_config(config)
        # Should return high contrast theme
        assert theme is not None

    def test_colorblind_mode_theme(self) -> None:
        """Test colorblind mode theme selection."""
        config = {"plain_text": False, "high_contrast": False, "colorblind_mode": True}
        theme = console_instance.get_theme_for_config(config)
        assert theme is not None

    def test_default_theme(self) -> None:
        """Test default theme selection."""
        config = {"plain_text": False, "high_contrast": False, "colorblind_mode": False}
        theme = console_instance.get_theme_for_config(config)
        assert theme is console_instance.LAZYSSH_THEME


class TestCreateConsoleWithConfig:
    """Tests for create_console_with_config function."""

    def test_normal_mode(self) -> None:
        """Test console creation in normal mode."""
        config = {
            "plain_text": False,
            "high_contrast": False,
            "colorblind_mode": False,
            "no_rich": False,
        }
        console = console_instance.create_console_with_config(config)
        assert console is not None

    def test_no_rich_mode(self) -> None:
        """Test console creation with no_rich."""
        config = {
            "plain_text": False,
            "high_contrast": False,
            "colorblind_mode": False,
            "no_rich": True,
        }
        console = console_instance.create_console_with_config(config)
        assert console is not None

    def test_plain_text_mode(self) -> None:
        """Test console creation in plain text mode."""
        config = {
            "plain_text": True,
            "high_contrast": False,
            "colorblind_mode": False,
            "no_rich": False,
        }
        console = console_instance.create_console_with_config(config)
        assert console is not None
        assert console.color_system is None


class TestDisplayFunctions:
    """Tests for display helper functions."""

    def test_display_error(self, capsys) -> None:
        """Test display_error function."""
        # Just verify it doesn't raise
        console_instance.display_error("Test error")
        # Output goes to console, not stdout

    def test_display_success(self) -> None:
        """Test display_success function."""
        console_instance.display_success("Test success")

    def test_display_info(self) -> None:
        """Test display_info function."""
        console_instance.display_info("Test info")

    def test_display_warning(self) -> None:
        """Test display_warning function."""
        console_instance.display_warning("Test warning")


class TestDisplayAccessibleMessage:
    """Tests for display_accessible_message function."""

    @pytest.mark.parametrize(
        "msg_type",
        ["error", "success", "warning", "info", "unknown"],
        ids=["error", "success", "warning", "info", "unknown-defaults-to-info"],
    )
    def test_message_types(self, msg_type: str) -> None:
        """Test that each message type (including unknown) does not raise."""
        console_instance.display_accessible_message("Test", msg_type)


class TestDisplayMessageWithFallback:
    """Tests for display_message_with_fallback function."""

    @pytest.mark.parametrize(
        ("msg_type", "expected_prefix"),
        [("info", "INFO:"), ("success", "SUCCESS:"), ("error", "ERROR:"), ("warning", "WARNING:")],
    )
    def test_plain_text_types(
        self, monkeypatch: pytest.MonkeyPatch, capsys, msg_type: str, expected_prefix: str
    ) -> None:
        """Test plain text output for each message type."""
        monkeypatch.setenv("LAZYSSH_PLAIN_TEXT", "true")

        console_instance.display_message_with_fallback("Test message", msg_type)

        captured = capsys.readouterr()
        assert expected_prefix in captured.out
        assert "Test message" in captured.out

    def test_no_rich_mode(self, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
        """Test no_rich mode output."""
        monkeypatch.setenv("LAZYSSH_NO_RICH", "true")
        monkeypatch.delenv("LAZYSSH_PLAIN_TEXT", raising=False)

        console_instance.display_message_with_fallback("Test message", "info")

        captured = capsys.readouterr()
        assert "INFO:" in captured.out

    @pytest.mark.parametrize("msg_type", ["info", "success", "error", "warning"])
    def test_rich_mode_types(self, monkeypatch: pytest.MonkeyPatch, msg_type: str) -> None:
        """Test rich mode output does not raise for each message type."""
        monkeypatch.delenv("LAZYSSH_PLAIN_TEXT", raising=False)
        monkeypatch.delenv("LAZYSSH_NO_RICH", raising=False)

        console_instance.display_message_with_fallback("Test message", msg_type)

    def test_rich_mode_unknown(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test rich mode unknown type defaults to info."""
        monkeypatch.delenv("LAZYSSH_PLAIN_TEXT", raising=False)
        monkeypatch.delenv("LAZYSSH_NO_RICH", raising=False)

        console_instance.display_message_with_fallback("Test message", "unknown")


class TestIsRealTerminal:
    """Tests for _is_real_terminal function."""

    def test_returns_false_when_isatty_raises_attribute_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns False when isatty raises AttributeError."""

        class BadStdout:
            def isatty(self):
                raise AttributeError("No isatty")

        monkeypatch.setattr("sys.stdout", BadStdout())

        assert console_instance._is_real_terminal() is False

    def test_returns_false_when_isatty_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns False when isatty raises ValueError."""

        class BadStdout:
            def isatty(self):
                raise ValueError("Bad value")

        monkeypatch.setattr("sys.stdout", BadStdout())

        assert console_instance._is_real_terminal() is False


class TestSafeConsolePrint:
    """Tests for _safe_console_print function."""

    def test_handles_oserror_on_console_print(
        self, monkeypatch: pytest.MonkeyPatch, capsys
    ) -> None:
        """Test fallback to plain print when console.print raises OSError."""
        from unittest import mock

        # Mock console.print to raise OSError
        with mock.patch.object(
            console_instance.console, "print", side_effect=OSError("Broken pipe")
        ):
            console_instance._safe_console_print("[info]Test message[/info]")

        captured = capsys.readouterr()
        # Should fall back to plain print, stripping markup
        assert "Test message" in captured.out

    def test_handles_oserror_on_fallback_print(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test silently ignores when both console.print and print raise OSError."""
        from unittest import mock

        # Mock console.print to raise OSError
        with mock.patch.object(
            console_instance.console, "print", side_effect=OSError("Broken pipe")
        ):
            # Mock builtin print to also raise OSError
            with mock.patch("builtins.print", side_effect=OSError("Broken pipe")):
                # Should not raise
                console_instance._safe_console_print("[info]Test message[/info]")
