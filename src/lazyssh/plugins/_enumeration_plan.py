"""Enumeration plan definitions for the LazySSH optimize enumeration change.

This module inventories all remote probes executed by the optimized enumerate
plugin and documents the priority finding heuristics that summarize the
results. Separating the static probe catalogue from the runtime logic allows
the main plugin implementation to stay focused on transport, parsing, and
rendering concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RemoteProbe:
    """Describes a single remote command collected by the batch script."""

    category: str
    key: str
    command: str
    timeout: int = 8


REMOTE_PROBES: tuple[RemoteProbe, ...] = (
    # System profile
    RemoteProbe("system", "os_release", "cat /etc/os-release 2>/dev/null || uname -a", timeout=4),
    RemoteProbe("system", "kernel", "uname -r", timeout=4),
    RemoteProbe("system", "hostname", "hostname", timeout=3),
    RemoteProbe("system", "uptime", "uptime -p 2>/dev/null || uptime", timeout=4),
    RemoteProbe("system", "current_time", "date --iso-8601=seconds 2>/dev/null || date", timeout=3),
    RemoteProbe("system", "timezone", "timedatectl status 2>/dev/null || date +%Z", timeout=4),
    RemoteProbe("system", "architecture", "uname -m", timeout=3),
    RemoteProbe(
        "system",
        "cpu_model",
        "lscpu 2>/dev/null || cat /proc/cpuinfo 2>/dev/null || echo 'Unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "system",
        "load_avg",
        "cat /proc/loadavg 2>/dev/null || uptime | awk '{print $8,$9,$10}'",
        timeout=3,
    ),
    # Users and privilege footprint
    RemoteProbe("users", "current_user", "whoami", timeout=3),
    RemoteProbe("users", "id", "id", timeout=3),
    RemoteProbe("users", "passwd", "getent passwd 2>/dev/null || cat /etc/passwd", timeout=5),
    RemoteProbe("users", "group", "getent group 2>/dev/null || cat /etc/group", timeout=5),
    RemoteProbe("users", "sudoers", "cat /etc/sudoers 2>/dev/null", timeout=4),
    RemoteProbe("users", "sudoers_d", "ls -1 /etc/sudoers.d 2>/dev/null", timeout=4),
    RemoteProbe("users", "sudo_check", "sudo -ln 2>/dev/null || sudo -l 2>/dev/null", timeout=6),
    RemoteProbe("users", "logged_in", "who 2>/dev/null || echo 'No active sessions'", timeout=3),
    RemoteProbe("users", "last_logins", "last -n 10 2>/dev/null", timeout=5),
    # Network exposure
    RemoteProbe(
        "network",
        "interfaces",
        "ip -o addr 2>/dev/null || ifconfig -a 2>/dev/null || ip addr",
        timeout=6,
    ),
    RemoteProbe(
        "network",
        "routing_table",
        "ip route 2>/dev/null || route -n 2>/dev/null || echo 'Unavailable'",
        timeout=4,
    ),
    RemoteProbe(
        "network",
        "listening_services",
        "ss -tulnp 2>/dev/null || netstat -tulnp 2>/dev/null || echo 'Unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "network",
        "active_connections",
        "ss -tunap 2>/dev/null || netstat -tunap 2>/dev/null || echo 'Unavailable'",
        timeout=6,
    ),
    RemoteProbe("network", "dns", "cat /etc/resolv.conf 2>/dev/null", timeout=3),
    RemoteProbe("network", "hosts_file", "cat /etc/hosts 2>/dev/null", timeout=3),
    RemoteProbe(
        "network",
        "firewall_rules",
        "iptables -L -n 2>/dev/null || nft list ruleset 2>/dev/null || echo 'Unavailable'",
        timeout=6,
    ),
    # Processes and services
    RemoteProbe(
        "processes",
        "top_processes",
        "ps axo user,pid,ppid,%cpu,%mem,start,time,cmd --sort=-%cpu | head -n 50",
        timeout=5,
    ),
    RemoteProbe(
        "processes",
        "systemd_services",
        "systemctl list-units --type=service --all 2>/dev/null || echo 'systemd not present'",
        timeout=6,
    ),
    RemoteProbe(
        "processes",
        "systemd_running",
        "systemctl list-units --type=service --state=running 2>/dev/null || service --status-all 2>/dev/null || echo 'Unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "processes",
        "systemd_failed",
        "systemctl --failed 2>/dev/null || echo 'Unavailable'",
        timeout=5,
    ),
    RemoteProbe(
        "processes",
        "timers",
        "systemctl list-timers --all 2>/dev/null || echo 'Unavailable'",
        timeout=5,
    ),
    # Package landscape
    RemoteProbe(
        "packages",
        "package_manager",
        "if command -v dpkg-query >/dev/null 2>&1; then echo dpkg; "
        "elif command -v rpm >/dev/null 2>&1; then echo rpm; "
        "elif command -v pacman >/dev/null 2>&1; then echo pacman; "
        "elif command -v apk >/dev/null 2>&1; then echo apk; "
        "elif command -v zypper >/dev/null 2>&1; then echo zypper; "
        "else echo unknown; fi",
        timeout=3,
    ),
    RemoteProbe(
        "packages",
        "package_inventory",
        "if command -v dpkg-query >/dev/null 2>&1; then dpkg-query -W -f '${binary:Package}\\t${Version}\\n' | head -n 200; "
        "elif command -v rpm >/dev/null 2>&1; then rpm -qa | head -n 200; "
        "elif command -v pacman >/dev/null 2>&1; then pacman -Q | head -n 200; "
        "elif command -v apk >/dev/null 2>&1; then apk list --installed | head -n 200; "
        "elif command -v zypper >/dev/null 2>&1; then zypper packages -i | head -n 200; "
        "else echo 'Package inventory unavailable'; fi",
        timeout=12,
    ),
    RemoteProbe(
        "packages",
        "package_counts",
        "if command -v dpkg-query >/dev/null 2>&1; then dpkg-query -W -f '${binary:Package}\\n' | wc -l; "
        "elif command -v rpm >/dev/null 2>&1; then rpm -qa | wc -l; "
        "elif command -v pacman >/dev/null 2>&1; then pacman -Q | wc -l; "
        "elif command -v apk >/dev/null 2>&1; then apk list --installed | wc -l; "
        "elif command -v zypper >/dev/null 2>&1; then zypper packages -i | tail -n +5 | wc -l; "
        "else echo 0; fi",
        timeout=6,
    ),
    # Filesystem and permissions
    RemoteProbe(
        "filesystem",
        "disk_usage",
        "df -h --output=source,fstype,size,used,avail,pcent,target",
        timeout=4,
    ),
    RemoteProbe("filesystem", "mounts", "mount", timeout=4),
    RemoteProbe("filesystem", "fstab", "cat /etc/fstab 2>/dev/null", timeout=4),
    RemoteProbe("filesystem", "home_listing", "ls -ld /home/* 2>/dev/null", timeout=4),
    RemoteProbe(
        "filesystem",
        "tmp_listing",
        "ls -ld /tmp /var/tmp /dev/shm 2>/dev/null",
        timeout=4,
    ),
    RemoteProbe(
        "filesystem",
        "suid_files",
        "if command -v timeout >/dev/null 2>&1; then timeout 8s find / -xdev -perm -4000 -type f 2>/dev/null; "
        "else find / -xdev -perm -4000 -type f 2>/dev/null; fi",
        timeout=10,
    ),
    RemoteProbe(
        "filesystem",
        "sgid_files",
        "if command -v timeout >/dev/null 2>&1; then timeout 8s find / -xdev -perm -2000 -type f 2>/dev/null; "
        "else find / -xdev -perm -2000 -type f 2>/dev/null; fi",
        timeout=10,
    ),
    RemoteProbe(
        "filesystem",
        "world_writable_dirs",
        "if command -v timeout >/dev/null 2>&1; then timeout 8s find / -xdev -type d -perm -0002 ! -path '/tmp' ! -path '/var/tmp' ! -path '/dev/shm' 2>/dev/null; "
        "else find / -xdev -type d -perm -0002 ! -path '/tmp' ! -path '/var/tmp' ! -path '/dev/shm' 2>/dev/null; fi",
        timeout=10,
    ),
    # Environment
    RemoteProbe("environment", "env_vars", "env", timeout=4),
    RemoteProbe("environment", "path", "printf '%s\\n' \"$PATH\"", timeout=2),
    RemoteProbe("environment", "shell", 'echo "$SHELL"', timeout=2),
    RemoteProbe("environment", "umask", "umask", timeout=2),
    RemoteProbe("environment", "limits", "ulimit -a", timeout=3),
    # Scheduled tasks
    RemoteProbe("scheduled", "cron_user", "crontab -l 2>/dev/null", timeout=4),
    RemoteProbe("scheduled", "cron_system", "cat /etc/crontab 2>/dev/null", timeout=4),
    RemoteProbe("scheduled", "cron_d", "ls -1 /etc/cron.d 2>/dev/null", timeout=3),
    RemoteProbe("scheduled", "cron_daily", "ls -1 /etc/cron.daily 2>/dev/null", timeout=3),
    RemoteProbe("scheduled", "at_jobs", "atq 2>/dev/null", timeout=3),
    RemoteProbe(
        "scheduled",
        "systemd_timers",
        "systemctl list-timers --all 2>/dev/null || echo 'Unavailable'",
        timeout=5,
    ),
    # Security configuration
    RemoteProbe(
        "security",
        "selinux",
        "sestatus 2>/dev/null || getenforce 2>/dev/null || echo 'SELinux not installed'",
        timeout=3,
    ),
    RemoteProbe(
        "security",
        "apparmor",
        "aa-status 2>/dev/null || apparmor_status 2>/dev/null || echo 'AppArmor not installed'",
        timeout=3,
    ),
    RemoteProbe(
        "security",
        "ssh_config",
        "cat /etc/ssh/sshd_config 2>/dev/null || echo 'SSH config not accessible'",
        timeout=4,
    ),
    RemoteProbe(
        "security",
        "ssh_effective_config",
        "sshd -T 2>/dev/null || echo 'sshd -T unavailable'",
        timeout=4,
    ),
    RemoteProbe(
        "security",
        "fail2ban",
        "fail2ban-client status 2>/dev/null || echo 'Fail2ban not installed'",
        timeout=4,
    ),
    RemoteProbe(
        "security",
        "firewall_cmd",
        "ufw status 2>/dev/null || firewall-cmd --state 2>/dev/null || echo 'Firewall status unavailable'",
        timeout=4,
    ),
    # Logs
    RemoteProbe(
        "logs",
        "auth_recent",
        "journalctl -n 200 -u ssh --no-pager 2>/dev/null || "
        "tail -n 200 /var/log/auth.log 2>/dev/null || "
        "tail -n 200 /var/log/secure 2>/dev/null || echo 'Authentication logs unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "logs",
        "syslog_recent",
        "journalctl -n 200 --no-pager 2>/dev/null || tail -n 200 /var/log/syslog 2>/dev/null || "
        "tail -n 200 /var/log/messages 2>/dev/null || echo 'System logs unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "logs",
        "failed_logins",
        "lastb -n 20 2>/dev/null || echo 'No failed login data'",
        timeout=5,
    ),
    # Hardware snapshot
    RemoteProbe("hardware", "cpu", "lscpu 2>/dev/null || cat /proc/cpuinfo 2>/dev/null", timeout=6),
    RemoteProbe("hardware", "memory", "free -h", timeout=3),
    RemoteProbe(
        "hardware", "block_devices", "lsblk -f 2>/dev/null || echo 'lsblk unavailable'", timeout=4
    ),
    RemoteProbe(
        "hardware", "pci_devices", "lspci 2>/dev/null || echo 'lspci not installed'", timeout=4
    ),
    RemoteProbe(
        "hardware", "usb_devices", "lsusb 2>/dev/null || echo 'lsusb not installed'", timeout=4
    ),
)


@dataclass(frozen=True)
class PriorityHeuristic:
    """Metadata describing a priority finding heuristic."""

    key: str
    category: str
    severity: Literal["high", "medium", "info"]
    headline: str
    description: str


PRIORITY_HEURISTICS: tuple[PriorityHeuristic, ...] = (
    PriorityHeuristic(
        key="sudo_membership",
        category="users",
        severity="high",
        headline="Current user inherits elevated privileges",
        description="Detect membership in sudo or wheel groups to highlight immediate privilege escalation opportunities.",
    ),
    PriorityHeuristic(
        key="passwordless_sudo",
        category="users",
        severity="high",
        headline="Passwordless sudo rules discovered",
        description="Surface sudoers entries granting NOPASSWD access for rapid exploitation paths.",
    ),
    PriorityHeuristic(
        key="suid_binaries",
        category="filesystem",
        severity="high",
        headline="Potentially dangerous SUID/SGID binaries located",
        description="Summarize counts and notable privileged binaries for post-exploitation pivoting.",
    ),
    PriorityHeuristic(
        key="world_writable_dirs",
        category="filesystem",
        severity="medium",
        headline="World-writable directories outside canonical temp paths",
        description="Flag directories that may enable privilege escalation or persistence if writable by all users.",
    ),
    PriorityHeuristic(
        key="exposed_network_services",
        category="network",
        severity="medium",
        headline="Externally exposed network services",
        description="Highlight listening services bound to 0.0.0.0 or ::: to focus port enumeration efforts.",
    ),
    PriorityHeuristic(
        key="weak_ssh_configuration",
        category="security",
        severity="high",
        headline="Weak SSH daemon configuration detected",
        description="Call out insecure sshd_config directives such as PermitRootLogin yes or PasswordAuthentication yes.",
    ),
    PriorityHeuristic(
        key="suspicious_scheduled_tasks",
        category="scheduled",
        severity="medium",
        headline="Suspicious or high-impact scheduled tasks",
        description="Identify cron entries or systemd timers invoking network utilities or non-standard binaries.",
    ),
    PriorityHeuristic(
        key="kernel_drift",
        category="system",
        severity="info",
        headline="Kernel release deviates from package baseline",
        description="Note when the running kernel differs from package manager inventory, indicating pending reboots or manual installs.",
    ),
)
