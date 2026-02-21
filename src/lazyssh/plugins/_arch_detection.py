"""Remote architecture detection for LazySSH plugins.

Detects remote system architecture and OS via SSH control socket,
mapping to msfvenom-compatible identifiers for payload generation.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class RemoteArch:
    """Detected remote system architecture."""

    raw_arch: str  # e.g., "x86_64"
    raw_os: str  # e.g., "Linux"
    msf_arch: str  # e.g., "x64"
    msf_platform: str  # e.g., "linux"


ARCH_MAP: dict[str, str] = {
    "x86_64": "x64",
    "amd64": "x64",
    "i686": "x86",
    "i386": "x86",
    "aarch64": "aarch64",
    "arm64": "aarch64",
    "armv7l": "armle",
    "armv6l": "armle",
    "mips": "mips",
    "mipsel": "mipsel",
    "ppc64le": "ppc64le",
}

PLATFORM_MAP: dict[str, str] = {
    "linux": "linux",
    "darwin": "osx",
    "freebsd": "bsd",
    "openbsd": "bsd",
    "netbsd": "bsd",
    "sunos": "solaris",
}


def detect_remote_arch(
    socket_path: str | None = None,
    host: str | None = None,
    user: str | None = None,
    port: str | None = None,
) -> RemoteArch:
    """Detect remote architecture via SSH control socket.

    Parameters are read from environment variables when not provided:
      LAZYSSH_SOCKET_PATH, LAZYSSH_HOST, LAZYSSH_USER, LAZYSSH_PORT

    Raises RuntimeError if SSH execution fails.
    """
    socket_path = socket_path or os.environ.get("LAZYSSH_SOCKET_PATH", "")
    host = host or os.environ.get("LAZYSSH_HOST", "")
    user = user or os.environ.get("LAZYSSH_USER", "")
    port = port or os.environ.get("LAZYSSH_PORT")

    if not socket_path or not host or not user:
        raise RuntimeError("Missing SSH environment variables for architecture detection")

    ssh_cmd: list[str] = ["ssh", "-S", socket_path, "-o", "ControlMaster=no"]
    if port:
        ssh_cmd.extend(["-p", port])
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.extend(["sh", "-c", "uname -m && uname -s"])

    try:
        result = subprocess.run(  # noqa: S603,S607
            ssh_cmd,
            text=True,
            capture_output=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Architecture detection timed out") from exc

    if result.returncode != 0:
        raise RuntimeError(f"Architecture detection failed: {result.stderr.strip()}")

    lines = result.stdout.strip().splitlines()
    if len(lines) < 2:  # noqa: PLR2004
        raise RuntimeError(f"Unexpected uname output: {result.stdout!r}")

    raw_arch = lines[0].strip()
    raw_os = lines[1].strip()

    msf_arch = ARCH_MAP.get(raw_arch, raw_arch)
    msf_platform = PLATFORM_MAP.get(raw_os.lower(), raw_os.lower())

    return RemoteArch(
        raw_arch=raw_arch,
        raw_os=raw_os,
        msf_arch=msf_arch,
        msf_platform=msf_platform,
    )
