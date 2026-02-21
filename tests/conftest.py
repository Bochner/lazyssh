"""Pytest configuration and fixtures for lazyssh tests.

TEST ISOLATION REQUIREMENTS
===========================
All tests MUST be isolated from external dependencies for CI/CD compatibility.
Tests that make real subprocess calls or network connections will timeout in CI.

Always mock these operations:
- subprocess.run() / subprocess.Popen() - Mock to prevent process execution
- Confirm.ask() / Prompt.ask() / input() - Mock to prevent stdin blocking
- SSH connections and network calls - Mock to prevent network dependencies
- SCPMode with selected_connection - Mock subprocess.run before instantiation

Example pattern for subprocess mocking:
    mock_result = mock.MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "/home/user"
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

Timeout protection: pytest-timeout enforces 30s per test.
"""

import shutil
from pathlib import Path

import pytest

# The base directory used by lazyssh for runtime files
LAZYSSH_TMP_DIR = Path("/tmp/lazyssh")


def pytest_configure(config: pytest.Config) -> None:
    """Clean up /tmp/lazyssh at the start of each test session.

    This runs once at the beginning of the test session to remove
    artifacts from previous test runs.
    """
    if LAZYSSH_TMP_DIR.exists():
        # Remove all contents but keep the directory
        for item in LAZYSSH_TMP_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except OSError:
                # Ignore errors (e.g., permission issues, files in use)
                pass


@pytest.fixture
def clean_lazyssh_dir() -> Path:
    """Fixture that ensures a clean /tmp/lazyssh directory for a test.

    Use this fixture when a test needs a guaranteed clean state.
    The directory is cleaned before the test runs.

    Yields:
        Path to /tmp/lazyssh directory
    """
    # Clean before test
    if LAZYSSH_TMP_DIR.exists():
        for item in LAZYSSH_TMP_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except OSError:
                pass

    # Ensure directory exists
    LAZYSSH_TMP_DIR.mkdir(parents=True, exist_ok=True)

    return LAZYSSH_TMP_DIR


@pytest.fixture
def temp_connection_dir(tmp_path: Path) -> Path:
    """Fixture that provides an isolated temporary connection directory.

    Use this instead of /tmp/lazyssh when tests don't need the actual
    lazyssh directory structure. This provides better test isolation.

    Yields:
        Path to a temporary directory that mimics connection structure
    """
    conn_dir = tmp_path / "lazyssh" / "test-conn.d"
    conn_dir.mkdir(parents=True)
    (conn_dir / "downloads").mkdir()
    (conn_dir / "uploads").mkdir()
    (conn_dir / "logs").mkdir()
    return conn_dir
