"""
LazySSH - A comprehensive SSH toolkit for managing connections and tunnels.

This package provides tools for managing SSH connections, creating tunnels,
and opening terminal sessions through an interactive command-line interface.
"""

__version__ = "1.4.0"
__author__ = "Bochner"
__email__ = ""
__license__ = "MIT"

import os
import shutil
from pathlib import Path

# Include logging module in the package exports
from .logging_module import (  # noqa: F401
    APP_LOGGER,
    CMD_LOGGER,
    SCP_LOGGER,
    SSH_LOGGER,
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


def check_dependencies() -> tuple[list[str], list[str]]:
    """
    Check for required and optional external dependencies.

    Returns:
        A tuple of (required_missing, optional_missing) where each is a list of missing dependencies.
    """
    required_missing = []
    optional_missing = []

    # Check for SSH client (required)
    ssh_path = _check_executable("ssh")
    if not ssh_path:
        required_missing.append("OpenSSH Client (ssh)")
        if APP_LOGGER:
            APP_LOGGER.error("OpenSSH Client (ssh) not found but required")

    # Check for terminator (optional)
    terminator_path = _check_executable("terminator")
    if not terminator_path:
        optional_missing.append("Terminator terminal emulator (optional)")
        if APP_LOGGER:
            APP_LOGGER.warning("Terminator terminal emulator not found (optional)")

    if required_missing or optional_missing:
        if APP_LOGGER:
            if required_missing:
                APP_LOGGER.debug(
                    f"Dependencies check: Missing required: {', '.join(required_missing)}"
                )
            if optional_missing:
                APP_LOGGER.debug(
                    f"Dependencies check: Missing optional: {', '.join(optional_missing)}"
                )
    else:
        if APP_LOGGER:
            APP_LOGGER.debug("Dependencies check: All dependencies found")

    return (required_missing, optional_missing)


def _check_executable(name: str) -> str | None:
    """
    Check if an executable is available in the PATH.

    Args:
        name: The name of the executable to check for

    Returns:
        The path to the executable if found, None otherwise
    """
    # Use shutil.which() for cross-platform compatibility
    path = shutil.which(name)
    if path:
        # Additional validation: verify the path is a file and executable
        path_obj = Path(path)
        if path_obj.is_file() and os.access(path, os.X_OK):
            return path
    return None
