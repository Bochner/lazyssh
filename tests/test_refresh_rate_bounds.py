#!/usr/bin/env python3
"""
Tests for refresh rate bounds checking functionality.
"""
import os
import sys
import unittest
from pathlib import Path

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestRefreshRateBounds(unittest.TestCase):
    """Test refresh rate bounds checking."""

    def setUp(self) -> None:
        """Set up test environment."""
        # Clear any existing environment variables
        if "LAZYSSH_REFRESH_RATE" in os.environ:
            del os.environ["LAZYSSH_REFRESH_RATE"]

    def test_refresh_rate_within_bounds(self) -> None:
        """Test refresh rate values within valid bounds."""
        from lazyssh.console_instance import parse_integer_env_var

        test_cases = [
            ("1", 1),
            ("2", 2),
            ("5", 5),
            ("8", 8),
            ("10", 10),
        ]

        for value, expected in test_cases:
            with self.subTest(value=value, expected=expected):
                os.environ["LAZYSSH_REFRESH_RATE"] = value
                result = parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10)
                self.assertEqual(result, expected)

    def test_refresh_rate_below_minimum(self) -> None:
        """Test refresh rate values below minimum."""
        from lazyssh.console_instance import parse_integer_env_var

        test_cases = [
            ("0", 1),  # Should be clamped to 1
            ("-1", 1),  # Should be clamped to 1
            ("-5", 1),  # Should be clamped to 1
        ]

        for value, expected in test_cases:
            with self.subTest(value=value, expected=expected):
                os.environ["LAZYSSH_REFRESH_RATE"] = value
                result = parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10)
                self.assertEqual(result, expected)

    def test_refresh_rate_above_maximum(self) -> None:
        """Test refresh rate values above maximum."""
        from lazyssh.console_instance import parse_integer_env_var

        test_cases = [
            ("11", 10),  # Should be clamped to 10
            ("15", 10),  # Should be clamped to 10
            ("100", 10),  # Should be clamped to 10
        ]

        for value, expected in test_cases:
            with self.subTest(value=value, expected=expected):
                os.environ["LAZYSSH_REFRESH_RATE"] = value
                result = parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10)
                self.assertEqual(result, expected)

    def test_refresh_rate_invalid_values(self) -> None:
        """Test refresh rate with invalid values."""
        from lazyssh.console_instance import parse_integer_env_var

        invalid_values = [
            "invalid",
            "abc",
            "1.5",
            "2.7",
            "",
            "  ",
            "1.0",
            "2.0",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                os.environ["LAZYSSH_REFRESH_RATE"] = value
                result = parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10)
                self.assertEqual(result, 4, f"Invalid value '{value}' should return default")

    def test_refresh_rate_default_value(self) -> None:
        """Test refresh rate default value when not set."""
        from lazyssh.console_instance import parse_integer_env_var

        # Ensure environment variable is not set
        if "LAZYSSH_REFRESH_RATE" in os.environ:
            del os.environ["LAZYSSH_REFRESH_RATE"]

        result = parse_integer_env_var("LAZYSSH_REFRESH_RATE", 4, 1, 10)
        self.assertEqual(result, 4)

    def test_refresh_rate_edge_cases(self) -> None:
        """Test refresh rate edge cases."""
        from lazyssh.console_instance import parse_integer_env_var

        # Test with different min/max bounds
        test_cases = [
            ("0", 1, 1, 5),  # min=1, max=5
            ("6", 3, 1, 5),  # min=1, max=5, value=6 should clamp to 5
            ("-1", 3, 1, 5),  # min=1, max=5, value=-1 should clamp to 1
        ]

        for value, default, min_val, max_val in test_cases:
            with self.subTest(value=value, default=default, min_val=min_val, max_val=max_val):
                os.environ["TEST_VAR"] = value
                result = parse_integer_env_var("TEST_VAR", default, min_val, max_val)
                expected = max(min_val, min(max_val, int(value)))
                self.assertEqual(result, expected)

    def test_refresh_rate_in_ui_config(self) -> None:
        """Test refresh rate in UI configuration."""
        from lazyssh.ui import get_ui_config

        # Test default
        config = get_ui_config()
        self.assertEqual(config["refresh_rate"], 4)

        # Test valid value
        os.environ["LAZYSSH_REFRESH_RATE"] = "7"
        config = get_ui_config()
        self.assertEqual(config["refresh_rate"], 7)

        # Test clamped value
        os.environ["LAZYSSH_REFRESH_RATE"] = "15"
        config = get_ui_config()
        self.assertEqual(config["refresh_rate"], 10)

        # Test invalid value
        os.environ["LAZYSSH_REFRESH_RATE"] = "invalid"
        config = get_ui_config()
        self.assertEqual(config["refresh_rate"], 4)

    def test_refresh_rate_used_in_live_displays(self) -> None:
        """Test that refresh rate is used in live display functions."""
        from lazyssh.ui import create_live_progress, create_live_status_display, create_live_table

        # Set a specific refresh rate
        os.environ["LAZYSSH_REFRESH_RATE"] = "2"

        # Test live progress
        live, progress = create_live_progress("Test task")
        self.assertEqual(live.refresh_per_second, 2)

        # Test live status display
        live_status = create_live_status_display()
        self.assertEqual(live_status.refresh_per_second, 2)

        # Test live table
        live_table, table = create_live_table("Test Table")
        self.assertEqual(live_table.refresh_per_second, 2)

    def test_refresh_rate_consistency(self) -> None:
        """Test that refresh rate is consistent across different functions."""
        from lazyssh.ui import create_live_progress, create_live_status_display, create_live_table

        # Set refresh rate
        os.environ["LAZYSSH_REFRESH_RATE"] = "3"

        # Create different live displays
        live1, _ = create_live_progress("Task 1")
        live2 = create_live_status_display()
        live3, _ = create_live_table("Table 1")

        # All should have the same refresh rate
        self.assertEqual(live1.refresh_per_second, 3)
        self.assertEqual(live2.refresh_per_second, 3)
        self.assertEqual(live3.refresh_per_second, 3)

    def test_refresh_rate_with_animations_disabled(self) -> None:
        """Test refresh rate behavior when animations are disabled."""
        from lazyssh.ui import create_efficient_progress_bar

        # Set refresh rate and disable animations
        os.environ["LAZYSSH_REFRESH_RATE"] = "5"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "true"

        progress = create_efficient_progress_bar()

        # When animations are disabled, progress should be created successfully
        self.assertIsNotNone(progress)

    def test_refresh_rate_with_animations_enabled(self) -> None:
        """Test refresh rate behavior when animations are enabled."""
        from lazyssh.ui import create_efficient_progress_bar

        # Set refresh rate and enable animations
        os.environ["LAZYSSH_REFRESH_RATE"] = "5"
        os.environ["LAZYSSH_NO_ANIMATIONS"] = "false"

        progress = create_efficient_progress_bar()

        # When animations are enabled, progress should be created successfully
        self.assertIsNotNone(progress)


if __name__ == "__main__":
    unittest.main()
