"""Configuration utilities for LazySSH"""

import os
from typing import Any


def load_config() -> dict[str, Any]:
    """Load configuration from environment variables or config file"""
    config = {
        "ssh_path": os.environ.get("LAZYSSH_SSH_PATH", "/usr/bin/ssh"),
        "terminal_emulator": os.environ.get("LAZYSSH_TERMINAL", "terminator"),
        "control_path_base": os.environ.get("LAZYSSH_CONTROL_PATH", "/tmp/"),
    }
    return config
