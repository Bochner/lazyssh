"""Configuration utilities for LazySSH"""

import os
import re
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Literal

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


def initialize_config_file(config_path: str | None = None) -> bool:
    """
    Initialize the configuration file with commented examples if it doesn't exist.

    Args:
        config_path: Optional custom path to config file

    Returns:
        True if file was created or already exists, False on error
    """
    file_path = get_config_file_path(config_path)

    # If file already exists, don't overwrite it
    if file_path.exists():
        return True

    if not ensure_config_directory():
        return False

    try:
        # Create config file with commented example
        example_config = """# LazySSH Connection Configuration File
#
# This file stores saved SSH connection configurations in TOML format.
# You can manually edit this file or use the 'save-config' command in LazySSH.
#
# Example configuration with all possible options:
#
# [example-connection]
# host = "192.168.1.100"              # SSH server hostname or IP (required)
# port = 22                           # SSH port (required, default: 22)
# username = "admin"                  # SSH username (required)
# socket_name = "my-connection"       # Control socket name (required)
# ssh_key = "~/.ssh/id_rsa"           # Path to SSH private key (optional)
# shell = "bash"                      # Shell to use (optional, e.g., bash, zsh, fish)
# no_term = false                     # Disable terminal allocation (optional, default: false)
# proxy_port = 9050                   # SOCKS proxy port (optional)
#
# Usage:
#   1. Save a connection after establishing it (prompted automatically)
#   2. Load configurations: lazyssh --config
#   3. Connect to saved config: use 'connect <name>' command
#   4. View saved configs: use 'config' or 'configs' command
#
# Add your configurations below:

"""
        with open(file_path, "w") as f:
            f.write(example_config)

        # Set permissions to 600 (owner read/write only)
        os.chmod(file_path, 0o600)

        if APP_LOGGER:
            APP_LOGGER.info(f"Initialized configuration file: {file_path}")
        return True

    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to initialize configuration file: {e}")
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
    Save or update a connection configuration, preserving comments.

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

    # Initialize the file if it doesn't exist
    if not file_path.exists():
        if not initialize_config_file():
            return False

    try:
        # Read existing file content as text to preserve comments
        with open(file_path) as f:
            file_content = f.read()

        # Check if config already exists
        existing_configs = load_configs()
        config_exists_flag = name in existing_configs

        if config_exists_flag:
            # Update existing config by replacing the section
            # Pattern to match the config section (including the header and all key-value pairs)
            # This matches from [name] to the next section or end of file
            section_pattern = rf"^\[{re.escape(name)}\][^\[]*"

            # Generate new config section
            config_lines = [f"[{name}]"]
            for key, value in connection_params.items():
                if isinstance(value, str):
                    config_lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    config_lines.append(f"{key} = {str(value).lower()}")
                elif value is not None:
                    config_lines.append(f"{key} = {value}")
            new_section = "\n".join(config_lines) + "\n"

            # Replace the section
            file_content = re.sub(
                section_pattern, new_section.rstrip(), file_content, flags=re.MULTILINE
            )
        else:
            # Append new config to the end of the file
            # Make sure there's a blank line before the new section
            if not file_content.endswith("\n\n"):
                if file_content.endswith("\n"):
                    file_content += "\n"
                else:
                    file_content += "\n\n"

            # Generate new config section
            config_lines = [f"[{name}]"]
            for key, value in connection_params.items():
                if isinstance(value, str):
                    config_lines.append(f'{key} = "{value}"')
                elif isinstance(value, bool):
                    config_lines.append(f"{key} = {str(value).lower()}")
                elif value is not None:
                    config_lines.append(f"{key} = {value}")
            file_content += "\n".join(config_lines) + "\n"

        # Write atomically (write to temp file, then rename)
        temp_fd, temp_path = tempfile.mkstemp(
            dir="/tmp/lazyssh", prefix=".connections_", suffix=".tmp"
        )
        try:
            with os.fdopen(temp_fd, "w") as f:
                f.write(file_content)

            # Set permissions before moving
            os.chmod(temp_path, 0o600)

            # Atomic move
            os.replace(temp_path, file_path)

            if APP_LOGGER:
                APP_LOGGER.info(f"Configuration '{name}' saved to {file_path}")
            return True
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                if APP_LOGGER:
                    APP_LOGGER.error(
                        f"Failed to clean up temporary file {temp_path}: {cleanup_error}"
                    )
                else:
                    print(
                        f"Error: Failed to clean up temporary file {temp_path}: {cleanup_error}",
                        flush=True,
                    )
            raise

    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to save configuration '{name}': {e}")
        return False


