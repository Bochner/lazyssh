#!/usr/bin/env python3
"""
Basic tests for LazySSH package structure.
"""
import importlib.util
import os
import sys
import unittest
from unittest import mock

# Add src to path to make imports work for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))


class TestBasicImports(unittest.TestCase):
    """Test basic imports and package structure."""

    def test_import_lazyssh(self):
        """Test that the lazyssh package can be imported."""
        import lazyssh
        self.assertIsNotNone(lazyssh)
        self.assertIsNotNone(lazyssh.__version__)
        
    def test_import_models(self):
        """Test that models can be imported."""
        from lazyssh import models
        self.assertIsNotNone(models)
        
    def test_import_ssh(self):
        """Test that ssh module can be imported."""
        from lazyssh import ssh
        self.assertIsNotNone(ssh)
    
    def test_version_match(self):
        """Test that version in __init__.py matches setup.py."""
        # Get version from __init__.py
        import lazyssh
        init_version = lazyssh.__version__
        
        # Parse setup.py to find version
        setup_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "setup.py"))
        with open(setup_path, 'r', encoding='utf-8') as f:
            setup_contents = f.read()
        
        # Simple parsing for version
        for line in setup_contents.splitlines():
            if 'version=' in line or 'version =' in line:
                # Very basic extraction, just for testing
                setup_version = line.split('=')[1].strip().strip('"\'').strip(',')
                break
        
        self.assertEqual(init_version, setup_version, 
                         f"Version mismatch: __init__.py: {init_version}, setup.py: {setup_version}")


class TestCommandLineInterface(unittest.TestCase):
    """Test command-line interface functionality."""
    
    @mock.patch('sys.argv', ['lazyssh', '--help'])
    def test_cli_help(self):
        """Test that CLI help option doesn't crash."""
        import lazyssh.__main__ as main_module
        # Just make sure this doesn't crash
        with mock.patch('click.core.Command.main') as mock_main:
            mock_main.return_value = None
            with self.assertRaises(SystemExit) as cm:
                main_module.main()
            # Help exits with code 0
            self.assertEqual(cm.exception.code, 0)


if __name__ == "__main__":
    unittest.main() 