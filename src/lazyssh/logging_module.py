#!/usr/bin/env python3
"""
LazySSH Logging Module - Provides robust logging capabilities using Python's logging and rich.logging.
"""

import logging
import os

# import sys
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import rich.logging
from rich.console import Console

# from typing import Any, Dict, Optional

# Define log levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Default log directory
DEFAULT_LOG_DIR = Path("/tmp/lazyssh/logs")  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
FILE_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# Debug mode flag
DEBUG_MODE = False

# Global settings
LOG_DIR = Path("/tmp/lazyssh/logs")  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
CONNECTION_LOG_DIR_TEMPLATE = "/tmp/lazyssh/{connection_name}.d/logs"  # noqa: S108  # /tmp/lazyssh is the documented runtime directory
DEFAULT_LOG_LEVEL = "INFO"

# Global console instance for Rich logging
console = Console()

# Global loggers
APP_LOGGER: logging.Logger | None = None
SSH_LOGGER: logging.Logger | None = None
SCP_LOGGER: logging.Logger | None = None
CMD_LOGGER: logging.Logger | None = None
CONFIG_LOGGER: logging.Logger | None = None


class TransferStats(TypedDict):
    """Per-connection file transfer statistics."""

    total_files: int
    total_bytes: int
    last_updated: datetime


# Track file transfer statistics per connection
transfer_stats: dict[str, TransferStats] = {}


def set_debug_mode(enabled: bool = True) -> None:
    """Enable or disable debug mode globally."""
    global DEBUG_MODE
    DEBUG_MODE = enabled

    # Update existing loggers
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith("lazyssh"):
            logger = logging.getLogger(logger_name)
            for handler in logger.handlers:
                if isinstance(handler, rich.logging.RichHandler):
                    handler.setLevel(logging.DEBUG if enabled else logging.CRITICAL)


