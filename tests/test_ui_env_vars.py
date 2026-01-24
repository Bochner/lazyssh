#!/usr/bin/env python3
"""
Tests for UI environment variable functionality.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestUIEnvironmentVariables(unittest.TestCase):
    """Test UI environment variable parsing and configuration."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing environment variables
        env_vars = [
            "LAZYSSH_HIGH_CONTRAST",
            "LAZYSSH_NO_RICH",
            "LAZYSSH_REFRESH_RATE",
            "LAZYSSH_NO_ANIMATIONS",
            "LAZYSSH_COLORBLIND_MODE",
            "LAZYSSH_PLAIN_TEXT",
        ]
        for var in env_vars:
            if var in os.environ:
                del os.environ[var]

    def test_parse_boolean_env_var_true_values(self) -> None:
        """Test parsing boolean environment variables with true values."""
        from lazyssh.console_instance import parse_boolean_env_var

        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        for value in true_values:
            with self.subTest(value=value):
                os.environ["TEST_VAR"] = value
                result = parse_boolean_env_var("TEST_VAR", False)
                self.assertTrue(result, f"Value '{value}' should be parsed as True")

    def test_parse_boolean_env_var_false_values(self) -> None:
        """Test parsing boolean environment variables with false values."""
        from lazyssh.console_instance import parse_boolean_env_var

        false_values = ["false", "FALSE", "0", "no", "NO", "off", "OFF", "", "invalid"]
        for value in false_values:
            with self.subTest(value=value):
                os.environ["TEST_VAR"] = value
                result = parse_boolean_env_var("TEST_VAR", True)
                self.assertFalse(result, f"Value '{value}' should be parsed as False")

    def test_parse_boolean_env_var_default(self) -> None:
        """Test parsing boolean environment variables with default values."""
        from lazyssh.console_instance import parse_boolean_env_var

        # Test with default True
        result = parse_boolean_env_var("NONEXISTENT_VAR", True)
        self.assertTrue(result)

        # Test with default False
        result = parse_boolean_env_var("NONEXISTENT_VAR", False)
        self.assertFalse(result)

    def test_parse_integer_env_var_valid_values(self) -> None:
        """Test parsing integer environment variables with valid values."""
        from lazyssh.console_instance import parse_integer_env_var

        test_cases = [
            ("5", 5),
            ("1", 1),
            ("10", 10),
            ("0", 1),  # Should be clamped to min_val
            ("15", 10),  # Should be clamped to max_val
        ]

        for value, expected in test_cases:
            with self.subTest(value=value, expected=expected):
                os.environ["TEST_VAR"] = value
                result = parse_integer_env_var("TEST_VAR", 4, 1, 10)
                self.assertEqual(result, expected)

    def test_parse_integer_env_var_invalid_values(self) -> None:
        """Test parsing integer environment variables with invalid values."""
        from lazyssh.console_instance import parse_integer_env_var

        invalid_values = ["invalid", "abc", "1.5", "", "  "]
        for value in invalid_values:
            with self.subTest(value=value):
                os.environ["TEST_VAR"] = value
                result = parse_integer_env_var("TEST_VAR", 4, 1, 10)
                self.assertEqual(result, 4, f"Invalid value '{value}' should return default")

    def test_parse_integer_env_var_default(self) -> None:
        """Test parsing integer environment variables with default values."""
        from lazyssh.console_instance import parse_integer_env_var

        result = parse_integer_env_var("NONEXISTENT_VAR", 7, 1, 10)
        self.assertEqual(result, 7)

    def test_get_ui_config_defaults(self) -> None:
        """Test getting UI configuration with default values."""
        from lazyssh.ui import get_ui_config

        config = get_ui_config()

        self.assertIsInstance(config, dict)
        self.assertFalse(config["high_contrast"])
        self.assertFalse(config["no_rich"])
        self.assertEqual(config["refresh_rate"], 4)
        self.assertFalse(config["no_animations"])
        self.assertFalse(config["colorblind_mode"])
        self.assertFalse(config["plain_text"])

    def test_get_ui_config_with_env_vars(self) -> None:
        """Test getting UI configuration with environment variables set."""
        from lazyssh.ui import get_ui_config

        # Set environment variables
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"
        os.environ["LAZYSSH_NO_RICH"] = "1"
        os.environ["LAZYSSH_REFRESH_RATE"] = "2"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "yes"
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "on"
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"

        config = get_ui_config()

        self.assertTrue(config["high_contrast"])
        self.assertTrue(config["no_rich"])
        self.assertEqual(config["refresh_rate"], 2)
        self.assertTrue(config["no_animations"])
        self.assertTrue(config["colorblind_mode"])
        self.assertTrue(config["plain_text"])

    def test_get_theme_for_config_default(self) -> None:
        """Test getting default theme."""
        from lazyssh.console_instance import LAZYSSH_THEME, get_theme_for_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": False,
        }

        theme = get_theme_for_config(config)
        self.assertEqual(theme, LAZYSSH_THEME)

    def test_get_theme_for_config_high_contrast(self) -> None:
        """Test getting high contrast theme."""
        from lazyssh.console_instance import create_high_contrast_theme, get_theme_for_config

        config = {
            "high_contrast": True,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": False,
        }

        theme = get_theme_for_config(config)
        expected_theme = create_high_contrast_theme()

        # Compare theme styles instead of object identity
        self.assertEqual(theme.styles, expected_theme.styles)

    def test_get_theme_for_config_colorblind(self) -> None:
        """Test getting colorblind-friendly theme."""
        from lazyssh.console_instance import create_colorblind_friendly_theme, get_theme_for_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": True,
            "plain_text": False,
        }

        theme = get_theme_for_config(config)
        expected_theme = create_colorblind_friendly_theme()

        # Compare theme styles instead of object identity
        self.assertEqual(theme.styles, expected_theme.styles)

    def test_get_theme_for_config_plain_text(self) -> None:
        """Test getting plain text theme."""
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
                    str(value), "default", f"Style '{key}' should be 'default' in plain text mode"
                )

    def test_create_console_with_config(self) -> None:
        """Test creating console with configuration."""
        from lazyssh.ui import create_console_with_config

        config = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": False,
        }

        console = create_console_with_config(config)
        self.assertIsNotNone(console)

    def test_create_console_with_no_rich_config(self) -> None:
        """Test creating console with no-rich configuration."""
        from lazyssh.ui import create_console_with_config

        config = {
            "high_contrast": False,
            "no_rich": True,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": False,
        }

        console = create_console_with_config(config)
        self.assertIsNotNone(console)
        # The console should be configured for basic terminal compatibility

    def test_get_current_ui_config(self) -> None:
        """Test getting current UI configuration."""
        from lazyssh.ui import get_current_ui_config

        config = get_current_ui_config()
        self.assertIsInstance(config, dict)
        self.assertIn("high_contrast", config)
        self.assertIn("no_rich", config)
        self.assertIn("refresh_rate", config)
        self.assertIn("no_animations", config)
        self.assertIn("colorblind_mode", config)
        self.assertIn("plain_text", config)

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

    def test_display_message_with_fallback_no_rich(self) -> None:
        """Test display message with fallback in no-rich mode."""
        from lazyssh.console_instance import display_message_with_fallback

        # Mock the get_ui_config to simulate no-rich mode
        with (
            mock.patch(
                "lazyssh.console_instance.get_ui_config",
                return_value={"plain_text": False, "no_rich": True},
            ),
            mock.patch("builtins.print") as mock_print,
        ):
            display_message_with_fallback("Test message", "error")
            mock_print.assert_called_once_with("ERROR: Test message")

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


if __name__ == "__main__":
    unittest.main()
