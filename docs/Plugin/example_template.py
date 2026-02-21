#!/usr/bin/env python3
# PLUGIN_NAME: example-template
# PLUGIN_DESCRIPTION: Template for creating custom LazySSH plugins
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

"""
Example Plugin Template for LazySSH

This template demonstrates how to create a custom plugin for LazySSH.
Copy this file, rename it, and modify the logic to suit your needs.

Environment Variables Available:
    LAZYSSH_SOCKET         - Control socket name
    LAZYSSH_HOST          - Remote host address
    LAZYSSH_PORT          - SSH port
    LAZYSSH_USER          - SSH username
    LAZYSSH_SOCKET_PATH   - Full path to control socket file
    LAZYSSH_SSH_KEY       - SSH key path (if key-based auth)
    LAZYSSH_SHELL         - Preferred shell (if configured)
    LAZYSSH_PLUGIN_API_VERSION - Plugin API version

Usage:
    1. Copy this file to create your own plugin
    2. Update the PLUGIN_* metadata at the top
    3. Modify the main() function with your logic
    4. Make the file executable: chmod +x your_plugin.py
    5. Run from LazySSH: plugin run your-plugin <socket-name>
"""

import os
import subprocess
import sys


def run_remote_command(command: str) -> tuple[int, str, str]:
    """Execute a command on the remote host via SSH

    Args:
        command: Shell command to execute

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")

    if not all([socket_path, host, user]):
        print("ERROR: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Use SSH with control socket for multiplexing
    ssh_cmd = [
        "ssh",
        "-S",
        socket_path,
        "-o",
        "ControlMaster=no",
        f"{user}@{host}",
        command,
    ]

    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", f"Error executing command: {e}"


def print_section(title: str, content: str = "") -> None:
    """Print a formatted section header

    Args:
        title: Section title
        content: Optional content to display
    """
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    if content:
        print(content)


def main():
    """Main plugin logic - modify this function"""

    # Get connection information from environment
    socket_name = os.environ.get("LAZYSSH_SOCKET", "unknown")
    host = os.environ.get("LAZYSSH_HOST", "unknown")
    user = os.environ.get("LAZYSSH_USER", "unknown")
    port = os.environ.get("LAZYSSH_PORT", "22")

    print_section("Example Plugin Template")
    print(f"Connected to: {user}@{host}:{port}")
    print(f"Socket: {socket_name}")

    # Example: Run a simple command
    print_section("Remote System Information")
    exit_code, stdout, stderr = run_remote_command("uname -a")

    if exit_code == 0:
        print(stdout.strip())
    else:
        print(f"ERROR: {stderr}", file=sys.stderr)
        return 1

    # Example: Get hostname
    exit_code, stdout, stderr = run_remote_command("hostname")
    if exit_code == 0:
        print(f"\nHostname: {stdout.strip()}")

    # Example: Check uptime
    exit_code, stdout, stderr = run_remote_command("uptime")
    if exit_code == 0:
        print(f"Uptime: {stdout.strip()}")

    print_section("Plugin Execution Complete")
    print("Modify this template to create your own custom plugins!")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nPlugin interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
