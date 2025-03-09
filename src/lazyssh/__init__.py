"""
LazySSH - A comprehensive SSH toolkit for managing connections and tunnels.

This package provides tools for managing SSH connections, creating tunnels,
and opening terminal sessions through an interactive command-line interface.
"""

__version__ = "1.0.0"
__author__ = "Bochner"
__email__ = ""
__license__ = "MIT"

import os
import subprocess
from typing import List, Optional


def check_dependencies() -> List[str]:
    """
    Check for required external dependencies.

    Returns:
        A list of missing dependencies, empty if all are installed.
    """
    missing_deps = []

    # Check for SSH client
    ssh_path = _check_executable("ssh")
    if not ssh_path:
        missing_deps.append("OpenSSH Client (ssh)")

    # Check for terminator (recommended but not strictly required)
    terminator_path = _check_executable("terminator")
    if not terminator_path:
        missing_deps.append("Terminator terminal emulator (optional)")

    return missing_deps


def _check_executable(name: str) -> Optional[str]:
    """
    Check if an executable is available in the PATH.

    Args:
        name: The name of the executable to check for

    Returns:
        The path to the executable if found, None otherwise
    """
    try:
        path = subprocess.check_output(["which", name], universal_newlines=True).strip()
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
        return None
    except subprocess.CalledProcessError:
        return None