def delete_config(name: str) -> bool:
    """
    Delete a saved configuration, preserving comments.

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
        # Load existing configs to check if it exists
        existing_configs = load_configs()

        if name not in existing_configs:
            if APP_LOGGER:
                APP_LOGGER.warning(f"Configuration '{name}' not found")
            return False

        # Read existing file content as text to preserve comments
        with open(file_path) as f:
            file_content = f.read()

        # Remove the config section from the file
        # Pattern to match the config section (including the header and all key-value pairs)
        # This matches from [name] to the next section or end of file
        section_pattern = rf"^\[{re.escape(name)}\][^\[]*"

        # Remove the section
        file_content = re.sub(section_pattern, "", file_content, flags=re.MULTILINE)

        # Clean up any extra blank lines (more than 2 consecutive)
        file_content = re.sub(r"\n{3,}", "\n\n", file_content)

        # Write atomically
        temp_fd, temp_path = tempfile.mkstemp(
            dir="/tmp/lazyssh", prefix=".connections_", suffix=".tmp"
        )
        try:
            with os.fdopen(temp_fd, "w") as f:
                f.write(file_content)

            # Set permissions before moving
            os.chmod(temp_path, 0o600)

            # Atomic move
            os.replace(temp_path, file_path)

            if APP_LOGGER:
                APP_LOGGER.info(f"Configuration '{name}' deleted from {file_path}")
            return True
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                if APP_LOGGER:
                    APP_LOGGER.error(
                        f"Failed to clean up temporary file {temp_path}: {cleanup_error}"
                    )
                else:
                    print(
                        f"Error: Failed to clean up temporary file {temp_path}: {cleanup_error}",
                        flush=True,
                    )
            raise

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


def backup_config(config_path: str | None = None) -> tuple[bool, str]:
    """
    Create a backup of the connections configuration file.

    Args:
        config_path: Optional custom path to config file

    Returns:
        Tuple of (success: bool, message: str)
    """
    file_path = get_config_file_path(config_path)
    backup_path = Path(str(file_path) + ".backup")

    # Check if original config exists
    if not file_path.exists():
        if APP_LOGGER:
            APP_LOGGER.debug(f"No configuration file to backup: {file_path}")
        return False, "No configuration file to backup"

    try:
        # Read the original file
        with open(file_path, "rb") as f:
            content = f.read()

        # Ensure directory exists
        if not ensure_config_directory():
            return False, "Cannot create backup: directory creation failed"

        # Write atomically (write to temp file, then rename)
        temp_fd, temp_path = tempfile.mkstemp(dir="/tmp/lazyssh", prefix=".backup_", suffix=".tmp")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(content)

            # Set permissions to 600 (owner read/write only)
            os.chmod(temp_path, 0o600)

            # Atomic move (overwrites existing backup if present)
            os.replace(temp_path, backup_path)

            if APP_LOGGER:
                APP_LOGGER.info(f"Configuration backed up to {backup_path}")
            return True, f"Configuration backed up to {backup_path}"

        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                if APP_LOGGER:
                    APP_LOGGER.error(
                        f"Failed to clean up temporary file {temp_path}: {cleanup_error}"
                    )
            raise

    except PermissionError as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Permission denied creating backup: {e}")
        return False, "Cannot create backup: permission denied"
    except Exception as e:
        if APP_LOGGER:
            APP_LOGGER.error(f"Failed to create backup: {e}")
        return False, f"Cannot create backup: {e}"
