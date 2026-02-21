"""Tests for config module - TOML operations, validation, backup, and save operations."""

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from lazyssh import config


class TestGetTerminalMethod:
    """Tests for get_terminal_method function."""

    def test_default_returns_auto(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default terminal method is 'auto'."""
        monkeypatch.delenv("LAZYSSH_TERMINAL_METHOD", raising=False)
        assert config.get_terminal_method() == "auto"

    @pytest.mark.parametrize(
        ("env_value", "expected"),
        [
            ("auto", "auto"),
            ("terminator", "terminator"),
            ("native", "native"),
            ("NATIVE", "native"),
            ("Terminator", "terminator"),
            ("AUTO", "auto"),
            ("invalid", "auto"),
        ],
        ids=[
            "auto",
            "terminator",
            "native",
            "case-NATIVE",
            "case-Terminator",
            "case-AUTO",
            "invalid-defaults-auto",
        ],
    )
    def test_returns_expected_method(
        self, monkeypatch: pytest.MonkeyPatch, env_value: str, expected: str
    ) -> None:
        """Test that the correct terminal method is returned for various inputs."""
        monkeypatch.setenv("LAZYSSH_TERMINAL_METHOD", env_value)
        assert config.get_terminal_method() == expected


class TestLoadConfig:
    """Tests for load_config function."""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that default config values are returned."""
        monkeypatch.delenv("LAZYSSH_SSH_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_TERMINAL", raising=False)
        monkeypatch.delenv("LAZYSSH_CONTROL_PATH", raising=False)
        monkeypatch.delenv("LAZYSSH_TERMINAL_METHOD", raising=False)

        cfg = config.load_config()

        assert cfg["ssh_path"] == "/usr/bin/ssh"
        assert cfg["terminal_emulator"] == "terminator"
        assert cfg["control_path_base"] == "/tmp/"
        assert cfg["terminal_method"] == "auto"

    def test_custom_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that custom env values are used."""
        monkeypatch.setenv("LAZYSSH_SSH_PATH", "/custom/ssh")
        monkeypatch.setenv("LAZYSSH_TERMINAL", "xterm")
        monkeypatch.setenv("LAZYSSH_CONTROL_PATH", "/var/run/")
        monkeypatch.setenv("LAZYSSH_TERMINAL_METHOD", "native")

        cfg = config.load_config()

        assert cfg["ssh_path"] == "/custom/ssh"
        assert cfg["terminal_emulator"] == "xterm"
        assert cfg["control_path_base"] == "/var/run/"
        assert cfg["terminal_method"] == "native"


class TestGetConfigFilePath:
    """Tests for get_config_file_path function."""

    def test_default_path(self) -> None:
        """Test that default path is returned."""
        path = config.get_config_file_path()
        assert path == Path("/tmp/lazyssh/connections.conf")

    def test_custom_path(self) -> None:
        """Test that custom path is returned."""
        path = config.get_config_file_path("/custom/path/config.toml")
        assert path == Path("/custom/path/config.toml")


class TestEnsureConfigDirectory:
    """Tests for ensure_config_directory function."""

    def test_creates_directory(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that directory is created if it doesn't exist."""
        # Reset APP_LOGGER to None to avoid log output
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        result = config.ensure_config_directory()

        assert result is True
        assert Path("/tmp/lazyssh").exists()

    def test_returns_true_when_exists(self) -> None:
        """Test returns True when directory already exists."""
        Path("/tmp/lazyssh").mkdir(parents=True, exist_ok=True)
        result = config.ensure_config_directory()
        assert result is True

    def test_permission_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that permission errors are handled."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        def mock_mkdir(*args, **kwargs):
            raise PermissionError("Permission denied")

        with mock.patch.object(Path, "mkdir", mock_mkdir):
            result = config.ensure_config_directory()
            assert result is False


class TestValidateConfigName:
    """Tests for validate_config_name function."""

    @pytest.mark.parametrize(
        "name",
        ["myconfig", "my-config", "my_config", "MyConfig123", "123"],
        ids=["alpha", "hyphen", "underscore", "mixed-case-digits", "digits-only"],
    )
    def test_valid_names(self, name: str) -> None:
        """Test valid configuration names."""
        assert config.validate_config_name(name) is True

    @pytest.mark.parametrize(
        "name",
        ["", "my config", "my.config", "my/config", "config!", "@config"],
        ids=["empty", "space", "dot", "slash", "exclamation", "at-sign"],
    )
    def test_invalid_names(self, name: str) -> None:
        """Test invalid configuration names."""
        assert config.validate_config_name(name) is False


class TestInitializeConfigFile:
    """Tests for initialize_config_file function."""

    def test_creates_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that config file is created."""
        config_path = tmp_path / "test_config.toml"
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        result = config.initialize_config_file(str(config_path))

        assert result is True
        assert config_path.exists()
        content = config_path.read_text()
        assert "LazySSH Connection Configuration File" in content

    def test_skips_existing_file(self, tmp_path: Path) -> None:
        """Test that existing files are not overwritten."""
        config_path = tmp_path / "existing.toml"
        config_path.write_text("existing content")

        result = config.initialize_config_file(str(config_path))

        assert result is True
        assert config_path.read_text() == "existing content"

    def test_fails_on_directory_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that failure to create directory returns False."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        def mock_ensure_fail():
            return False

        monkeypatch.setattr("lazyssh.config.ensure_config_directory", mock_ensure_fail)

        result = config.initialize_config_file("/nonexistent/path/config.toml")
        assert result is False

    def test_write_failure(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that write failures are handled."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        # Create a non-existent path to a file we can't write
        config_path = tmp_path / "readonly_dir" / "config.toml"

        def mock_open(*args, **kwargs):
            raise PermissionError("Cannot write")

        with mock.patch("builtins.open", mock_open):
            result = config.initialize_config_file(str(config_path))
            assert result is False


class TestLoadConfigs:
    """Tests for load_configs function."""

    def test_loads_configs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that configs are loaded from TOML file."""
        config_path = tmp_path / "configs.toml"
        config_path.write_text("""
[server1]
host = "192.168.1.1"
port = 22
username = "admin"

[server2]
host = "10.0.0.1"
port = 2222
username = "user"
""")
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        configs = config.load_configs(str(config_path))

        assert "server1" in configs
        assert configs["server1"]["host"] == "192.168.1.1"
        assert configs["server1"]["port"] == 22
        assert "server2" in configs
        assert configs["server2"]["port"] == 2222

    def test_returns_empty_for_missing_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing file returns empty dict."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        configs = config.load_configs(str(tmp_path / "nonexistent.toml"))
        assert configs == {}

    def test_returns_empty_for_invalid_toml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that invalid TOML returns empty dict."""
        config_path = tmp_path / "invalid.toml"
        config_path.write_text("this is not valid [toml")
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        configs = config.load_configs(str(config_path))
        assert configs == {}

    def test_handles_read_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that read errors are handled."""
        config_path = tmp_path / "error.toml"
        config_path.write_text("[valid]\nkey = 1")
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        def mock_open(*args, **kwargs):
            raise OSError("Read error")

        with mock.patch("builtins.open", mock_open):
            configs = config.load_configs(str(config_path))
            assert configs == {}


class TestSaveConfig:
    """Tests for save_config function."""

    def test_saves_new_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test saving a new configuration."""
        # Use a temp file for the config
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"

            # Override the default config path
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            # Create the directory
            config_path.parent.mkdir(parents=True, exist_ok=True)

            result = config.save_config(
                "myserver",
                {
                    "host": "192.168.1.100",
                    "port": 22,
                    "username": "admin",
                },
            )

            assert result is True
            assert config_path.exists()
            content = config_path.read_text()
            assert "[myserver]" in content
            assert 'host = "192.168.1.100"' in content

    def test_invalid_name_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that invalid config names are rejected."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        result = config.save_config("invalid name!", {"host": "test"})
        assert result is False

    def test_updates_existing_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating an existing configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("""# Header comment

[existing]
host = "old.host.com"
port = 22
""")
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config(
                "existing",
                {
                    "host": "new.host.com",
                    "port": 2222,
                },
            )

            assert result is True
            content = config_path.read_text()
            assert 'host = "new.host.com"' in content
            assert "port = 2222" in content
            assert "# Header comment" in content

    def test_saves_boolean_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that boolean values are saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config(
                "test",
                {
                    "host": "test.com",
                    "no_term": True,
                    "enabled": False,
                },
            )

            assert result is True
            content = config_path.read_text()
            assert "no_term = true" in content
            assert "enabled = false" in content

    def test_handles_none_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that None values are not written."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config(
                "test",
                {
                    "host": "test.com",
                    "optional_key": None,
                },
            )

            assert result is True
            content = config_path.read_text()
            assert "optional_key" not in content

    def test_appends_with_proper_spacing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that appended configs have proper spacing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("# Comment\n")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config("newconfig", {"host": "test.com"})

            assert result is True
            content = config_path.read_text()
            # Should have blank line before new section
            assert "\n\n[newconfig]" in content

    def test_temp_file_cleanup_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that temp files are cleaned up on error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text('[existing]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            # Make os.replace fail
            def mock_replace(src, dst):
                raise OSError("Replace failed")

            with mock.patch("os.replace", mock_replace):
                result = config.save_config("test", {"host": "test.com"})
                assert result is False

    def test_cleanup_error_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error handling during temp file cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text('[existing]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            # Set APP_LOGGER to None to test the else branch
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            def mock_unlink(path):
                raise OSError("Unlink failed")

            with (
                mock.patch("os.replace", mock_replace),
                mock.patch("os.unlink", mock_unlink),
            ):
                result = config.save_config("test", {"host": "test.com"})
                assert result is False


class TestDeleteConfig:
    """Tests for delete_config function."""

    def test_deletes_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test deleting an existing configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("""
[server1]
host = "192.168.1.1"
port = 22

[server2]
host = "10.0.0.1"
port = 2222
""")
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.delete_config("server1")

            assert result is True
            content = config_path.read_text()
            assert "[server1]" not in content
            assert "[server2]" in content

    def test_returns_false_for_missing_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that missing file returns False."""
        config_path = tmp_path / "nonexistent.conf"
        monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        result = config.delete_config("server1")
        assert result is False

    def test_returns_false_for_missing_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing config returns False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[other]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.delete_config("nonexistent")
            assert result is False

    def test_cleans_up_blank_lines(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that extra blank lines are cleaned up after deletion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("""[server1]
host = "a"



[server2]
host = "b"
""")
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.delete_config("server1")

            assert result is True
            content = config_path.read_text()
            # Should not have more than 2 consecutive newlines
            assert "\n\n\n" not in content

    def test_temp_file_cleanup_on_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that temp files are cleaned up on delete error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[server1]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            with mock.patch("os.replace", mock_replace):
                result = config.delete_config("server1")
                assert result is False

    def test_cleanup_error_during_delete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test cleanup error handling during delete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[server1]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            def mock_unlink(path):
                raise OSError("Unlink failed")

            with (
                mock.patch("os.replace", mock_replace),
                mock.patch("os.unlink", mock_unlink),
            ):
                result = config.delete_config("server1")
                assert result is False


class TestConfigExists:
    """Tests for config_exists function."""

    def test_returns_true_when_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test returns True when config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[myserver]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            assert config.config_exists("myserver") is True

    def test_returns_false_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test returns False when config doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[other]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            assert config.config_exists("myserver") is False


class TestGetConfig:
    """Tests for get_config function."""

    def test_returns_config_when_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test returns config dict when config exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[myserver]\nhost = "192.168.1.1"\nport = 22\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.get_config("myserver")

            assert result is not None
            assert result["host"] == "192.168.1.1"
            assert result["port"] == 22

    def test_returns_none_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test returns None when config doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[other]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            assert config.get_config("myserver") is None


class MockLogger:
    """Mock logger that captures all log messages."""

    def __init__(self):
        self.messages: list[tuple[str, str]] = []

    def debug(self, msg):
        self.messages.append(("debug", msg))

    def info(self, msg):
        self.messages.append(("info", msg))

    def warning(self, msg):
        self.messages.append(("warning", msg))

    def error(self, msg):
        self.messages.append(("error", msg))


class TestLoggingBranches:
    """Tests for code paths that involve APP_LOGGER."""

    def test_ensure_config_directory_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test ensure_config_directory with APP_LOGGER enabled."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        result = config.ensure_config_directory()

        assert result is True
        assert any("ensured" in msg for level, msg in logger.messages)

    def test_ensure_config_directory_error_with_logger(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test ensure_config_directory error path with logger."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        def mock_mkdir(*args, **kwargs):
            raise PermissionError("denied")

        with mock.patch.object(Path, "mkdir", mock_mkdir):
            result = config.ensure_config_directory()
            assert result is False
            assert any("Failed to create" in msg for level, msg in logger.messages)

    def test_initialize_config_file_with_logger(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialize_config_file with logger."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        # Use actual /tmp/lazyssh path which will work
        config_path = Path("/tmp/lazyssh/test_init_logger.toml")
        if config_path.exists():
            config_path.unlink()

        result = config.initialize_config_file(str(config_path))

        assert result is True
        assert any("Initialized" in msg for level, msg in logger.messages)

        # Cleanup
        if config_path.exists():
            config_path.unlink()

    def test_initialize_config_file_error_with_logger(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialize_config_file error with logger."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        # Use a path in /tmp/lazyssh so ensure_config_directory works
        config_path = Path("/tmp/lazyssh/test_error_logger.toml")
        if config_path.exists():
            config_path.unlink()

        original_open = open

        def mock_open(path, *args, **kwargs):
            if str(path) == str(config_path):
                raise OSError("Write error")
            return original_open(path, *args, **kwargs)

        with mock.patch("builtins.open", mock_open):
            result = config.initialize_config_file(str(config_path))
            assert result is False
            assert any("Failed to initialize" in msg for level, msg in logger.messages)

    def test_load_configs_debug_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_configs debug logging for missing file."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        result = config.load_configs(str(tmp_path / "missing.toml"))

        assert result == {}
        assert any("not found" in msg for level, msg in logger.messages)

    def test_load_configs_info_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test load_configs info logging for successful load."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        config_path = tmp_path / "test.toml"
        config_path.write_text('[server]\nhost = "test"\n')

        result = config.load_configs(str(config_path))

        assert "server" in result
        assert any("Loaded" in msg for level, msg in logger.messages)

    def test_load_configs_toml_error_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test load_configs TOML error logging."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        config_path = tmp_path / "invalid.toml"
        config_path.write_text("invalid [toml")

        result = config.load_configs(str(config_path))

        assert result == {}
        assert any("Failed to parse TOML" in msg for level, msg in logger.messages)

    def test_load_configs_general_error_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test load_configs general error logging."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        config_path = tmp_path / "test.toml"
        config_path.write_text('[server]\nhost = "test"\n')

        def mock_open(*args, **kwargs):
            raise OSError("Read error")

        with mock.patch("builtins.open", mock_open):
            result = config.load_configs(str(config_path))
            assert result == {}
            assert any("Failed to load" in msg for level, msg in logger.messages)

    def test_save_config_invalid_name_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config invalid name with logger."""
        logger = MockLogger()
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        result = config.save_config("invalid name!", {"host": "test"})

        assert result is False
        assert any("Invalid configuration name" in msg for level, msg in logger.messages)

    def test_save_config_success_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config success with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "lazyssh" / "connections.conf"
            config_path.parent.mkdir(parents=True, exist_ok=True)

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            result = config.save_config("myserver", {"host": "test.com"})

            assert result is True
            assert any("saved" in msg for level, msg in logger.messages)

    def test_save_config_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[existing]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            with mock.patch("os.replace", mock_replace):
                result = config.save_config("test", {"host": "test.com"})
                assert result is False
                assert any("Failed to save" in msg for level, msg in logger.messages)

    def test_save_config_cleanup_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config cleanup error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[existing]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            def mock_unlink(path):
                raise OSError("Unlink failed")

            with (
                mock.patch("os.replace", mock_replace),
                mock.patch("os.unlink", mock_unlink),
            ):
                result = config.save_config("test", {"host": "test.com"})
                assert result is False
                assert any("Failed to clean up" in msg for level, msg in logger.messages)

    def test_delete_config_file_not_found_with_logger(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test delete_config warning for missing file with logger."""
        logger = MockLogger()
        config_path = tmp_path / "nonexistent.conf"

        monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        result = config.delete_config("server1")

        assert result is False
        assert any("not found" in msg for level, msg in logger.messages)

    def test_delete_config_name_not_found_with_logger(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test delete_config warning for missing config name with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[other]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            result = config.delete_config("nonexistent")

            assert result is False
            assert any("not found" in msg for level, msg in logger.messages)

    def test_delete_config_success_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test delete_config success with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[server1]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            result = config.delete_config("server1")

            assert result is True
            assert any("deleted" in msg for level, msg in logger.messages)

    def test_delete_config_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test delete_config error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[server1]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            with mock.patch("os.replace", mock_replace):
                result = config.delete_config("server1")
                assert result is False
                assert any("Failed to delete" in msg for level, msg in logger.messages)

    def test_delete_config_cleanup_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test delete_config cleanup error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text('[server1]\nhost = "test"\n')

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            def mock_unlink(path):
                raise OSError("Unlink failed")

            with (
                mock.patch("os.replace", mock_replace),
                mock.patch("os.unlink", mock_unlink),
            ):
                result = config.delete_config("server1")
                assert result is False
                assert any("Failed to clean up" in msg for level, msg in logger.messages)

    def test_backup_config_success_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test backup_config success with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            success, message = config.backup_config()

            assert success is True
            assert any("backed up" in msg for level, msg in logger.messages)

    def test_backup_config_debug_log(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test backup_config debug logging for missing file."""
        logger = MockLogger()
        config_path = tmp_path / "nonexistent.conf"

        monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

        success, message = config.backup_config()

        assert success is False
        assert any("No configuration file" in msg for level, msg in logger.messages)

    def test_backup_config_permission_error_with_logger(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test backup_config permission error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_mkstemp(*args, **kwargs):
                raise PermissionError("denied")

            with mock.patch("tempfile.mkstemp", mock_mkstemp):
                success, message = config.backup_config()
                assert success is False
                assert any("Permission denied" in msg for level, msg in logger.messages)

    def test_backup_config_general_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test backup_config general error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_open(*args, **kwargs):
                raise OSError("Read error")

            with mock.patch("builtins.open", mock_open):
                success, message = config.backup_config()
                assert success is False
                assert any("Failed to create backup" in msg for level, msg in logger.messages)

    def test_backup_config_cleanup_error_with_logger(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test backup_config cleanup error with logger."""
        logger = MockLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", logger)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            def mock_unlink(path):
                raise OSError("Unlink failed")

            with (
                mock.patch("os.replace", mock_replace),
                mock.patch("os.unlink", mock_unlink),
            ):
                success, message = config.backup_config()
                assert success is False
                assert any("Failed to clean up" in msg for level, msg in logger.messages)


class TestEdgeCases:
    """Tests for edge cases in config module."""

    def test_save_config_ensure_dir_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config when ensure_config_directory fails."""
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)
        monkeypatch.setattr("lazyssh.config.ensure_config_directory", lambda: False)

        result = config.save_config("myserver", {"host": "test.com"})
        assert result is False

    def test_save_config_initialize_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config when initialize_config_file fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            # Don't create the file so initialize_config_file will be called

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)
            monkeypatch.setattr("lazyssh.config.initialize_config_file", lambda x=None: False)

            result = config.save_config("myserver", {"host": "test.com"})
            assert result is False

    def test_save_config_file_ends_without_newline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test save_config when file doesn't end with newline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            # Write content without trailing newlines
            config_path.write_text("# Header")  # No trailing newline

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config("newconfig", {"host": "test.com"})

            assert result is True
            content = config_path.read_text()
            assert "[newconfig]" in content
            # Should have added \n\n before the new section
            assert "# Header\n\n[newconfig]" in content

    def test_save_config_updates_with_bool_in_update(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating existing config with boolean value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("""[existing]
host = "old.host.com"
port = 22
""")
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config(
                "existing",
                {
                    "host": "new.host.com",
                    "no_term": True,
                },
            )

            assert result is True
            content = config_path.read_text()
            assert 'host = "new.host.com"' in content
            assert "no_term = true" in content

    def test_save_config_updates_with_int_value(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating existing config with integer value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("""[existing]
host = "host.com"
""")
            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            result = config.save_config(
                "existing",
                {
                    "host": "host.com",
                    "port": 2222,
                },
            )

            assert result is True
            content = config_path.read_text()
            assert "port = 2222" in content


class TestBackupConfig:
    """Tests for backup_config function."""

    def test_creates_backup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that backup is created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            backup_path = Path(tmpdir) / "connections.conf.backup"
            config_path.write_text("original content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            success, message = config.backup_config()

            assert success is True
            assert backup_path.exists()
            assert backup_path.read_text() == "original content"
            assert str(backup_path) in message

    def test_returns_false_when_no_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test returns False when config file doesn't exist."""
        config_path = tmp_path / "nonexistent.conf"
        monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
        monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

        success, message = config.backup_config()

        assert success is False
        assert "No configuration file" in message

    def test_overwrites_existing_backup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that existing backup is overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            backup_path = Path(tmpdir) / "connections.conf.backup"
            config_path.write_text("new content")
            backup_path.write_text("old backup")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            success, message = config.backup_config()

            assert success is True
            assert backup_path.read_text() == "new content"

    def test_handles_permission_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that permission errors are handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            def mock_mkstemp(*args, **kwargs):
                raise PermissionError("No permission")

            with mock.patch("tempfile.mkstemp", mock_mkstemp):
                success, message = config.backup_config()

                assert success is False
                assert "permission denied" in message.lower()

    def test_handles_general_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that general errors are handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            def mock_read(*args, **kwargs):
                raise OSError("Read error")

            with mock.patch("builtins.open", mock_read):
                success, message = config.backup_config()

                assert success is False
                assert "Cannot create backup" in message

    def test_cleanup_on_replace_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test temp file cleanup on replace error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)

            original_mkstemp = tempfile.mkstemp

            def tracked_mkstemp(*args, **kwargs):
                return original_mkstemp(*args, **kwargs)

            def mock_replace(src, dst):
                raise OSError("Replace failed")

            with mock.patch("os.replace", mock_replace):
                success, message = config.backup_config()
                assert success is False

    def test_directory_creation_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that directory creation failure is handled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "connections.conf"
            config_path.write_text("content")

            monkeypatch.setattr("lazyssh.config.get_config_file_path", lambda x=None: config_path)
            monkeypatch.setattr("lazyssh.config.APP_LOGGER", None)
            monkeypatch.setattr("lazyssh.config.ensure_config_directory", lambda: False)

            success, message = config.backup_config()

            assert success is False
            assert "directory creation failed" in message
