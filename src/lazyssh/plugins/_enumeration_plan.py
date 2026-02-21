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
        "journalctl -n 20 -u ssh --no-pager 2>/dev/null || "
        "tail -n 20 /var/log/auth.log 2>/dev/null || "
        "tail -n 20 /var/log/secure 2>/dev/null || echo 'Authentication logs unavailable'",
        timeout=6,
    ),
    RemoteProbe(
        "logs",
        "syslog_recent",
        "journalctl -n 20 --no-pager 2>/dev/null || tail -n 20 /var/log/syslog 2>/dev/null || "
        "tail -n 20 /var/log/messages 2>/dev/null || echo 'System logs unavailable'",
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
    # Capabilities
    RemoteProbe(
        "capabilities",
        "cap_binaries",
        "getcap -r / 2>/dev/null",
        timeout=10,
    ),
    RemoteProbe(
        "capabilities",
        "cap_interesting",
        "getcap -r / 2>/dev/null | grep -iE 'cap_setuid|cap_setgid|cap_dac_override|cap_sys_admin|cap_sys_ptrace|cap_net_raw|cap_chown|cap_fowner'",
        timeout=10,
    ),
    # Container detection
    RemoteProbe(
        "container",
        "docker_group",
        "id -nG 2>/dev/null | tr ' ' '\\n' | grep -q docker && echo 'IN_DOCKER_GROUP' || echo 'NOT_IN_DOCKER_GROUP'",
        timeout=4,
    ),
    RemoteProbe(
        "container",
        "docker_socket",
        "test -r /var/run/docker.sock && echo 'DOCKER_SOCKET_READABLE' || echo 'DOCKER_SOCKET_NOT_READABLE'",
        timeout=4,
    ),
    RemoteProbe(
        "container",
        "container_detection",
        "if [ -f /.dockerenv ]; then echo 'DOCKER_CONTAINER'; "
        "elif grep -q docker /proc/1/cgroup 2>/dev/null; then echo 'DOCKER_CONTAINER_CGROUP'; "
        "elif grep -q lxc /proc/1/cgroup 2>/dev/null; then echo 'LXC_CONTAINER'; "
        "elif [ -d /run/lxc ] || [ -f /dev/lxd/sock ]; then echo 'LXC_CONTAINER'; "
        "else echo 'NOT_CONTAINER'; fi",
        timeout=6,
    ),
    RemoteProbe(
        "container",
        "lxc_check",
        "if [ -S /dev/lxd/sock ] || command -v lxc >/dev/null 2>&1; then "
        "echo 'LXD_PRESENT'; lxc list 2>/dev/null || echo 'LXC_LIST_DENIED'; "
        "else echo 'NO_LXD'; fi",
        timeout=4,
    ),
    # Credentials
    RemoteProbe(
        "credentials",
        "shadow_readable",
        "cat /etc/shadow 2>/dev/null | head -5 || echo 'SHADOW_NOT_READABLE'",
        timeout=4,
    ),
    RemoteProbe(
        "credentials",
        "ssh_keys",
        "find /root/.ssh /home/*/.ssh -name 'id_*' ! -name '*.pub' -readable 2>/dev/null || echo 'NO_READABLE_KEYS'",
        timeout=8,
    ),
    RemoteProbe(
        "credentials",
        "history_files",
        "for f in ~/.bash_history ~/.zsh_history ~/.python_history /root/.bash_history; do "
        'if [ -r "$f" ]; then grep -iE \'pass(word)?=|token=|secret=|api_key=\' "$f" 2>/dev/null | head -5 && echo "FILE:$f"; fi; done || echo \'NO_HISTORY_SECRETS\'',
        timeout=8,
    ),
    RemoteProbe(
        "credentials",
        "config_credentials",
        "find / -maxdepth 4 \\( -name '.env' -o -name '.htpasswd' -o -name 'wp-config.php' \\) -readable 2>/dev/null | head -20 || echo 'NONE_FOUND'",
        timeout=8,
    ),
    RemoteProbe(
        "credentials",
        "cloud_credentials",
        "ls -la ~/.aws/credentials ~/.config/gcloud/application_default_credentials.json ~/.azure/accessTokens.json 2>/dev/null || echo 'NO_CLOUD_CREDS'; "
        "curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ 2>/dev/null | head -5 && echo 'AWS_METADATA_AVAILABLE' || echo 'NO_CLOUD_METADATA'",
        timeout=8,
    ),
    RemoteProbe(
        "credentials",
        "git_credentials",
        "cat ~/.git-credentials 2>/dev/null | head -5; "
        "grep -E 'credential|password|token' ~/.gitconfig 2>/dev/null || echo 'NO_GIT_CREDS'",
        timeout=4,
    ),
    RemoteProbe(
        "credentials",
        "database_configs",
        "cat ~/.my.cnf ~/.pgpass 2>/dev/null | head -10; "
        "find /etc -maxdepth 2 -name 'mongod.conf' -readable 2>/dev/null || echo 'NO_DB_CONFIGS'",
        timeout=4,
    ),
    # Writable critical files
    RemoteProbe(
        "writable",
        "writable_passwd",
        "test -w /etc/passwd && echo 'WRITABLE' || echo 'NOT_WRITABLE'",
        timeout=3,
    ),
    RemoteProbe(
        "writable",
        "writable_shadow",
        "test -w /etc/shadow && echo 'WRITABLE' || echo 'NOT_WRITABLE'",
        timeout=3,
    ),
    RemoteProbe(
        "writable",
        "writable_sudoers",
        "test -w /etc/sudoers && echo 'WRITABLE'; "
        'for f in /etc/sudoers.d/*; do test -w "$f" 2>/dev/null && echo "WRITABLE:$f"; done; '
        "echo 'DONE'",
        timeout=4,
    ),
    RemoteProbe(
        "writable",
        "writable_cron",
        "for f in /etc/crontab /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/cron.monthly; do "
        'test -w "$f" 2>/dev/null && echo "WRITABLE:$f"; done; echo \'DONE\'',
        timeout=6,
    ),
    RemoteProbe(
        "writable",
        "writable_services",
        "find /etc/systemd/system /usr/lib/systemd/system -type f -writable 2>/dev/null | head -20 || echo 'NONE_WRITABLE'",
        timeout=8,
    ),
    RemoteProbe(
        "writable",
        "writable_path_dirs",
        'IFS=:; for d in $PATH; do test -w "$d" 2>/dev/null && echo "WRITABLE:$d"; done; echo \'DONE\'',
        timeout=6,
    ),
    RemoteProbe(
        "writable",
        "writable_profile",
        "for f in /etc/profile /etc/bash.bashrc /etc/bashrc /etc/environment; do "
        'test -w "$f" 2>/dev/null && echo "WRITABLE:$f"; done; echo \'DONE\'',
        timeout=4,
    ),
    RemoteProbe(
        "writable",
        "writable_init_scripts",
        "find /etc/init.d -type f -writable 2>/dev/null | head -20 || echo 'NONE_WRITABLE'",
        timeout=4,
    ),
    # Library hijack
    RemoteProbe(
        "library_hijack",
        "ld_preload",
        "echo \"LD_PRELOAD=$LD_PRELOAD\"; cat /etc/ld.so.preload 2>/dev/null || echo 'NO_LD_PRELOAD_FILE'",
        timeout=4,
    ),
    RemoteProbe(
        "library_hijack",
        "ld_library_path",
        'echo "LD_LIBRARY_PATH=$LD_LIBRARY_PATH"; '
        'IFS=:; for d in $LD_LIBRARY_PATH; do test -w "$d" 2>/dev/null && echo "WRITABLE:$d"; done; echo \'DONE\'',
        timeout=4,
    ),
    RemoteProbe(
        "library_hijack",
        "python_path",
        'echo "PYTHONPATH=$PYTHONPATH"; '
        "python3 -c 'import sys; [print(p) for p in sys.path]' 2>/dev/null | while read -r d; do "
        'test -w "$d" 2>/dev/null && echo "WRITABLE:$d"; done; echo \'DONE\'',
        timeout=6,
    ),
    RemoteProbe(
        "library_hijack",
        "rpath_runpath",
        "find / -xdev -perm -4000 -type f 2>/dev/null | head -10 | while read -r f; do "
        "readelf -d \"$f\" 2>/dev/null | grep -E 'RPATH|RUNPATH' && echo \"BINARY:$f\"; done; echo 'DONE'",
        timeout=8,
    ),
    # Interesting files
    RemoteProbe(
        "interesting_files",
        "backup_files",
        "ls -la /var/backups/ 2>/dev/null; "
        "find / -maxdepth 3 \\( -name '*.bak' -o -name '*.old' -o -name '*.backup' -o -name '*.sql' \\) -readable 2>/dev/null | head -20 || echo 'NO_BACKUPS'",
        timeout=6,
    ),
    RemoteProbe(
        "interesting_files",
        "mail_files",
        "ls -la /var/mail/ /var/spool/mail/ 2>/dev/null || echo 'NO_MAIL'",
        timeout=4,
    ),
    RemoteProbe(
        "interesting_files",
        "opt_contents",
        "ls -la /opt/ 2>/dev/null || echo 'EMPTY_OPT'",
        timeout=4,
    ),
    RemoteProbe(
        "interesting_files",
        "tmp_interesting",
        "find /tmp /var/tmp /dev/shm -type f \\( -name '*.sh' -o -name '*.py' -o -name '*.pl' -o -perm -111 \\) 2>/dev/null | head -20 || echo 'NONE_FOUND'",
        timeout=8,
    ),
    RemoteProbe(
        "interesting_files",
        "recently_modified",
        "find /etc /usr/local/bin /usr/local/sbin -type f -mtime -1 2>/dev/null | head -20 || echo 'NONE_RECENT'",
        timeout=8,
    ),
    # Additions to existing categories
    # filesystem additions
    RemoteProbe(
        "filesystem",
        "nfs_exports",
        "cat /etc/exports 2>/dev/null || echo 'NO_NFS_EXPORTS'",
        timeout=4,
    ),
    RemoteProbe(
        "filesystem",
        "mounted_nfs",
        "mount | grep -i nfs 2>/dev/null || echo 'NO_NFS_MOUNTS'",
        timeout=4,
    ),
    # users additions
    RemoteProbe(
        "users",
        "doas_conf",
        "cat /etc/doas.conf 2>/dev/null || echo 'NO_DOAS'",
        timeout=4,
    ),
    RemoteProbe(
        "users",
        "polkit_rules",
        "find /etc/polkit-1 /usr/share/polkit-1 -type f -name '*.rules' -o -name '*.pkla' 2>/dev/null | head -10; "
        "cat /etc/polkit-1/localauthority.conf.d/*.pkla 2>/dev/null || echo 'NO_POLKIT_RULES'",
        timeout=6,
    ),
    RemoteProbe(
        "users",
        "pkexec_version",
        "pkexec --version 2>/dev/null || echo 'PKEXEC_NOT_FOUND'",
        timeout=3,
    ),
)