def ensure_log_directory(log_dir: Path | str | None = None) -> bool:
    """Ensure the log directory exists."""
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_dir = Path(log_dir)

    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_dir.chmod(0o700)  # Secure permissions
        except OSError as e:
            from .console_instance import display_error

            display_error(f"Error creating log directory: {e}")
            return False
    return True


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_dir: Path | str | None = None,
    log_to_file: bool = True,
) -> logging.Logger:
    """
    Set up a logger with the specified name and level.

    Args:
        name: Name of the logger
        level: Logging level (default: INFO)
        log_dir: Directory to store logs (default: DEFAULT_LOG_DIR)
        log_to_file: Whether to log to a file (default: True)

    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Don't propagate to parent loggers

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Add rich console handler (only shows output when debug mode is enabled)
    rich_handler = rich.logging.RichHandler(
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        show_time=True,
        markup=True,
        console=console,
    )

    # Set console handler level based on debug mode
    rich_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.CRITICAL)
    rich_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(rich_handler)

    # Add file handler if requested
    if log_to_file and ensure_log_directory(log_dir):
        log_dir = log_dir or DEFAULT_LOG_DIR
        log_file = Path(log_dir) / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

        try:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(logging.Formatter(FILE_LOG_FORMAT))
            file_handler.setLevel(level)  # File handler always uses the specified level
            logger.addHandler(file_handler)
        except OSError as e:
            logger.error(f"Failed to set up file logging: {e}")

    return logger


def get_logger(
    name: str, level: int | None = None, log_dir: Path | str | None = None
) -> logging.Logger:
    """
    Get a logger with the given name. If it doesn't exist, create it.

    Args:
        name: Name of the logger
        level: Logging level (default: None, will use INFO)
        log_dir: Directory to store logs (default: DEFAULT_LOG_DIR)

    Returns:
        Logger instance
    """
    # Get level from environment variable or use default
    env_level = os.environ.get("LAZYSSH_LOG_LEVEL", "INFO")
    level = level or LOG_LEVELS.get(env_level.upper(), logging.INFO)

    return setup_logger(name, level, log_dir)


def get_connection_logger(connection_name: str) -> logging.Logger:
    """Create or get a logger for a specific connection"""
    # Create connection-specific log directory
    log_dir = Path(CONNECTION_LOG_DIR_TEMPLATE.format(connection_name=connection_name))
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        # Ensure directory permissions are secure
        log_dir.chmod(0o700)

    # Create or get the logger
    logger_name = f"lazyssh.connection.{connection_name}"
    logger = logging.getLogger(logger_name)

    # If logger doesn't have handlers, set them up
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if DEBUG_MODE else get_log_level_from_env())
        logger.propagate = False

        # File handler for connection log
        conn_log_file = log_dir / "connection.log"
        file_handler = logging.FileHandler(conn_log_file)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler (only in debug mode)
        if DEBUG_MODE:
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                f"[{connection_name}] %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

    return logger


# Create core loggers
APP_LOGGER = get_logger("lazyssh")
SSH_LOGGER = get_logger("lazyssh.ssh")
CMD_LOGGER = get_logger("lazyssh.command")
SCP_LOGGER = get_logger("lazyssh.scp")


def log_ssh_connection(
    host: str,
    port: int,
    username: str,
    socket_path: str,
    dynamic_port: int | None = None,
    identity_file: str | None = None,
    shell: str | None = None,
    success: bool = True,
) -> None:
    """Log SSH connection details."""
    if not SSH_LOGGER:
        return

    if success:
        SSH_LOGGER.info(f"Connection established: {username}@{host}:{port}, socket: {socket_path}")
        if dynamic_port:
            SSH_LOGGER.info(f"Dynamic proxy created on port {dynamic_port}")
        if identity_file:
            SSH_LOGGER.debug(f"Using identity file: {identity_file}")
        if shell:
            SSH_LOGGER.debug(f"Using shell: {shell}")
    else:
        SSH_LOGGER.error(f"Connection failed: {username}@{host}:{port}")


def log_ssh_command(
    connection_name: str,
    command: str,
    success: bool = True,
    output: str | None = None,
    error: str | None = None,
) -> None:
    """Log SSH command execution"""
    if not SSH_LOGGER:
        return

    if success:
        SSH_LOGGER.info(f"Command executed on {connection_name}: {command}")
        if DEBUG_MODE and output:
            SSH_LOGGER.debug(f"Output: {output[:500]}{'...' if len(output) > 500 else ''}")
    else:
        SSH_LOGGER.error(f"Command failed on {connection_name}: {command}")
        if error:
            SSH_LOGGER.error(f"Error: {error}")


def log_scp_command(connection_name: str, command: str) -> None:
    """Log SCP command execution"""
    command_short = command[:100] + "..." if len(command) > 100 else command
    if SCP_LOGGER:
        SCP_LOGGER.info(f"SCP command executed on {connection_name}: {command_short}")

    # Also log to connection-specific log
    conn_logger = get_connection_logger(connection_name)
    if conn_logger:
        conn_logger.info(f"SCP command executed: {command}")


def log_file_transfer(
    connection_name: str, source: str, destination: str, size: int, operation: str
) -> None:
    """Log file transfer operations"""
    # Format the size for readability
    size_formatted = format_size(size)

    if SCP_LOGGER:
        if operation == "upload":
            SCP_LOGGER.info(
                f"File uploaded to {connection_name}: {source} -> {destination} ({size_formatted})"
            )
        else:  # download
            SCP_LOGGER.info(
                f"File downloaded from {connection_name}: {source} -> {destination} ({size_formatted})"
            )

    # Also log to connection-specific log
    conn_logger = get_connection_logger(connection_name)
    if conn_logger:
        if operation == "upload":
            conn_logger.info(f"File uploaded: {source} -> {destination} ({size_formatted})")
        else:  # download
            conn_logger.info(f"File downloaded: {source} -> {destination} ({size_formatted})")


def format_size(size_bytes: int) -> str:
    """Format a size in bytes to a human-readable string"""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    size_bytes_float = float(size_bytes)  # Convert to float to avoid type issues
    while size_bytes_float >= 1024 and i < len(size_name) - 1:
        size_bytes_float /= 1024
        i += 1
    return f"{size_bytes_float:.2f}{size_name[i]}"


def update_transfer_stats(connection_name: str, files_count: int, bytes_count: int) -> None:
    """Update and log file transfer statistics for a connection"""
    # Initialize stats for this connection if not exists
    if connection_name not in transfer_stats:
        transfer_stats[connection_name] = {
            "total_files": 0,
            "total_bytes": 0,
            "last_updated": datetime.now(),
        }

    # Update stats - if files_count is 1, it's a single file transfer (put/get)
    # In this case, we count it as 1 file total, not increment
    stats = transfer_stats[connection_name]
    if files_count == 1:
        # Single file transfer - reset counter
        stats["total_files"] = 1
    else:
        # Multiple file transfer (from mget) - additive
        stats["total_files"] += files_count

    stats["total_bytes"] += bytes_count
    stats["last_updated"] = datetime.now()

    # Log the updated stats
    total_bytes = stats["total_bytes"]
    if isinstance(total_bytes, int):
        bytes_formatted = format_size(total_bytes)
    else:
        bytes_formatted = "0B"  # Fallback if not an int  # pragma: no cover

    if SCP_LOGGER:
        SCP_LOGGER.info(
            f"Transfer stats for {connection_name}: {stats['total_files']} files, {bytes_formatted}"
        )

    # Log to connection-specific log
    conn_logger = get_connection_logger(connection_name)
    if conn_logger:
        conn_logger.info(f"Transfer stats: {stats['total_files']} files, {bytes_formatted}")


def log_tunnel_creation(
    socket_path: str,
    local_port: int,
    remote_host: str,
    remote_port: int,
    reverse: bool = False,
    success: bool = True,
) -> None:
    """Log tunnel creation details."""
    if not SSH_LOGGER:
        return

    tunnel_type = "reverse" if reverse else "forward"

    if success:
        SSH_LOGGER.info(
            f"Tunnel created: {socket_path} - {tunnel_type} "
            f"{local_port} -> {remote_host}:{remote_port}"
        )
    else:
        SSH_LOGGER.error(
            f"Tunnel creation failed: {socket_path} - {tunnel_type} "
            f"{local_port} -> {remote_host}:{remote_port}"
        )


def get_connection_log_path(connection_name: str) -> str:
    """Get the path to the connection log file"""
    return f"{CONNECTION_LOG_DIR_TEMPLATE.format(connection_name=connection_name)}/connection.log"


def get_log_level_from_env() -> int:
    """Get the log level from environment variable, defaulting to INFO"""
    env_level = os.environ.get("LAZYSSH_LOG_LEVEL", DEFAULT_LOG_LEVEL)
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(env_level.upper(), logging.INFO)
