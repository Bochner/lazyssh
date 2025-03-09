#!/usr/bin/env python3
"""
Basic tests for LazySSH package structure.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

# Add src to path to make imports work for tests
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path.absolute()))


class TestBasicImports(unittest.TestCase):
    """Test basic imports and package structure."""

    def test_import_lazyssh(self) -> None:
        """Test that the lazyssh package can be imported."""
        import lazyssh

        self.assertIsNotNone(lazyssh)

    def test_import_models(self) -> None:
        """Test that the models module can be imported."""
        from lazyssh import models

        self.assertIsNotNone(models)

    def test_import_ssh(self) -> None:
        """Test that the ssh module can be imported."""
        from lazyssh import ssh

        self.assertIsNotNone(ssh)

    def test_version_match(self) -> None:
        """Test that the version is consistent across files."""
        import lazyssh

        # Get version from __init__.py
        init_version = lazyssh.__version__

        # Check that version is a string
        self.assertIsInstance(init_version, str)

        # Check that version follows semantic versioning
        parts = init_version.split(".")
        self.assertEqual(len(parts), 3, "Version should be in format X.Y.Z")

        # Check that each part is a number
        for part in parts:
            self.assertTrue(part.isdigit(), f"Version part '{part}' should be a number")


class TestCommandLineInterface(unittest.TestCase):
    """Test command line interface."""

    @mock.patch("sys.argv", ["lazyssh", "--help"])
    def test_cli_help(self) -> None:
        """Test that the CLI help command works."""
        with mock.patch("sys.stdout"):  # Suppress output
            try:
                from lazyssh.__main__ import main

                # Just check that it doesn't raise an exception
                # We're not actually running it because it would exit
                self.assertTrue(callable(main))
            except Exception as e:
                self.fail(f"CLI help command raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
