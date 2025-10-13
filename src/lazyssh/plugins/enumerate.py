#!/usr/bin/env python3
# PLUGIN_NAME: enumerate
# PLUGIN_DESCRIPTION: Comprehensive system enumeration and reconnaissance
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

"""
System Enumeration Plugin for LazySSH

Performs comprehensive system reconnaissance including:
- Operating system and kernel information
- User accounts and groups
- Network configuration
- Running processes and services
- Installed packages
- Filesystem and mounts
- Environment variables
- Scheduled tasks (cron, systemd timers)
- Security configurations
- System logs
- Hardware information

Output is formatted as human-readable report or JSON.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Simple ANSI color codes - Dracula theme
COLORS = {
    "cyan": "\033[96m",  # Cyan
    "green": "\033[92m",  # Green
    "yellow": "\033[93m",  # Yellow
    "purple": "\033[95m",  # Purple/Magenta
    "reset": "\033[0m",  # Reset
    "bold": "\033[1m",  # Bold
    "dim": "\033[2m",  # Dim
}


def color(text: str, color_name: str, bold: bool = False) -> str:
    """Apply color to text using ANSI codes

    Args:
        text: Text to color
        color_name: Name of color from COLORS dict
        bold: Whether to make text bold

    Returns:
        Colored text string
    """
    c = COLORS.get(color_name, "")
    b = COLORS["bold"] if bold else ""
    return f"{b}{c}{text}{COLORS['reset']}"


def print_status(message: str) -> None:
    """Print a status message

    Args:
        message: Status message to print
    """
    print(f"  {color('[*]', 'cyan')} {message}")


def print_section_header(title: str) -> None:
    """Print a section header

    Args:
        title: Section title
    """
    print()
    # Minimal header to avoid conflicts with enclosing UI frames
    print(color(f"› {title}", "purple", bold=True))


def print_subsection(title: str, content: str = "") -> None:
    """Print a subsection - simple and clean

    Args:
        title: Subsection title
        content: Content to display
    """
    print()
    print(color(f"{title}:", "yellow", bold=True))
    if content and content.strip():
        print(content)
    else:
        print(color("N/A", "dim"))
        print()
        print(f"[{title}]")
        if content:
            print(content)


@dataclass
class EnumerationData:
    """Container for all enumeration results"""

    system: dict[str, Any]
    users: dict[str, Any]
    network: dict[str, Any]
    processes: dict[str, Any]
    packages: dict[str, Any]
    filesystem: dict[str, Any]
    environment: dict[str, Any]
    scheduled: dict[str, Any]
    security: dict[str, Any]
    logs: dict[str, Any]
    hardware: dict[str, Any]


def run_remote_command(command: str, timeout: int = 30) -> tuple[int, str, str]:
    """Execute a command on the remote host via SSH

    Args:
        command: Shell command to execute
        timeout: Command timeout in seconds

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")

    if socket_path is None or host is None or user is None:
        print("ERROR: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # At this point, mypy knows these are str (not Optional)
    ssh_cmd: list[str] = [
        "ssh",
        "-S",
        socket_path,
        "-o",
        "ControlMaster=no",
        f"{user}@{host}",
        command,
    ]

    try:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", f"Error: {e}"


def safe_command(command: str, default: str = "N/A") -> str:
    """Run command and return output or default on failure

    Args:
        command: Shell command to execute
        default: Default value if command fails

    Returns:
        Command output or default value
    """
    exit_code, stdout, stderr = run_remote_command(command)
    if exit_code == 0 and stdout.strip():
        return stdout.strip()
    return default


def enumerate_system() -> dict[str, Any]:
    """Gather system information"""
    print_status("Enumerating system information...")

    data = {
        "os": safe_command("cat /etc/os-release 2>/dev/null || uname -a"),
        "kernel": safe_command("uname -r"),
        "hostname": safe_command("hostname"),
        "uptime": safe_command("uptime"),
        "date": safe_command("date"),
        "timezone": safe_command("timedatectl 2>/dev/null || date +%Z"),
        "architecture": safe_command("uname -m"),
        "cpu_info": safe_command(
            "lscpu 2>/dev/null || cat /proc/cpuinfo | grep 'model name' | head -1"
        ),
    }

    return data


def enumerate_users() -> dict[str, Any]:
    """Gather user and group information"""
    print_status("Enumerating users and groups...")

    data = {
        "current_user": safe_command("whoami"),
        "user_id": safe_command("id"),
        "users": safe_command("cat /etc/passwd | cut -d: -f1"),
        "groups": safe_command("cat /etc/group | cut -d: -f1"),
        "sudoers": safe_command("cat /etc/sudoers 2>/dev/null || echo 'Permission denied'"),
        "logged_in_users": safe_command("who"),
        "last_logins": safe_command("last -n 10 2>/dev/null || echo 'Not available'"),
    }

    return data


def enumerate_network() -> dict[str, Any]:
    """Gather network configuration"""
    print_status("Enumerating network configuration...")

    data = {
        "interfaces": safe_command("ip addr 2>/dev/null || ifconfig"),
        "routing_table": safe_command("ip route 2>/dev/null || route -n"),
        "listening_ports": safe_command(
            "ss -tulnp 2>/dev/null || netstat -tulnp 2>/dev/null || echo 'Not available'"
        ),
        "active_connections": safe_command(
            "ss -tunap 2>/dev/null || netstat -tunap 2>/dev/null || echo 'Not available'"
        ),
        "dns": safe_command("cat /etc/resolv.conf 2>/dev/null"),
        "hosts": safe_command("cat /etc/hosts 2>/dev/null"),
        "arp_table": safe_command("ip neigh 2>/dev/null || arp -an"),
        "firewall_rules": safe_command("iptables -L -n 2>/dev/null || echo 'Permission denied'"),
    }

    return data


def enumerate_processes() -> dict[str, Any]:
    """Gather process and service information"""
    print_status("Enumerating processes and services...")

    data = {
        "processes": safe_command("ps auxf 2>/dev/null || ps aux"),
        "systemd_services": safe_command(
            "systemctl list-units --type=service --all 2>/dev/null || echo 'Systemd not available'"
        ),
        "running_services": safe_command(
            "systemctl list-units --type=service --state=running 2>/dev/null || service --status-all 2>/dev/null || echo 'Not available'"
        ),
        "enabled_services": safe_command(
            "systemctl list-unit-files --type=service --state=enabled 2>/dev/null || echo 'Not available'"
        ),
    }

    return data


def enumerate_packages() -> dict[str, Any]:
    """Gather installed package information"""
    print_status("Enumerating installed packages...")

    # Detect package manager
    pkg_mgr = "unknown"
    packages = "N/A"

    # Try different package managers
    if safe_command("which dpkg") != "N/A":
        pkg_mgr = "dpkg"
        packages = safe_command("dpkg -l")
    elif safe_command("which rpm") != "N/A":
        pkg_mgr = "rpm"
        packages = safe_command("rpm -qa")
    elif safe_command("which pacman") != "N/A":
        pkg_mgr = "pacman"
        packages = safe_command("pacman -Q")
    elif safe_command("which apk") != "N/A":
        pkg_mgr = "apk"
        packages = safe_command("apk list --installed")

    data = {
        "package_manager": pkg_mgr,
        "installed_packages": packages,
        "package_count": len(packages.split("\n")) if packages != "N/A" else 0,
    }

    return data


def enumerate_filesystem() -> dict[str, Any]:
    """Gather filesystem information"""
    print_status("Enumerating filesystem...")

    data = {
        "mounts": safe_command("mount"),
        "disk_usage": safe_command("df -h"),
        "block_devices": safe_command("lsblk 2>/dev/null || echo 'Not available'"),
        "fstab": safe_command("cat /etc/fstab 2>/dev/null"),
        "home_directories": safe_command("ls -la /home 2>/dev/null || echo 'Permission denied'"),
        "tmp_files": safe_command("ls -la /tmp 2>/dev/null"),
        "suid_files": safe_command(
            "find / -perm -4000 -type f 2>/dev/null || echo 'Not available'"
        ),
        "writable_dirs": safe_command(
            "find / -writable -type d 2>/dev/null || echo 'Not available'"
        ),
    }

    return data


def enumerate_environment() -> dict[str, Any]:
    """Gather environment variables"""
    print_status("Enumerating environment variables...")

    data = {
        "env_vars": safe_command("env"),
        "path": safe_command("echo $PATH"),
        "shell": safe_command("echo $SHELL"),
        "home": safe_command("echo $HOME"),
        "pwd": safe_command("pwd"),
    }

    return data


def enumerate_scheduled() -> dict[str, Any]:
    """Gather scheduled tasks information"""
    print_status("Enumerating scheduled tasks...")

    data = {
        "user_crontab": safe_command("crontab -l 2>/dev/null || echo 'No crontab'"),
        "system_cron": safe_command("cat /etc/crontab 2>/dev/null"),
        "cron_d": safe_command("ls -la /etc/cron.d/ 2>/dev/null || echo 'Not available'"),
        "cron_daily": safe_command("ls -la /etc/cron.daily/ 2>/dev/null || echo 'Not available'"),
        "systemd_timers": safe_command(
            "systemctl list-timers --all 2>/dev/null || echo 'Not available'"
        ),
        "at_jobs": safe_command("atq 2>/dev/null || echo 'Not available'"),
    }

    return data


def enumerate_security() -> dict[str, Any]:
    """Gather security configuration"""
    print_status("Enumerating security configurations...")

    data = {
        "selinux": safe_command(
            "sestatus 2>/dev/null || getenforce 2>/dev/null || echo 'SELinux not installed'"
        ),
        "apparmor": safe_command("aa-status 2>/dev/null || echo 'AppArmor not installed'"),
        "firewall": safe_command(
            "ufw status 2>/dev/null || firewall-cmd --state 2>/dev/null || echo 'No firewall detected'"
        ),
        "iptables": safe_command("iptables -L -n 2>/dev/null || echo 'Permission denied'"),
        "fail2ban": safe_command(
            "fail2ban-client status 2>/dev/null || echo 'Fail2ban not installed'"
        ),
        "ssh_config": safe_command(
            "cat /etc/ssh/sshd_config 2>/dev/null || echo 'Permission denied'"
        ),
        "ssh_keys": safe_command("ls -la ~/.ssh/ 2>/dev/null || echo 'No SSH directory'"),
    }

    return data


def enumerate_logs() -> dict[str, Any]:
    """Gather system logs summary"""
    print_status("Enumerating system logs...")

    data = {
        "auth_log": safe_command(
            "cat /var/log/auth.log 2>/dev/null || cat /var/log/secure 2>/dev/null || echo 'Not available'"
        ),
        "syslog": safe_command(
            "cat /var/log/syslog 2>/dev/null || cat /var/log/messages 2>/dev/null || echo 'Not available'"
        ),
        "kern_log": safe_command(
            "cat /var/log/kern.log 2>/dev/null || cat /var/log/dmesg 2>/dev/null || echo 'Not available'"
        ),
        "failed_logins": safe_command("lastb -n 10 2>/dev/null || echo 'Not available'"),
        "journal": safe_command(
            "journalctl -n 20 --no-pager 2>/dev/null || echo 'Systemd journal not available'"
        ),
    }

    return data


def enumerate_hardware() -> dict[str, Any]:
    """Gather hardware information"""
    print_status("Enumerating hardware...")

    data = {
        "cpu": safe_command("lscpu 2>/dev/null || cat /proc/cpuinfo"),
        "memory": safe_command("free -h"),
        "meminfo": safe_command("cat /proc/meminfo"),
        "pci_devices": safe_command("lspci 2>/dev/null || echo 'Not available'"),
        "usb_devices": safe_command("lsusb 2>/dev/null || echo 'Not available'"),
        "dmi_info": safe_command("dmidecode -t system 2>/dev/null || echo 'Permission denied'"),
    }

    return data


def format_human_readable(data: EnumerationData) -> None:
    """Format and print enumeration data as human-readable report

    Args:
        data: EnumerationData object
    """
    # Header - Simple colored text
    print()
    print(color("SYSTEM ENUMERATION REPORT", "purple", bold=True))

    # System Information
    print_section_header("SYSTEM INFORMATION")
    for key, value in data.system.items():
        print_subsection(key.upper(), str(value))

    # Users
    print_section_header("USERS AND GROUPS")
    for key, value in data.users.items():
        print_subsection(key.upper(), str(value))

    # Network
    print_section_header("NETWORK CONFIGURATION")
    for key, value in data.network.items():
        print_subsection(key.upper(), str(value))

    # Processes
    print_section_header("PROCESSES AND SERVICES")
    process_count = len(data.processes["processes"].split("\n"))
    print()
    print(f"{color('Process Count:', 'cyan')} {color(str(process_count), 'green')}")
    # Full process list
    print_subsection("PROCESSES", data.processes["processes"])
    print_subsection("RUNNING SERVICES", str(data.processes["running_services"]))

    # Packages
    print_section_header("INSTALLED PACKAGES")
    print()
    print(f"{color('Package Manager:', 'cyan')} {color(data.packages['package_manager'], 'green')}")
    print(
        f"{color('Package Count:', 'cyan')} {color(str(data.packages['package_count']), 'green')}"
    )

    # Filesystem
    print_section_header("FILESYSTEM")
    print_subsection("DISK USAGE", data.filesystem["disk_usage"])
    print_subsection("MOUNTS", str(data.filesystem["mounts"]))

    # Environment
    print_section_header("ENVIRONMENT")
    print()
    print(f"{color('PATH:', 'cyan')} {data.environment['path']}")
    print(f"{color('SHELL:', 'cyan')} {data.environment['shell']}")
    print(f"{color('HOME:', 'cyan')} {data.environment['home']}")
    print(f"{color('PWD:', 'cyan')} {data.environment['pwd']}")

    # Scheduled Tasks
    print_section_header("SCHEDULED TASKS")
    has_scheduled = False
    for key, value in data.scheduled.items():
        if value != "N/A" and value != "Not available" and value != "No crontab":
            print_subsection(key.upper(), str(value))
            has_scheduled = True
    if not has_scheduled:
        print(f"\n{color('No scheduled tasks found', 'dim')}")

    # Security
    print_section_header("SECURITY CONFIGURATION")
    has_security = False
    for key, value in data.security.items():
        if (
            value != "N/A"
            and "not installed" not in value.lower()
            and "permission denied" not in value.lower()
        ):
            print_subsection(key.upper(), str(value))
            has_security = True
    if not has_security:
        print(f"\n{color('No security configurations accessible', 'dim')}")

    # Hardware
    print_section_header("HARDWARE INFORMATION")
    print_subsection("MEMORY", data.hardware["memory"])
    print_subsection("CPU", str(data.hardware["cpu"]))

    # Footer
    print()
    print(color("END OF REPORT", "purple", bold=True))
    print()


def _format_plain_text(data: EnumerationData) -> None:
    """Fallback plain text formatter - same as colored version

    Args:
        data: EnumerationData object
    """
    print("\n" + "=" * 80)
    print(" " * 25 + "SYSTEM ENUMERATION REPORT")
    print("=" * 80)

    print("\n" + "─" * 80)
    print("  SYSTEM INFORMATION")
    print("─" * 80)
    for key, value in data.system.items():
        print(f"\n[{key.upper()}]")
        print(str(value))

    print("\n" + "─" * 80)
    print("  USERS AND GROUPS")
    print("─" * 80)
    for key, value in data.users.items():
        print(f"\n[{key.upper()}]")
        print(str(value))

    print("\n" + "─" * 80)
    print("  NETWORK CONFIGURATION")
    print("─" * 80)
    for key, value in data.network.items():
        print(f"\n[{key.upper()}]")
        print(str(value))

    print("\n" + "─" * 80)
    print("  END OF REPORT")
    print("=" * 80 + "\n")


def main() -> int:
    """Main plugin logic"""
    # Lazy import to avoid heavy imports if not needed
    try:
        from lazyssh.logging_module import CONNECTION_LOG_DIR_TEMPLATE
    except Exception:
        CONNECTION_LOG_DIR_TEMPLATE = "/tmp/lazyssh/{connection_name}.d/logs"
    # Get connection info
    socket_name = os.environ.get("LAZYSSH_SOCKET", "unknown")
    host = os.environ.get("LAZYSSH_HOST", "unknown")
    user = os.environ.get("LAZYSSH_USER", "unknown")

    # Display header - simple ANSI colors
    print()
    print(color("LazySSH Enumeration Plugin v1.0.0", "cyan", bold=True))
    print(
        f"{color('Target:', 'green')} {color(f'{user}@{host}', 'yellow')} {color(f'(socket: {socket_name})', 'dim')}"
    )
    print()
    print(color("Starting comprehensive system enumeration...", "cyan"))
    print()

    # Gather all data
    data = EnumerationData(
        system=enumerate_system(),
        users=enumerate_users(),
        network=enumerate_network(),
        processes=enumerate_processes(),
        packages=enumerate_packages(),
        filesystem=enumerate_filesystem(),
        environment=enumerate_environment(),
        scheduled=enumerate_scheduled(),
        security=enumerate_security(),
        logs=enumerate_logs(),
        hardware=enumerate_hardware(),
    )

    # Display completion message
    print()
    print(f"{color('✓', 'green')} {color('Enumeration complete!', 'cyan')}")
    print()

    # Determine output mode and render content
    is_json = "--json" in sys.argv
    if is_json:
        import dataclasses

        data_dict = dataclasses.asdict(data)
        rendered_output = json.dumps(data_dict, indent=2)
        print(rendered_output)
    else:
        # Generate a plain-text report for saving (non-colored)
        lines: list[str] = []

        lines.append("")
        lines.append("SYSTEM ENUMERATION REPORT")

        def add_section(header: str, mapping: dict[str, Any]) -> None:
            lines.append("")
            lines.append(f"[{header}]")
            for key, value in mapping.items():
                lines.append("")
                lines.append(f"[{key.upper()}]")
                lines.append(str(value))

        add_section("SYSTEM INFORMATION", data.system)
        add_section("USERS AND GROUPS", data.users)
        add_section("NETWORK CONFIGURATION", data.network)
        add_section("PROCESSES AND SERVICES", data.processes)
        add_section("INSTALLED PACKAGES", data.packages)
        add_section("FILESYSTEM", data.filesystem)
        add_section("ENVIRONMENT", data.environment)
        add_section("SCHEDULED TASKS", data.scheduled)
        add_section("SECURITY CONFIGURATION", data.security)
        add_section("HARDWARE INFORMATION", data.hardware)

        lines.append("")
        lines.append("END OF REPORT")

        rendered_output = "\n".join(lines)

        # Human-readable display with colors in terminal
        format_human_readable(data)

    # Persist survey to standard logging location with timestamp
    # Derive connection name
    connection_name = os.environ.get("LAZYSSH_CONNECTION_NAME") or os.environ.get(
        "LAZYSSH_SOCKET", "unknown"
    )
    # If a path was provided, use the basename as a reasonable connection name
    if "/" in connection_name:
        connection_name = Path(connection_name).name

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = "json" if is_json else "txt"
    log_dir = Path(CONNECTION_LOG_DIR_TEMPLATE.format(connection_name=connection_name))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Best-effort fallback to default logs dir
        log_dir = Path("/tmp/lazyssh/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

    output_file = log_dir / f"survey_{timestamp}.{ext}"
    try:
        output_file.write_text(rendered_output + "\n", encoding="utf-8")
        print(
            color(
                f"Saved survey to {str(output_file)}",
                "green",
            )
        )
    except Exception as e:
        print(color(f"Failed to save survey: {e}", "yellow"))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nEnumeration interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
