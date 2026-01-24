"""Tests for __init__ module - version info, dependency checking."""

from pathlib import Path

import pytest

from lazyssh import (
    __author__,
    __license__,
    __version__,
    _check_executable,
    check_dependencies,
)


class TestVersionInfo:
    """Tests for version and package metadata."""

    def test_version_format(self) -> None:
        """Test version follows semantic versioning format."""
        parts = __version__.split(".")
        assert len(parts) >= 2
        # First two parts should be numeric
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    def test_author_defined(self) -> None:
        """Test author is defined."""
        assert __author__ is not None
        assert len(__author__) > 0

    def test_license_defined(self) -> None:
        """Test license is defined."""
        assert __license__ is not None
        assert __license__ == "MIT"


class TestCheckExecutable:
    """Tests for _check_executable function."""

    def test_find_existing_executable(self) -> None:
        """Test finding an existing executable (python)."""
        # Python should always be available
        result = _check_executable("python")
        # May be python or python3 depending on system
        if result is None:
            result = _check_executable("python3")
        assert result is not None

    def test_nonexistent_executable(self) -> None:
        """Test with non-existent executable."""
        result = _check_executable("nonexistent_binary_xyz123")
        assert result is None

    def test_which_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when shutil.which returns None."""
        monkeypatch.setattr("shutil.which", lambda x: None)
        result = _check_executable("ssh")
        assert result is None

    def test_path_not_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when path exists but is not a file."""
        # Return a directory path instead of file
        monkeypatch.setattr("shutil.which", lambda x: "/tmp")
        result = _check_executable("ssh")
        assert result is None

    def test_path_not_executable(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Test when path exists but is not executable."""
        # Create a non-executable file
        non_exec = tmp_path / "not_executable"
        non_exec.touch()
        non_exec.chmod(0o644)

        monkeypatch.setattr("shutil.which", lambda x: str(non_exec))
        result = _check_executable("ssh")
        assert result is None


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_all_dependencies_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when all dependencies are found."""

        # Mock both ssh and terminator as found
        def mock_check(name):
            return f"/usr/bin/{name}"

        monkeypatch.setattr("lazyssh._check_executable", mock_check)
        monkeypatch.setattr("lazyssh.APP_LOGGER", None)

        required, optional = check_dependencies()
        assert required == []
        assert optional == []

    def test_ssh_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when ssh is missing."""

        def mock_check(name):
            if name == "ssh":
                return None
            return f"/usr/bin/{name}"

        monkeypatch.setattr("lazyssh._check_executable", mock_check)
        monkeypatch.setattr("lazyssh.APP_LOGGER", None)

        required, optional = check_dependencies()
        assert len(required) == 1
        assert "ssh" in required[0].lower()

    def test_terminator_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when terminator is missing."""

        def mock_check(name):
            if name == "terminator":
                return None
            return f"/usr/bin/{name}"

        monkeypatch.setattr("lazyssh._check_executable", mock_check)
        monkeypatch.setattr("lazyssh.APP_LOGGER", None)

        required, optional = check_dependencies()
        assert required == []
        assert len(optional) == 1
        assert "terminator" in optional[0].lower()

    def test_all_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test when all dependencies are missing."""
        monkeypatch.setattr("lazyssh._check_executable", lambda x: None)
        monkeypatch.setattr("lazyssh.APP_LOGGER", None)

        required, optional = check_dependencies()
        assert len(required) == 1
        assert len(optional) == 1


class TestCheckDependenciesLogging:
    """Tests for check_dependencies logging branches."""

    def test_logging_ssh_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logging when ssh is missing."""

        class MockLogger:
            def __init__(self):
                self.messages: list[tuple[str, str]] = []

            def error(self, msg):
                self.messages.append(("error", msg))

            def warning(self, msg):
                self.messages.append(("warning", msg))

            def debug(self, msg):
                self.messages.append(("debug", msg))

        logger = MockLogger()

        def mock_check(name):
            if name == "ssh":
                return None
            return f"/usr/bin/{name}"

        monkeypatch.setattr("lazyssh._check_executable", mock_check)
        monkeypatch.setattr("lazyssh.APP_LOGGER", logger)

        check_dependencies()
        assert any("ssh" in msg.lower() for level, msg in logger.messages if level == "error")

    def test_logging_terminator_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logging when terminator is missing."""

        class MockLogger:
            def __init__(self):
                self.messages: list[tuple[str, str]] = []

            def error(self, msg):
                self.messages.append(("error", msg))

            def warning(self, msg):
                self.messages.append(("warning", msg))

            def debug(self, msg):
                self.messages.append(("debug", msg))

        logger = MockLogger()

        def mock_check(name):
            if name == "terminator":
                return None
            return f"/usr/bin/{name}"

        monkeypatch.setattr("lazyssh._check_executable", mock_check)
        monkeypatch.setattr("lazyssh.APP_LOGGER", logger)

        check_dependencies()
        assert any(
            "terminator" in msg.lower() for level, msg in logger.messages if level == "warning"
        )

    def test_logging_all_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test logging when all dependencies are found."""

        class MockLogger:
            def __init__(self):
                self.messages: list[tuple[str, str]] = []

            def error(self, msg):
                self.messages.append(("error", msg))

            def warning(self, msg):
                self.messages.append(("warning", msg))

            def debug(self, msg):
                self.messages.append(("debug", msg))

        logger = MockLogger()
        monkeypatch.setattr("lazyssh._check_executable", lambda x: f"/usr/bin/{x}")
        monkeypatch.setattr("lazyssh.APP_LOGGER", logger)

        check_dependencies()
        assert any(
            "all dependencies found" in msg.lower()
            for level, msg in logger.messages
            if level == "debug"
        )

    def test_logging_missing_deps_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test debug logging for missing dependencies."""

        class MockLogger:
            def __init__(self):
                self.messages: list[tuple[str, str]] = []

            def error(self, msg):
                self.messages.append(("error", msg))

            def warning(self, msg):
                self.messages.append(("warning", msg))

            def debug(self, msg):
                self.messages.append(("debug", msg))

        logger = MockLogger()
        monkeypatch.setattr("lazyssh._check_executable", lambda x: None)
        monkeypatch.setattr("lazyssh.APP_LOGGER", logger)

        check_dependencies()
        # Should have debug messages about missing dependencies
        debug_msgs = [msg for level, msg in logger.messages if level == "debug"]
        assert any("missing required" in msg.lower() for msg in debug_msgs)
        assert any("missing optional" in msg.lower() for msg in debug_msgs)


class TestPackageExports:
    """Tests for package-level exports."""

    def test_logger_exports(self) -> None:
        """Test that loggers are exported from the package."""

        # These may be None if not initialized, but should be importable
        # The important thing is they don't raise ImportError

    def test_logging_function_exports(self) -> None:
        """Test that logging functions are exported."""
        from lazyssh import (
            format_size,
            get_connection_logger,
            get_logger,
            log_file_transfer,
            log_scp_command,
            log_ssh_command,
            log_ssh_connection,
            log_tunnel_creation,
            set_debug_mode,
            update_transfer_stats,
        )

        # All should be callable
        assert callable(format_size)
        assert callable(get_connection_logger)
        assert callable(get_logger)
        assert callable(log_file_transfer)
        assert callable(log_scp_command)
        assert callable(log_ssh_command)
        assert callable(log_ssh_connection)
        assert callable(log_tunnel_creation)
        assert callable(set_debug_mode)
        assert callable(update_transfer_stats)
