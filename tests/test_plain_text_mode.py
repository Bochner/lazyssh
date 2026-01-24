#!/usr/bin/env python3
"""
Tests for plain text mode functionality.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

from rich.style import Style

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestPlainTextMode(unittest.TestCase):
    """Test plain text mode functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing environment variables
        if "LAZYSSH_PLAIN_TEXT" in os.environ:
            del os.environ["LAZYSSH_PLAIN_TEXT"]

    def test_plain_text_default_false(self) -> None:
        """Test that plain_text defaults to False."""
        from lazyssh.ui import get_ui_config

        config = get_ui_config()
        self.assertFalse(config["plain_text"])

    def test_plain_text_true_values(self) -> None:
        """Test that plain_text is True for various true values."""
        from lazyssh.ui import get_ui_config

        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        for value in true_values:
            with self.subTest(value=value):
                os.environ["LAZYSSH_PLAIN_TEXT"] = value
                config = get_ui_config()
                self.assertTrue(config["plain_text"], f"Value '{value}' should be parsed as True")

    def test_plain_text_false_values(self) -> None:
        """Test that plain_text is False for various false values."""
        from lazyssh.ui import get_ui_config

        false_values = ["false", "FALSE", "0", "no", "NO", "off", "OFF", "", "invalid"]
        for value in false_values:
            with self.subTest(value=value):
                os.environ["LAZYSSH_PLAIN_TEXT"] = value
                config = get_ui_config()
                self.assertFalse(config["plain_text"], f"Value '{value}' should be parsed as False")

    def test_plain_text_theme_creation(self) -> None:
        """Test plain text theme creation."""
        from lazyssh.console_instance import get_theme_for_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": True,
        }

        theme = get_theme_for_config(config)

        # Check that our explicitly set theme values are "default"
        expected_keys = {
            "info",
            "warning",
            "error",
            "success",
            "header",
            "accent",
            "dim",
            "highlight",
            "border",
            "table.header",
            "table.row",
            "panel.title",
            "panel.subtitle",
            "keyword",
            "operator",
            "string",
            "variable",
            "number",
            "comment",
            "foreground",
            "background",
            "progress.description",
            "progress.percentage",
            "progress.bar",
            "progress.bar.complete",
        }
        for key in expected_keys:
            if key in theme.styles:
                value = theme.styles[key]
                self.assertEqual(
                    value,
                    Style.parse("default"),
                    f"Style '{key}' should be default Style in plain text mode",
                )

    def test_plain_text_theme_precedence(self) -> None:
        """Test that plain text theme takes precedence over other themes."""
        from lazyssh.console_instance import get_theme_for_config

        # Set multiple theme options
        config = {
            "high_contrast": True,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": True,
            "plain_text": True,
        }

        theme = get_theme_for_config(config)

        # Check that our explicitly set theme values are "default"
        expected_keys = {
            "info",
            "warning",
            "error",
            "success",
            "header",
            "accent",
            "dim",
            "highlight",
            "border",
            "table.header",
            "table.row",
            "panel.title",
            "panel.subtitle",
            "keyword",
            "operator",
            "string",
            "variable",
            "number",
            "comment",
            "foreground",
            "background",
            "progress.description",
            "progress.percentage",
            "progress.bar",
            "progress.bar.complete",
        }
        for key in expected_keys:
            if key in theme.styles:
                value = theme.styles[key]
                self.assertEqual(
                    value,
                    Style.parse("default"),
                    f"Style '{key}' should be default Style when plain text is enabled",
                )

    def test_console_creation_plain_text_mode(self) -> None:
        """Test console creation in plain text mode."""
        from lazyssh.ui import create_console_with_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": True,
        }

        console = create_console_with_config(config)

        # In plain text mode, color_system should be None
        self.assertIsNone(console.color_system)

    def test_display_message_with_fallback_plain_text(self) -> None:
        """Test display message with fallback in plain text mode."""
        from lazyssh.console_instance import display_message_with_fallback

        # Mock the get_ui_config to simulate plain text mode
        with (
            mock.patch(
                "lazyssh.console_instance.get_ui_config",
                return_value={"plain_text": True, "no_rich": False},
            ),
            mock.patch("builtins.print") as mock_print,
        ):
            display_message_with_fallback("Test message", "info")
            mock_print.assert_called_once_with("INFO: Test message")

    def test_display_message_with_fallback_different_types(self) -> None:
        """Test display message with fallback for different message types."""
        from lazyssh.console_instance import display_message_with_fallback

        # Mock the get_ui_config to simulate plain text mode
        with (
            mock.patch(
                "lazyssh.console_instance.get_ui_config",
                return_value={"plain_text": True, "no_rich": False},
            ),
            mock.patch("builtins.print") as mock_print,
        ):
            # Test different message types
            test_cases = [
                ("info", "INFO:"),
                ("success", "SUCCESS:"),
                ("error", "ERROR:"),
                ("warning", "WARNING:"),
                ("unknown", "INFO:"),  # Default fallback
            ]

            for msg_type, expected_prefix in test_cases:
                with self.subTest(msg_type=msg_type):
                    mock_print.reset_mock()
                    display_message_with_fallback("Test message", msg_type)
                    mock_print.assert_called_once_with(f"{expected_prefix} Test message")

    def test_display_message_with_fallback_rich_mode(self) -> None:
        """Test display message with fallback in rich mode."""
        from lazyssh.console_instance import display_message_with_fallback

        # Mock the get_ui_config to simulate rich mode
        with (
            mock.patch(
                "lazyssh.console_instance.get_ui_config",
                return_value={"plain_text": False, "no_rich": False},
            ),
            mock.patch("lazyssh.console_instance.display_info") as mock_display_info,
        ):
            display_message_with_fallback("Test message", "info")
            mock_display_info.assert_called_once_with("Test message")

    def test_plain_text_mode_with_no_rich(self) -> None:
        """Test plain text mode interaction with no-rich mode."""
        from lazyssh.ui import create_console_with_config, get_ui_config

        # Enable both plain text and no-rich
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        os.environ["LAZYSSH_NO_RICH"] = "true"

        config = get_ui_config()
        self.assertTrue(config["plain_text"])
        self.assertTrue(config["no_rich"])

        console = create_console_with_config(config)

        # Both settings should be respected
        self.assertIsNone(console.color_system)  # Plain text

    def test_plain_text_mode_independence(self) -> None:
        """Test that plain text mode is independent of other settings."""
        from lazyssh.console_instance import get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set multiple environment variables
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "true"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"
        os.environ["LAZYSSH_NO_RICH"] = "true"

        config = get_ui_config()

        # All settings should be True
        self.assertTrue(config["plain_text"])
        self.assertTrue(config["high_contrast"])
        self.assertTrue(config["colorblind_mode"])
        self.assertTrue(config["no_animations"])
        self.assertTrue(config["no_rich"])

        # But theme should still be plain text
        theme = get_theme_for_config(config)
        # Check that our explicitly set theme values are "default"
        expected_keys = {
            "info",
            "warning",
            "error",
            "success",
            "header",
            "accent",
            "dim",
            "highlight",
            "border",
            "table.header",
            "table.row",
            "panel.title",
            "panel.subtitle",
            "keyword",
            "operator",
            "string",
            "variable",
            "number",
            "comment",
            "foreground",
            "background",
            "progress.description",
            "progress.percentage",
            "progress.bar",
            "progress.bar.complete",
        }
        for key in expected_keys:
            if key in theme.styles:
                value = theme.styles[key]
                self.assertEqual(
                    value,
                    Style.parse("default"),
                    f"Style '{key}' should be default Style when plain text is enabled",
                )

    def test_plain_text_mode_environment_variable_changes(self) -> None:
        """Test that changes to plain text environment variable are reflected."""
        from lazyssh.ui import get_ui_config

        # Initial state - plain text disabled
        config1 = get_ui_config()
        self.assertFalse(config1["plain_text"])

        # Enable plain text
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        config2 = get_ui_config()
        self.assertTrue(config2["plain_text"])

        # Disable plain text
        os.environ["LAZYSSH_PLAIN_TEXT"] = "false"
        config3 = get_ui_config()
        self.assertFalse(config3["plain_text"])

        # Remove environment variable
        del os.environ["LAZYSSH_PLAIN_TEXT"]
        config4 = get_ui_config()
        self.assertFalse(config4["plain_text"])

    def test_plain_text_mode_console_configuration(self) -> None:
        """Test console configuration in plain text mode."""
        from lazyssh.ui import create_console_with_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": True,
        }

        console = create_console_with_config(config)

        # Check console configuration
        self.assertIsNone(console.color_system)

        # Console should be created successfully
        self.assertIsNotNone(console)

    def test_plain_text_mode_with_refresh_rate(self) -> None:
        """Test plain text mode with refresh rate setting."""
        from lazyssh.ui import create_live_progress, get_ui_config

        # Set plain text and refresh rate
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        os.environ["LAZYSSH_REFRESH_RATE"] = "3"

        config = get_ui_config()
        self.assertTrue(config["plain_text"])
        self.assertEqual(config["refresh_rate"], 3)

        # Live progress should still use configured refresh rate
        live, progress = create_live_progress("Test task")
        self.assertEqual(live.refresh_per_second, 3)

    def test_plain_text_mode_with_animations(self) -> None:
        """Test plain text mode with animation settings."""
        from lazyssh.ui import create_live_progress, get_ui_config

        # Set plain text and disable animations
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        config = get_ui_config()
        self.assertTrue(config["plain_text"])
        self.assertTrue(config["no_animations"])

        # Live progress should not have spinner
        live, progress = create_live_progress("Test task")
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)


if __name__ == "__main__":
    unittest.main()
