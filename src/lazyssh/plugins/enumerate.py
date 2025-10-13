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
from typing import Any


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

    if not all([socket_path, host, user]):
        print("ERROR: Missing required environment variables", file=sys.stderr)
        sys.exit(1)

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
    print("  [*] Enumerating system information...")

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
    print("  [*] Enumerating users and groups...")

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
    print("  [*] Enumerating network configuration...")

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
    print("  [*] Enumerating processes and services...")

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
    print("  [*] Enumerating installed packages...")

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
    print("  [*] Enumerating filesystem...")

    data = {
        "mounts": safe_command("mount"),
        "disk_usage": safe_command("df -h"),
        "block_devices": safe_command("lsblk 2>/dev/null || echo 'Not available'"),
        "fstab": safe_command("cat /etc/fstab 2>/dev/null"),
        "home_directories": safe_command("ls -la /home 2>/dev/null || echo 'Permission denied'"),
        "tmp_files": safe_command("ls -la /tmp 2>/dev/null | head -20"),
        "suid_files": safe_command(
            "find / -perm -4000 -type f 2>/dev/null | head -50 || echo 'Not available'"
        ),
        "writable_dirs": safe_command(
            "find / -writable -type d 2>/dev/null | head -30 || echo 'Not available'"
        ),
    }

    return data


def enumerate_environment() -> dict[str, Any]:
    """Gather environment variables"""
    print("  [*] Enumerating environment variables...")

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
    print("  [*] Enumerating scheduled tasks...")

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
    print("  [*] Enumerating security configurations...")

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
    print("  [*] Enumerating system logs...")

    data = {
        "auth_log": safe_command(
            "tail -20 /var/log/auth.log 2>/dev/null || tail -20 /var/log/secure 2>/dev/null || echo 'Not available'"
        ),
        "syslog": safe_command(
            "tail -20 /var/log/syslog 2>/dev/null || tail -20 /var/log/messages 2>/dev/null || echo 'Not available'"
        ),
        "kern_log": safe_command(
            "tail -20 /var/log/kern.log 2>/dev/null || tail -20 /var/log/dmesg 2>/dev/null || echo 'Not available'"
        ),
        "failed_logins": safe_command("lastb -n 10 2>/dev/null || echo 'Not available'"),
        "journal": safe_command(
            "journalctl -n 20 --no-pager 2>/dev/null || echo 'Systemd journal not available'"
        ),
    }

    return data


def enumerate_hardware() -> dict[str, Any]:
    """Gather hardware information"""
    print("  [*] Enumerating hardware...")

    data = {
        "cpu": safe_command("lscpu 2>/dev/null || cat /proc/cpuinfo"),
        "memory": safe_command("free -h"),
        "meminfo": safe_command("cat /proc/meminfo | head -20"),
        "pci_devices": safe_command("lspci 2>/dev/null || echo 'Not available'"),
        "usb_devices": safe_command("lsusb 2>/dev/null || echo 'Not available'"),
        "dmi_info": safe_command("dmidecode -t system 2>/dev/null || echo 'Permission denied'"),
    }

    return data


def format_human_readable(data: EnumerationData) -> str:
    """Format enumeration data as human-readable report

    Args:
        data: EnumerationData object

    Returns:
        Formatted string report
    """
    output = []
    output.append("=" * 80)
    output.append(" " * 25 + "SYSTEM ENUMERATION REPORT")
    output.append("=" * 80)
    output.append("")

    # System Information
    output.append("─" * 80)
    output.append("SYSTEM INFORMATION")
    output.append("─" * 80)
    for key, value in data.system.items():
        output.append(f"\n[{key.upper()}]")
        output.append(str(value))

    # Users
    output.append("\n" + "─" * 80)
    output.append("USERS AND GROUPS")
    output.append("─" * 80)
    for key, value in data.users.items():
        output.append(f"\n[{key.upper()}]")
        output.append(str(value)[:500])  # Limit output

    # Network
    output.append("\n" + "─" * 80)
    output.append("NETWORK CONFIGURATION")
    output.append("─" * 80)
    for key, value in data.network.items():
        output.append(f"\n[{key.upper()}]")
        output.append(str(value)[:1000])  # Limit output

    # Processes
    output.append("\n" + "─" * 80)
    output.append("PROCESSES AND SERVICES")
    output.append("─" * 80)
    output.append(f"\n[PROCESS COUNT]: {len(data.processes['processes'].split(chr(10)))}")
    output.append("\n[RUNNING SERVICES]")
    output.append(str(data.processes["running_services"])[:1000])

    # Packages
    output.append("\n" + "─" * 80)
    output.append("INSTALLED PACKAGES")
    output.append("─" * 80)
    output.append(f"Package Manager: {data.packages['package_manager']}")
    output.append(f"Package Count: {data.packages['package_count']}")

    # Filesystem
    output.append("\n" + "─" * 80)
    output.append("FILESYSTEM")
    output.append("─" * 80)
    output.append("\n[DISK USAGE]")
    output.append(data.filesystem["disk_usage"])
    output.append("\n[MOUNTS]")
    output.append(str(data.filesystem["mounts"])[:1000])

    # Environment
    output.append("\n" + "─" * 80)
    output.append("ENVIRONMENT")
    output.append("─" * 80)
    output.append(f"PATH: {data.environment['path']}")
    output.append(f"SHELL: {data.environment['shell']}")
    output.append(f"HOME: {data.environment['home']}")
    output.append(f"PWD: {data.environment['pwd']}")

    # Scheduled Tasks
    output.append("\n" + "─" * 80)
    output.append("SCHEDULED TASKS")
    output.append("─" * 80)
    for key, value in data.scheduled.items():
        if value != "N/A" and value != "Not available" and value != "No crontab":
            output.append(f"\n[{key.upper()}]")
            output.append(str(value)[:500])

    # Security
    output.append("\n" + "─" * 80)
    output.append("SECURITY CONFIGURATION")
    output.append("─" * 80)
    for key, value in data.security.items():
        if (
            value != "N/A"
            and "not installed" not in value.lower()
            and "permission denied" not in value.lower()
        ):
            output.append(f"\n[{key.upper()}]")
            output.append(str(value)[:500])

    # Hardware
    output.append("\n" + "─" * 80)
    output.append("HARDWARE INFORMATION")
    output.append("─" * 80)
    output.append("\n[MEMORY]")
    output.append(data.hardware["memory"])
    output.append("\n[CPU]")
    output.append(str(data.hardware["cpu"])[:500])

    output.append("\n" + "=" * 80)
    output.append("END OF REPORT")
    output.append("=" * 80)

    return "\n".join(output)


def main():
    """Main plugin logic"""
    # Get connection info
    socket_name = os.environ.get("LAZYSSH_SOCKET", "unknown")
    host = os.environ.get("LAZYSSH_HOST", "unknown")
    user = os.environ.get("LAZYSSH_USER", "unknown")

    print()
    print("=" * 80)
    print("  LazySSH Enumeration Plugin v1.0.0")
    print(f"  Target: {user}@{host} (socket: {socket_name})")
    print("=" * 80)
    print()
    print("Starting comprehensive system enumeration...")
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

    print()
    print("  [✓] Enumeration complete!")
    print()
    print("=" * 80)
    print()

    # Check if JSON output requested
    if "--json" in sys.argv:
        # Convert dataclass to dict
        import dataclasses

        data_dict = dataclasses.asdict(data)
        print(json.dumps(data_dict, indent=2))
    else:
        # Human-readable output
        print(format_human_readable(data))

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
