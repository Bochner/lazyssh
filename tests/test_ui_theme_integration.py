#!/usr/bin/env python3
"""
Integration tests for UI theme switching functionality.
"""
import os
import sys
import unittest
from pathlib import Path

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestUIThemeIntegration(unittest.TestCase):
    """Test UI theme switching integration."""

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

    def test_theme_switching_high_contrast(self) -> None:
        """Test theme switching to high contrast mode."""
        from lazyssh.console_instance import create_high_contrast_theme, get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set high contrast environment variable
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"

        config = get_ui_config()
        theme = get_theme_for_config(config)
        expected_theme = create_high_contrast_theme()

        # Compare theme styles instead of object identity
        self.assertEqual(theme.styles, expected_theme.styles)
        self.assertTrue(config["high_contrast"])

    def test_theme_switching_colorblind_mode(self) -> None:
        """Test theme switching to colorblind-friendly mode."""
        from lazyssh.console_instance import create_colorblind_friendly_theme, get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set colorblind mode environment variable
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "true"

        config = get_ui_config()
        theme = get_theme_for_config(config)
        expected_theme = create_colorblind_friendly_theme()

        # Compare theme styles instead of object identity
        self.assertEqual(theme.styles, expected_theme.styles)
        self.assertTrue(config["colorblind_mode"])

    def test_theme_switching_plain_text(self) -> None:
        """Test theme switching to plain text mode."""
        from lazyssh.console_instance import get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set plain text environment variable
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"

        config = get_ui_config()
        theme = get_theme_for_config(config)

        self.assertTrue(config["plain_text"])
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

    def test_theme_precedence_plain_text_overrides_others(self) -> None:
        """Test that plain text mode overrides other theme settings."""
        from lazyssh.console_instance import get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set multiple theme environment variables
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "true"
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"

        config = get_ui_config()
        theme = get_theme_for_config(config)

        # Plain text should override other settings
        self.assertTrue(config["plain_text"])
        self.assertTrue(config["high_contrast"])
        self.assertTrue(config["colorblind_mode"])

        # But the theme should be plain text
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
                    str(value),
                    "default",
                    f"Style '{key}' should be 'default' when plain text is enabled",
                )

    def test_theme_precedence_high_contrast_over_colorblind(self) -> None:
        """Test that high contrast mode overrides colorblind mode."""
        from lazyssh.console_instance import create_high_contrast_theme, get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set both high contrast and colorblind mode
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "true"

        config = get_ui_config()
        theme = get_theme_for_config(config)
        expected_theme = create_high_contrast_theme()

        self.assertTrue(config["high_contrast"])
        self.assertTrue(config["colorblind_mode"])

        # High contrast should take precedence
        # Compare theme styles instead of object identity
        self.assertEqual(theme.styles, expected_theme.styles)

    def test_console_creation_with_different_themes(self) -> None:
        """Test console creation with different theme configurations."""
        from lazyssh.ui import create_console_with_config

        # Test default theme
        config_default = {
            "high_contrast": False,
            "no_rich": False,
            "refresh_rate": 4,
            "no_animations": False,
            "colorblind_mode": False,
            "plain_text": False,
        }

        console_default = create_console_with_config(config_default)
        self.assertIsNotNone(console_default)

        # Test high contrast theme
        config_high_contrast = config_default.copy()
        config_high_contrast["high_contrast"] = True

        console_high_contrast = create_console_with_config(config_high_contrast)
        self.assertIsNotNone(console_high_contrast)

        # Test colorblind theme
        config_colorblind = config_default.copy()
        config_colorblind["colorblind_mode"] = True

        console_colorblind = create_console_with_config(config_colorblind)
        self.assertIsNotNone(console_colorblind)

        # Test plain text theme
        config_plain_text = config_default.copy()
        config_plain_text["plain_text"] = True

        console_plain_text = create_console_with_config(config_plain_text)
        self.assertIsNotNone(console_plain_text)

    def test_console_configuration_no_rich_mode(self) -> None:
        """Test console configuration in no-rich mode."""
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
        # In no-rich mode, console should be configured appropriately

    def test_console_configuration_plain_text_mode(self) -> None:
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
        self.assertIsNotNone(console)
        # In plain text mode, color_system should be None
        self.assertIsNone(console.color_system)

    def test_theme_consistency_across_calls(self) -> None:
        """Test that theme selection is consistent across multiple calls."""
        from lazyssh.console_instance import get_theme_for_config
        from lazyssh.ui import get_ui_config

        # Set environment variables
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"

        config1 = get_ui_config()
        theme1 = get_theme_for_config(config1)

        config2 = get_ui_config()
        theme2 = get_theme_for_config(config2)

        # Themes should be identical
        self.assertEqual(theme1.styles, theme2.styles)
        self.assertEqual(config1, config2)

    def test_environment_variable_changes_reflected(self) -> None:
        """Test that changes to environment variables are reflected in configuration."""
        from lazyssh.ui import get_ui_config

        # Initial configuration
        config1 = get_ui_config()
        self.assertFalse(config1["high_contrast"])

        # Change environment variable
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"

        # New configuration should reflect the change
        config2 = get_ui_config()
        self.assertTrue(config2["high_contrast"])

        # Remove environment variable
        del os.environ["LAZYSSH_HIGH_CONTRAST"]

        # Configuration should return to default
        config3 = get_ui_config()
        self.assertFalse(config3["high_contrast"])


if __name__ == "__main__":
    unittest.main()
