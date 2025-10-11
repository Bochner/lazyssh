"""Configuration utilities for LazySSH"""

import os
from typing import Any, Literal

# Valid terminal method values
TerminalMethod = Literal["auto", "terminator", "native"]


def get_terminal_method() -> TerminalMethod:
    """
    Get the configured terminal method from environment variable.

    Returns:
        The configured terminal method, defaults to 'auto'.
        Valid values: 'auto', 'terminator', 'native'
    """
    method = os.environ.get("LAZYSSH_TERMINAL_METHOD", "auto").lower()

    if method not in ["auto", "terminator", "native"]:
        # Invalid value, default to auto
        return "auto"

    return method  # type: ignore


def load_config() -> dict[str, Any]:
    """Load configuration from environment variables or config file"""
    config = {
        "ssh_path": os.environ.get("LAZYSSH_SSH_PATH", "/usr/bin/ssh"),
        "terminal_emulator": os.environ.get("LAZYSSH_TERMINAL", "terminator"),
        "control_path_base": os.environ.get("LAZYSSH_CONTROL_PATH", "/tmp/"),
        "terminal_method": get_terminal_method(),
    }
    return config
