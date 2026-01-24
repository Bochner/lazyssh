#!/usr/bin/env python3
"""
Tests for animation disable functionality.
"""

import os
import sys
import unittest
from pathlib import Path

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestAnimationDisable(unittest.TestCase):
    """Test animation disable functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing environment variables
        if "LAZYSSH_NO_ANIMATIONS" in os.environ:
            del os.environ["LAZYSSH_NO_ANIMATIONS"]

    def test_no_animations_default_false(self) -> None:
        """Test that no_animations defaults to False."""
        from lazyssh.ui import get_ui_config

        config = get_ui_config()
        self.assertFalse(config["no_animations"])

    def test_no_animations_true_values(self) -> None:
        """Test that no_animations is True for various true values."""
        from lazyssh.ui import get_ui_config

        true_values = ["true", "TRUE", "True", "1", "yes", "YES", "on", "ON"]
        for value in true_values:
            with self.subTest(value=value):
                os.environ["LAZYSSH_NO_ANIMATIONS"] = value
                config = get_ui_config()
                self.assertTrue(
                    config["no_animations"], f"Value '{value}' should be parsed as True"
                )

    def test_no_animations_false_values(self) -> None:
        """Test that no_animations is False for various false values."""
        from lazyssh.ui import get_ui_config

        false_values = ["false", "FALSE", "0", "no", "NO", "off", "OFF", "", "invalid"]
        for value in false_values:
            with self.subTest(value=value):
                os.environ["LAZYSSH_NO_ANIMATIONS"] = value
                config = get_ui_config()
                self.assertFalse(
                    config["no_animations"], f"Value '{value}' should be parsed as False"
                )

    def test_live_progress_with_animations_enabled(self) -> None:
        """Test live progress creation with animations enabled."""
        from lazyssh.ui import create_live_progress

        # Ensure animations are enabled
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "false"

        live, progress = create_live_progress("Test task")

        # Should have SpinnerColumn when animations are enabled
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertIn("SpinnerColumn", column_types)

    def test_live_progress_with_animations_disabled(self) -> None:
        """Test live progress creation with animations disabled."""
        from lazyssh.ui import create_live_progress

        # Disable animations
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        live, progress = create_live_progress("Test task")

        # Should not have SpinnerColumn when animations are disabled
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)

    def test_efficient_progress_bar_with_animations_enabled(self) -> None:
        """Test efficient progress bar with animations enabled."""
        from lazyssh.ui import create_efficient_progress_bar

        # Ensure animations are enabled
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "false"

        progress = create_efficient_progress_bar()

        # Should create progress bar successfully when animations are enabled
        self.assertIsNotNone(progress)

    def test_efficient_progress_bar_with_animations_disabled(self) -> None:
        """Test efficient progress bar with animations disabled."""
        from lazyssh.ui import create_efficient_progress_bar

        # Disable animations
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        progress = create_efficient_progress_bar()

        # Should create progress bar successfully when animations are disabled
        self.assertIsNotNone(progress)

    def test_animation_setting_independence(self) -> None:
        """Test that animation setting is independent of other settings."""
        from lazyssh.ui import create_live_progress, get_ui_config

        # Set multiple environment variables
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"
        os.environ["LAZYSSH_HIGH_CONTRAST"] = "true"
        os.environ["LAZYSSH_COLORBLIND_MODE"] = "true"
        os.environ["LAZYSSH_PLAIN_TEXT"] = "false"

        config = get_ui_config()

        # Animation setting should be independent
        self.assertTrue(config["no_animations"])
        self.assertTrue(config["high_contrast"])
        self.assertTrue(config["colorblind_mode"])
        self.assertFalse(config["plain_text"])

        # Live progress should still respect animation setting
        live, progress = create_live_progress("Test task")
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)

    def test_animation_setting_with_refresh_rate(self) -> None:
        """Test animation setting interaction with refresh rate."""
        from lazyssh.ui import create_efficient_progress_bar, create_live_progress

        # Set refresh rate and disable animations
        os.environ["LAZYSSH_REFRESH_RATE"] = "5"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        # Live progress should use configured refresh rate
        live, progress = create_live_progress("Test task")
        self.assertEqual(live.refresh_per_second, 5)

        # Efficient progress bar should be created successfully
        efficient_progress = create_efficient_progress_bar()
        self.assertIsNotNone(efficient_progress)

    def test_animation_setting_consistency(self) -> None:
        """Test that animation setting is consistent across different functions."""
        from lazyssh.ui import create_efficient_progress_bar, create_live_progress

        # Disable animations
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        # Both functions should respect the animation setting
        live, progress = create_live_progress("Test task")
        efficient_progress = create_efficient_progress_bar()

        # Live progress should not have spinner
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)

        # Efficient progress should be created successfully
        self.assertIsNotNone(efficient_progress)

    def test_animation_setting_with_plain_text_mode(self) -> None:
        """Test animation setting with plain text mode."""
        from lazyssh.ui import create_live_progress, get_ui_config

        # Enable both plain text and no animations
        os.environ["LAZYSSH_PLAIN_TEXT"] = "true"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        config = get_ui_config()

        # Both settings should be True
        self.assertTrue(config["plain_text"])
        self.assertTrue(config["no_animations"])

        # Live progress should not have spinner
        live, progress = create_live_progress("Test task")
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)

    def test_animation_setting_with_no_rich_mode(self) -> None:
        """Test animation setting with no-rich mode."""
        from lazyssh.ui import create_live_progress, get_ui_config

        # Enable both no-rich and no animations
        os.environ["LAZYSSH_NO_RICH"] = "true"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        config = get_ui_config()

        # Both settings should be True
        self.assertTrue(config["no_rich"])
        self.assertTrue(config["no_animations"])

        # Live progress should not have spinner
        live, progress = create_live_progress("Test task")
        columns = progress.columns
        column_types = [type(col).__name__ for col in columns]
        self.assertNotIn("SpinnerColumn", column_types)

    def test_animation_setting_environment_variable_changes(self) -> None:
        """Test that changes to animation environment variable are reflected."""
        from lazyssh.ui import get_ui_config

        # Initial state - animations enabled
        config1 = get_ui_config()
        self.assertFalse(config1["no_animations"])

        # Disable animations
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"
        config2 = get_ui_config()
        self.assertTrue(config2["no_animations"])

        # Re-enable animations
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "false"
        config3 = get_ui_config()
        self.assertFalse(config3["no_animations"])

        # Remove environment variable
        del os.environ["LAZYSSH_NO_ANIMATIONS"]
        config4 = get_ui_config()
        self.assertFalse(config4["no_animations"])


if __name__ == "__main__":
    unittest.main()
