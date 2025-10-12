"""Configuration utilities for LazySSH"""

import os
import re
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Literal

import tomli_w

from .logging_module import APP_LOGGER

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


# Connection Configuration Management


def get_config_file_path(custom_path: str | None = None) -> Path:
    """
    Get the path to the connections configuration file.

    Args:
        custom_path: Optional custom path to use instead of default

    Returns:
        Path object pointing to the configuration file
    """
    if custom_path:
        return Path(custom_path)
    return Path("/tmp/lazyssh/connections.conf")


def ensure_config_directory() -> bool:
    """
    Ensure the configuration directory exists with proper permissions.

    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        config_dir = Path("/tmp/lazyssh")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_dir.chmod(0o700)
        if APP_LOGGER:
            APP_LOGGER.debug(f"Configuration directory ensured: {config_dir}")
        return True
    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to create configuration directory: {e}")
        return False


def validate_config_name(name: str) -> bool:
    """
    Validate that a configuration name contains only allowed characters.

    Args:
        name: The configuration name to validate

    Returns:
        True if valid, False otherwise
    """
    # Allow alphanumeric characters, dashes, and underscores
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", name))


def load_configs(config_path: str | None = None) -> dict[str, dict[str, Any]]:
    """
    Load all saved configurations from the TOML file.

    Args:
        config_path: Optional custom path to config file

    Returns:
        Dictionary mapping config names to their parameters.
        Returns empty dict if file doesn't exist or has errors.
    """
    file_path = get_config_file_path(config_path)

    if not file_path.exists():
        if APP_LOGGER:
            APP_LOGGER.debug(f"Configuration file not found: {file_path}")
        return {}

    try:
        with open(file_path, "rb") as f:
            configs = tomllib.load(f)

        if APP_LOGGER:
            APP_LOGGER.info(f"Loaded {len(configs)} configuration(s) from {file_path}")

        return configs
    except tomllib.TOMLDecodeError as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to parse TOML configuration: {e}")
        return {}
    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to load configurations: {e}")
        return {}


def save_config(name: str, connection_params: dict[str, Any]) -> bool:
    """
    Save or update a connection configuration.

    Args:
        name: Configuration name
        connection_params: Dictionary of connection parameters

    Returns:
        True if saved successfully, False otherwise
    """
    if not validate_config_name(name):
        if APP_LOGGER:
            APP_LOGGER.error(f"Invalid configuration name: {name}")
        return False

    if not ensure_config_directory():
        return False

    file_path = get_config_file_path()

    try:
        # Load existing configs
        existing_configs = load_configs() if file_path.exists() else {}

        # Update with new config
        existing_configs[name] = connection_params

        # Write atomically (write to temp file, then rename)
        temp_fd, temp_path = tempfile.mkstemp(dir="/tmp/lazyssh", prefix=".connections_", suffix=".tmp")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                tomli_w.dump(existing_configs, f)

            # Set permissions before moving
            os.chmod(temp_path, 0o600)

            # Atomic move
            os.replace(temp_path, file_path)

            if APP_LOGGER:
                APP_LOGGER.info(f"Configuration '{name}' saved to {file_path}")
            return True
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise e

    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to save configuration '{name}': {e}")
        return False


def delete_config(name: str) -> bool:
    """
    Delete a saved configuration.

    Args:
        name: Name of the configuration to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    file_path = get_config_file_path()

    if not file_path.exists():
        if APP_LOGGER:
            APP_LOGGER.warning(f"Configuration file not found: {file_path}")
        return False

    try:
        # Load existing configs
        existing_configs = load_configs()

        if name not in existing_configs:
            if APP_LOGGER:
                APP_LOGGER.warning(f"Configuration '{name}' not found")
            return False

        # Remove the config
        del existing_configs[name]

        # Write atomically
        temp_fd, temp_path = tempfile.mkstemp(dir="/tmp/lazyssh", prefix=".connections_", suffix=".tmp")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                tomli_w.dump(existing_configs, f)

            # Set permissions before moving
            os.chmod(temp_path, 0o600)

            # Atomic move
            os.replace(temp_path, file_path)

            if APP_LOGGER:
                APP_LOGGER.info(f"Configuration '{name}' deleted from {file_path}")
            return True
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise e

    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to delete configuration '{name}': {e}")
        return False


def config_exists(name: str) -> bool:
    """
    Check if a configuration with the given name exists.

    Args:
        name: Configuration name to check

    Returns:
        True if configuration exists, False otherwise
    """
    configs = load_configs()
    return name in configs


def get_config(name: str) -> dict[str, Any] | None:
    """
    Get a specific configuration by name.

    Args:
        name: Configuration name

    Returns:
        Dictionary of connection parameters, or None if not found
    """
    configs = load_configs()
    return configs.get(name)