@dataclass(frozen=True)
class PriorityHeuristic:
    """Metadata describing a priority finding heuristic."""

    key: str
    category: str
    severity: Literal["critical", "high", "medium", "info"]
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
    # New heuristics for expanded probe categories
    PriorityHeuristic(
        key="dangerous_capabilities",
        category="capabilities",
        severity="high",
        headline="Binaries with dangerous Linux capabilities found",
        description="Flag binaries with cap_setuid, cap_sys_admin, or other privilege-granting capabilities.",
    ),
    PriorityHeuristic(
        key="writable_passwd_file",
        category="writable",
        severity="critical",
        headline="World-writable /etc/passwd allows instant root",
        description="If /etc/passwd is writable, a new root-level user can be appended for instant privilege escalation.",
    ),
    PriorityHeuristic(
        key="docker_escape",
        category="container",
        severity="high",
        headline="Docker group membership or socket access enables host escape",
        description="User is in the docker group or can access the Docker socket, enabling host filesystem mount and root-level escape.",
    ),
    PriorityHeuristic(
        key="writable_service_files",
        category="writable",
        severity="high",
        headline="Writable systemd service files detected",
        description="Writable service files run as root can be modified to execute arbitrary commands on service restart.",
    ),
    PriorityHeuristic(
        key="credential_exposure",
        category="credentials",
        severity="high",
        headline="Exposed credentials or sensitive authentication material",
        description="Readable SSH private keys, shadow file, or credential files found on disk.",
    ),
    PriorityHeuristic(
        key="gtfobins_sudo",
        category="users",
        severity="high",
        headline="Sudo-allowed binaries exploitable via GTFOBins",
        description="Cross-reference sudo-allowed commands against GTFOBins database for known shell escape techniques.",
    ),
    PriorityHeuristic(
        key="gtfobins_suid",
        category="filesystem",
        severity="high",
        headline="SUID binaries exploitable via GTFOBins",
        description="Cross-reference SUID binaries against GTFOBins database for known privilege escalation techniques.",
    ),
    PriorityHeuristic(
        key="writable_path",
        category="writable",
        severity="medium",
        headline="Writable directories found in PATH",
        description="Writable PATH directories allow binary planting for privilege escalation when higher-privileged users or services execute commands.",
    ),
    PriorityHeuristic(
        key="writable_cron_files",
        category="writable",
        severity="medium",
        headline="Writable cron files or directories detected",
        description="Writable cron entries can be modified to execute arbitrary commands on schedule.",
    ),
    PriorityHeuristic(
        key="nfs_no_root_squash",
        category="filesystem",
        severity="medium",
        headline="NFS exports with no_root_squash allow remote root access",
        description="NFS shares exported with no_root_squash preserve remote root UID, enabling privileged file creation.",
    ),
    PriorityHeuristic(
        key="ld_preload_hijack",
        category="library_hijack",
        severity="medium",
        headline="Library preload hijacking opportunity detected",
        description="LD_PRELOAD or /etc/ld.so.preload configuration allows injecting shared libraries into privileged processes.",
    ),
    PriorityHeuristic(
        key="container_detected",
        category="container",
        severity="medium",
        headline="Running inside a container environment",
        description="System appears to be running inside Docker or LXC, which may limit exploitation but also present escape vectors.",
    ),
    PriorityHeuristic(
        key="cloud_environment",
        category="credentials",
        severity="info",
        headline="Cloud credential files or metadata endpoint accessible",
        description="AWS, GCP, or Azure credential files found, or cloud metadata endpoint is reachable.",
    ),
    PriorityHeuristic(
        key="interesting_backups",
        category="interesting_files",
        severity="info",
        headline="Accessible backup files found",
        description="Backup files (.bak, .old, .sql) may contain sensitive data or previous configurations.",
    ),
    PriorityHeuristic(
        key="recent_modifications",
        category="interesting_files",
        severity="info",
        headline="Recently modified files in sensitive locations",
        description="Files modified in the last 24 hours in /etc, /usr/local/bin, or /usr/local/sbin may indicate active changes.",
    ),
    PriorityHeuristic(
        key="kernel_exploits",
        category="system",
        severity="high",
        headline="Kernel version matches known privilege-escalation CVEs",
        description="Running kernel version falls within the affected range of one or more public kernel exploits (Dirty Pipe, Dirty COW, PwnKit, etc.).",
    ),
)
