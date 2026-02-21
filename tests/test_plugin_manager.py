import os
import stat
from pathlib import Path

from lazyssh.models import SSHConnection
from lazyssh.plugin_manager import PluginManager, ensure_runtime_plugins_dir


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    # Make executable
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR)


def test_discover_and_metadata_python_plugin(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "hello.py"
    _write_file(
        plugin_path,
        """#!/usr/bin/env python3
# PLUGIN_NAME: hello
# PLUGIN_DESCRIPTION: Say hello
# PLUGIN_VERSION: 1.2.3
# PLUGIN_REQUIREMENTS: python3
print("hello")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "hello" in plugins
    meta = plugins["hello"]
    assert meta.name == "hello"
    assert meta.description == "Say hello"
    assert meta.version == "1.2.3"
    assert meta.requirements == "python3"
    assert meta.plugin_type == "python"
    assert meta.is_valid is True


def test_python_plugin_missing_exec_bit_is_repaired(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "fixed.py"
    plugin_path.write_text(
        """#!/usr/bin/env python3
print("ok")
""",
        encoding="utf-8",
    )
    # Ensure execute bit is not set to begin with
    plugin_path.chmod(plugin_path.stat().st_mode & ~stat.S_IXUSR)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)
    meta = plugins["fixed"]

    assert meta.is_valid is True
    assert meta.validation_errors == []
    assert meta.validation_warnings == []
    assert os.access(plugin_path, os.X_OK) is True


def test_python_plugin_without_shebang_emits_warning(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "noshebang.py"
    plugin_path.write_text("print('no shebang')\n", encoding="utf-8")
    plugin_path.chmod(plugin_path.stat().st_mode | stat.S_IXUSR)

    pm = PluginManager(plugins_dir=plugins_dir)
    meta = pm.discover_plugins(force_refresh=True)["noshebang"]

    assert meta.is_valid is True
    assert meta.validation_errors == []
    assert len(meta.validation_warnings) >= 1  # Missing shebang


def test_python_plugin_missing_exec_bit_warns_when_unrepairable(
    tmp_path: Path, monkeypatch
) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "unexec.py"
    plugin_path.write_text(
        """#!/usr/bin/env python3
print("hi")
""",
        encoding="utf-8",
    )
    plugin_path.chmod(plugin_path.stat().st_mode & ~stat.S_IXUSR)

    def _raise_permission_error(self: Path, mode: int) -> None:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "chmod", _raise_permission_error, raising=False)

    pm = PluginManager(plugins_dir=plugins_dir)
    meta = pm.discover_plugins(force_refresh=True)["unexec"]

    assert meta.is_valid is True
    assert meta.validation_errors == []
    assert len(meta.validation_warnings) >= 1  # Unrepairable exec bit
    assert os.access(plugin_path, os.X_OK) is False


def test_shell_plugin_requires_shebang_and_exec_bit(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "bad.sh"
    plugin_path.write_text("echo 'missing shebang'\n", encoding="utf-8")
    # No exec bit to trigger executable validation
    plugin_path.chmod(plugin_path.stat().st_mode & ~stat.S_IXUSR)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)
    meta = plugins["bad"]

    assert meta.is_valid is False
    assert any("shebang" in err.lower() for err in meta.validation_errors)


def test_execute_plugin_passes_env_and_captures_output(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "envdump.py"
    _write_file(
        plugin_path,
        """#!/usr/bin/env python3
import os
print(os.environ.get("LAZYSSH_SOCKET"))
print(os.environ.get("LAZYSSH_HOST"))
print(os.environ.get("LAZYSSH_USER"))
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)

    conn = SSHConnection(host="1.2.3.4", port=22, username="alice", socket_path="/tmp/testsock")
    success, output, elapsed = pm.execute_plugin("envdump", conn)

    assert success is True
    assert "testsock" in output
    assert "1.2.3.4" in output
    assert "alice" in output
    assert elapsed >= 0


def test_env_dirs_precedence_over_user_and_packaged(tmp_path: Path, monkeypatch) -> None:
    # Create two env dirs A and B, and an empty packaged dir to avoid interference
    env_a = tmp_path / "envA"
    env_b = tmp_path / "envB"
    pkg_dir = tmp_path / "pkg"
    env_a.mkdir()
    env_b.mkdir()
    pkg_dir.mkdir()

    # Same plugin name in both env dirs; B should win if B is first in env list
    _write_file(
        env_a / "dup.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: duplicate
print("from A")
""",
    )
    _write_file(
        env_b / "dup.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: duplicate
print("from B")
""",
    )

    monkeypatch.setenv("LAZYSSH_PLUGIN_DIRS", f"{env_b}:{env_a}")

    pm = PluginManager(plugins_dir=pkg_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "duplicate" in plugins
    # Ensure file path points to env_b version (precedence left-to-right)
    assert str(plugins["duplicate"].file_path).startswith(str(env_b))


def test_user_dir_included_when_no_env(monkeypatch, tmp_path: Path) -> None:
    # Simulate home directory
    fake_home = tmp_path / "home"
    user_plugins = fake_home / ".lazyssh" / "plugins"
    user_plugins.mkdir(parents=True)

    # Patch Path.home to our fake home
    monkeypatch.setattr(Path, "home", lambda: fake_home)  # type: ignore[assignment]

    # Create a user plugin
    _write_file(
        user_plugins / "hey.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: hey
print("hey")
""",
    )

    # Empty packaged dir to isolate
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()

    # Ensure env is unset
    monkeypatch.delenv("LAZYSSH_PLUGIN_DIRS", raising=False)

    pm = PluginManager(plugins_dir=pkg_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "hey" in plugins
    assert str(plugins["hey"].file_path).startswith(str(user_plugins))


def test_nonexistent_env_dirs_are_ignored(monkeypatch, tmp_path: Path) -> None:
    # Env points to absolute but non-existent paths
    fake1 = str(tmp_path / "nope1")
    fake2 = str(tmp_path / "nope2")
    monkeypatch.setenv("LAZYSSH_PLUGIN_DIRS", f"{fake1}:{fake2}")

    # Empty packaged dir
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()

    pm = PluginManager(plugins_dir=pkg_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # No crash and no plugins found
    assert isinstance(plugins, dict)
    assert len(plugins) == 0


def test_runtime_dir_is_created_with_permissions(tmp_path: Path, monkeypatch) -> None:
    # Redirect runtime dir to a temp path for test isolation
    fake_runtime = tmp_path / "rt" / "plugins"
    monkeypatch.setattr("lazyssh.plugin_manager.RUNTIME_PLUGINS_DIR", fake_runtime, raising=False)

    # Ensure creation
    ensure_runtime_plugins_dir()

    assert fake_runtime.exists()
    # Check mode 0700
    mode = fake_runtime.stat().st_mode & 0o777
    assert mode == 0o700


def test_runtime_precedence_over_packaged_when_no_env_or_user(tmp_path: Path, monkeypatch) -> None:
    # Setup packaged dir with a plugin
    pkg_dir = tmp_path / "pkg"
    runtime_dir = tmp_path / "rt" / "plugins"
    user_dir = tmp_path / "home" / ".lazyssh" / "plugins"
    pkg_dir.mkdir(parents=True)
    runtime_dir.mkdir(parents=True)
    user_dir.mkdir(parents=True)

    def _write(path: Path, text: str) -> None:
        path.write_text(text, encoding="utf-8")
        path.chmod((path.stat().st_mode) | 0o100)

    # Same plugin name in runtime and packaged; runtime should win
    _write(
        pkg_dir / "dup.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: duplicate
print("from packaged")
""",
    )
    _write(
        runtime_dir / "dup.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: duplicate
print("from runtime")
""",
    )

    # Point home to fake user dir but leave it empty; unset env
    monkeypatch.setattr(Path, "home", lambda: user_dir.parents[2])  # type: ignore[assignment]
    monkeypatch.delenv("LAZYSSH_PLUGIN_DIRS", raising=False)
    # Redirect runtime constant
    monkeypatch.setattr("lazyssh.plugin_manager.RUNTIME_PLUGINS_DIR", runtime_dir, raising=False)

    pm = PluginManager(plugins_dir=pkg_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "duplicate" in plugins
    assert str(plugins["duplicate"].file_path).startswith(str(runtime_dir))


def test_runtime_dir_creation_failure_logs_warning(tmp_path: Path, monkeypatch) -> None:
    # Simulate an existing file at the runtime path so mkdir fails
    error_path = tmp_path / "rt-file"
    error_path.write_text("blocking file", encoding="utf-8")
    monkeypatch.setattr("lazyssh.plugin_manager.RUNTIME_PLUGINS_DIR", error_path, raising=False)

    logged: list[str] = []

    class DummyLogger:
        def warning(self, message: str) -> None:
            logged.append(message)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    # Should not raise despite the failure
    ensure_runtime_plugins_dir()

    assert logged
    assert "Failed to ensure runtime plugins dir" in logged[0]


def test_runtime_enforces_exec_bit_for_packaged_plugins(tmp_path: Path) -> None:
    # Create packaged dir with plugin that has shebang but no exec bit
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()

    p = pkg_dir / "runme.py"
    p.write_text(
        """#!/usr/bin/env python3
# PLUGIN_NAME: runme
print("ok")
""",
        encoding="utf-8",
    )
    # Ensure exec bit is removed
    p.chmod(0o644)

    # Initialize PluginManager should best-effort add user exec bit
    pm = PluginManager(plugins_dir=pkg_dir)

    # Now it should be executable
    assert os.access(p, os.X_OK)

    # And discovery should mark it valid
    plugins = pm.discover_plugins(force_refresh=True)
    assert plugins["runme"].is_valid is True


def test_python_plugin_shebang_check_failure_warns(tmp_path: Path, monkeypatch) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    plugin_path = plugins_dir / "shebang_fail.py"
    plugin_path.write_text(
        """#!/usr/bin/env python3
print("hi")
""",
        encoding="utf-8",
    )
    plugin_path.chmod(plugin_path.stat().st_mode | stat.S_IXUSR)

    def _raise_io_error(*args, **kwargs):
        raise OSError("access denied")

    monkeypatch.setattr("builtins.open", _raise_io_error)

    pm = PluginManager(plugins_dir=plugins_dir)
    meta = pm.discover_plugins(force_refresh=True)["shebang_fail"]

    assert meta.is_valid is True
    assert meta.validation_errors == []
    assert len(meta.validation_warnings) >= 2  # Failed to read file and failed to check shebang


def test_discover_plugins_uses_cache(tmp_path: Path) -> None:
    """Test that discover_plugins uses cache when force_refresh=False."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    _write_file(
        plugins_dir / "cached.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: cached
print("hello")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    # First call populates cache
    plugins1 = pm.discover_plugins()
    assert "cached" in plugins1

    # Remove the plugin file
    (plugins_dir / "cached.py").unlink()

    # Second call should use cache (not re-scan)
    plugins2 = pm.discover_plugins()
    assert "cached" in plugins2  # Still in cache

    # Force refresh should pick up change
    plugins3 = pm.discover_plugins(force_refresh=True)
    assert "cached" not in plugins3


def test_discover_plugins_init_logging(tmp_path: Path, monkeypatch) -> None:
    """Test initialization logging."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    PluginManager(plugins_dir=plugins_dir)

    assert any("initialized" in m.lower() for m in messages)


def test_discover_plugins_logs_count(tmp_path: Path, monkeypatch) -> None:
    """Test that discover_plugins logs the count of discovered plugins."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    _write_file(
        plugins_dir / "test.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: test
print("hi")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    pm.discover_plugins(force_refresh=True)

    assert any("discovered" in m.lower() for m in messages)


def test_discover_plugins_skips_underscore_files(tmp_path: Path) -> None:
    """Test that files starting with underscore are skipped."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "_hidden.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: hidden
print("hi")
""",
    )
    _write_file(
        plugins_dir / ".dotfile.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: dotfile
print("hi")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "hidden" not in plugins
    assert "dotfile" not in plugins


def test_discover_plugins_skips_non_py_sh_files(tmp_path: Path) -> None:
    """Test that non .py/.sh files are skipped."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    (plugins_dir / "readme.txt").write_text("just a readme", encoding="utf-8")
    (plugins_dir / "data.json").write_text("{}", encoding="utf-8")

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert len(plugins) == 0


def test_discover_plugins_path_resolution_failure(tmp_path: Path, monkeypatch) -> None:
    """Test path resolution failure handling."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "test.py",
        """#!/usr/bin/env python3
print("hi")
""",
    )

    # Mock resolve to fail
    original_resolve = Path.resolve

    def mock_resolve(self, strict=False):
        if "test.py" in str(self):
            raise OSError("Resolution failed")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", mock_resolve)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # Plugin should be skipped due to resolution failure
    assert "test" not in plugins
    assert any("resolution failure" in m.lower() for m in messages)


def test_non_absolute_path_in_plugin_dirs_ignored(tmp_path: Path, monkeypatch) -> None:
    """Test that non-absolute paths in LAZYSSH_PLUGIN_DIRS are ignored."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Set relative paths in env
    monkeypatch.setenv("LAZYSSH_PLUGIN_DIRS", "relative/path:another/relative")

    pm = PluginManager(plugins_dir=plugins_dir)
    paths = pm._get_search_paths()

    # Neither relative path should be in the list
    assert not any("relative" in str(p) for p in paths)


def test_validation_file_not_exists(tmp_path: Path) -> None:
    """Test validation when file doesn't exist."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    pm = PluginManager(plugins_dir=plugins_dir)

    # Try to validate a non-existent file
    errors: list[str] = []
    warnings: list[str] = []
    result = pm._validate_plugin(tmp_path / "nonexistent.py", "python", errors, warnings)

    assert result is False
    assert "does not exist" in errors[0].lower()


def test_shell_plugin_not_executable(tmp_path: Path, monkeypatch) -> None:
    """Test shell plugin that is not executable."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "noexec.sh"
    plugin_path.write_text(
        """#!/bin/bash
echo "hi"
""",
        encoding="utf-8",
    )
    # Remove execute bit
    plugin_path.chmod(0o644)

    # Prevent PluginManager from adding exec bit
    original_chmod = Path.chmod

    def mock_chmod(self, mode):
        if "noexec.sh" in str(self):
            return None  # Do nothing
        return original_chmod(self, mode)

    monkeypatch.setattr(Path, "chmod", mock_chmod)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    assert "noexec" in plugins
    assert plugins["noexec"].is_valid is False
    assert any("not executable" in e.lower() for e in plugins["noexec"].validation_errors)


def test_shell_plugin_shebang_check_failure(tmp_path: Path, monkeypatch) -> None:
    """Test shell plugin shebang check failure."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "checkfail.sh"
    plugin_path.write_text(
        """#!/bin/bash
echo "hi"
""",
        encoding="utf-8",
    )
    plugin_path.chmod(0o755)

    # Mock open to fail for shebang check
    original_open = open

    def mock_open(path, *args, **kwargs):
        if "checkfail.sh" in str(path) and "rb" in str(args):
            raise OSError("Cannot read")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # Should fail validation
    assert "checkfail" in plugins
    assert plugins["checkfail"].is_valid is False
    assert any("shebang" in e.lower() for e in plugins["checkfail"].validation_errors)


def test_execute_plugin_not_found(tmp_path: Path) -> None:
    """Test executing a plugin that doesn't exist."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("nonexistent", conn)

    assert success is False
    assert "not found" in output.lower()
    assert elapsed == 0.0


def test_execute_plugin_invalid(tmp_path: Path) -> None:
    """Test executing an invalid plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "invalid.sh"
    plugin_path.write_text("echo hi", encoding="utf-8")  # No shebang, not executable

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("invalid", conn)

    assert success is False
    assert "invalid" in output.lower()
    assert elapsed == 0.0


def test_execute_plugin_shell(tmp_path: Path) -> None:
    """Test executing a shell plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "shelltest.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: shelltest
echo "from shell"
""",
    )
    plugin_path.chmod(0o755)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("shelltest", conn)

    assert success is True
    assert "from shell" in output


def test_execute_plugin_with_args(tmp_path: Path) -> None:
    """Test executing a plugin with arguments."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "argstest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: argstest
import sys
print(f"args: {sys.argv[1:]}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("argstest", conn, args=["arg1", "arg2"])

    assert success is True
    assert "arg1" in output
    assert "arg2" in output


def test_execute_plugin_captures_stderr(tmp_path: Path) -> None:
    """Test that stderr is captured."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "stderrtest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: stderrtest
import sys
print("stdout output")
print("stderr output", file=sys.stderr)
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("stderrtest", conn)

    assert success is True
    assert "stdout output" in output
    assert "stderr output" in output


def test_execute_plugin_exception(tmp_path: Path, monkeypatch) -> None:
    """Test exception handling during plugin execution."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "exctest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: exctest
print("hi")
""",
    )

    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            pass

        def error(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    # Mock subprocess.Popen to raise exception
    def mock_popen(*args, **kwargs):
        raise OSError("Execution failed")

    monkeypatch.setattr("subprocess.Popen", mock_popen)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("exctest", conn)

    assert success is False
    assert "failed to execute" in output.lower()
    assert any("failed" in m.lower() for m in messages)


def test_execute_plugin_with_identity_file(tmp_path: Path) -> None:
    """Test that identity file is passed to plugin env."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "envcheck.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: envcheck
import os
print(f"SSH_KEY={os.environ.get('LAZYSSH_SSH_KEY', 'not set')}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(
        host="1.2.3.4",
        port=22,
        username="test",
        socket_path="/tmp/test",
        identity_file="~/.ssh/id_rsa",
    )

    success, output, elapsed = pm.execute_plugin("envcheck", conn)

    assert success is True
    assert "~/.ssh/id_rsa" in output


def test_execute_plugin_with_shell(tmp_path: Path) -> None:
    """Test that shell is passed to plugin env."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "shellcheck.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: shellcheck
import os
print(f"SHELL={os.environ.get('LAZYSSH_SHELL', 'not set')}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(
        host="1.2.3.4",
        port=22,
        username="test",
        socket_path="/tmp/test",
        shell="/bin/zsh",
    )

    success, output, elapsed = pm.execute_plugin("shellcheck", conn)

    assert success is True
    assert "/bin/zsh" in output


def test_get_plugin(tmp_path: Path) -> None:
    """Test get_plugin method."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "gettest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: gettest
print("hi")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)

    # Get existing plugin
    plugin = pm.get_plugin("gettest")
    assert plugin is not None
    assert plugin.name == "gettest"

    # Get non-existent plugin
    plugin = pm.get_plugin("nonexistent")
    assert plugin is None


def test_execute_plugin_streaming_not_found(tmp_path: Path) -> None:
    """Test streaming execution of non-existent plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("nonexistent", conn))

    assert len(chunks) == 1
    assert chunks[0][0] == "stderr"
    assert "not found" in chunks[0][1].lower()


def test_execute_plugin_streaming_invalid(tmp_path: Path) -> None:
    """Test streaming execution of invalid plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "invalid.sh"
    plugin_path.write_text("echo hi", encoding="utf-8")  # No shebang, not executable

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("invalid", conn))

    assert len(chunks) == 1
    assert chunks[0][0] == "stderr"
    assert "invalid" in chunks[0][1].lower()


def test_execute_plugin_streaming_with_callback(tmp_path: Path) -> None:
    """Test streaming execution with callback."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "callback.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: callback
print("line 1")
print("line 2")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    received: list[tuple[str, str]] = []

    def on_chunk(chunk: tuple[str, str]) -> None:
        received.append(chunk)

    # When using callback, nothing is yielded
    chunks = list(pm.execute_plugin_streaming("callback", conn, on_chunk=on_chunk))

    assert len(chunks) == 0
    assert len(received) >= 2


def test_execute_plugin_streaming_exception(tmp_path: Path, monkeypatch) -> None:
    """Test streaming execution exception handling."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "excstream.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: excstream
print("hi")
""",
    )

    # Mock subprocess.Popen to raise exception
    def mock_popen(*args, **kwargs):
        raise OSError("Execution failed")

    monkeypatch.setattr("subprocess.Popen", mock_popen)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("excstream", conn))

    assert len(chunks) >= 1
    assert any("failed" in c[1].lower() for c in chunks)


def test_execute_plugin_streaming_shell(tmp_path: Path) -> None:
    """Test streaming execution of shell plugin."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "stream_shell.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: stream_shell
echo "shell output"
""",
    )
    plugin_path.chmod(0o755)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("stream_shell", conn))

    assert any("shell output" in c[1] for c in chunks if c[0] == "stdout")


def test_plugin_type_inference_from_mock(tmp_path: Path, monkeypatch) -> None:
    """Test plugin_type inference when not available from metadata."""

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Create a mock plugin without plugin_type attribute
    class MockPlugin:
        def __init__(self):
            self.name = "mock"
            self.file_path = plugins_dir / "mock.py"
            self.is_valid = True
            self.validation_errors = []

    # Write actual plugin file
    _write_file(
        plugins_dir / "mock.py",
        """#!/usr/bin/env python3
print("from mock")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)

    # Mock get_plugin to return our mock
    mock_plugin = MockPlugin()
    monkeypatch.setattr(pm, "get_plugin", lambda name: mock_plugin if name == "mock" else None)

    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("mock", conn)

    assert success is True
    assert "from mock" in output


def test_init_enforces_exec_bit_failure(tmp_path: Path, monkeypatch) -> None:
    """Test that init logs when it fails to enforce exec bit."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "test.py"
    plugin_path.write_text("#!/usr/bin/env python3\nprint('hi')\n", encoding="utf-8")

    # Mock chmod to fail
    original_chmod = Path.chmod

    def mock_chmod(self, mode):
        if "test.py" in str(self):
            raise PermissionError("Cannot chmod")
        return original_chmod(self, mode)

    monkeypatch.setattr(Path, "chmod", mock_chmod)

    # Should not raise
    PluginManager(plugins_dir=plugins_dir)

    assert any("failed to enforce exec bit" in m.lower() for m in messages)


def test_execute_plugin_debug_logging(tmp_path: Path, monkeypatch) -> None:
    """Test that execute_plugin logs debug messages."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

        def error(self, msg, *args):
            pass

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "logtest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: logtest
print("hi")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    pm.execute_plugin("logtest", conn)

    assert any("executing" in m.lower() for m in messages)
    assert any("completed" in m.lower() for m in messages)


def test_validate_plugin_repair_exec_bit_logging(tmp_path: Path, monkeypatch) -> None:
    """Test that validate_plugin logs when it repairs exec bit."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Create PluginManager first (with empty dir), then add plugin
    pm = PluginManager(plugins_dir=plugins_dir)

    # Now add a plugin file without exec bit - won't be auto-fixed by init
    plugin_path = plugins_dir / "repair.py"
    plugin_path.write_text(
        """#!/usr/bin/env python3
print("hi")
""",
        encoding="utf-8",
    )
    plugin_path.chmod(0o644)  # No exec bit

    pm.discover_plugins(force_refresh=True)

    assert any("repaired" in m.lower() for m in messages)


def test_streaming_not_found_with_callback(tmp_path: Path) -> None:
    """Test streaming not found with callback."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    received: list[tuple[str, str]] = []

    def on_chunk(chunk: tuple[str, str]) -> None:
        received.append(chunk)

    # Nothing yielded when using callback
    chunks = list(pm.execute_plugin_streaming("nonexistent", conn, on_chunk=on_chunk))

    assert len(chunks) == 0
    assert len(received) == 1
    assert "not found" in received[0][1].lower()


def test_streaming_invalid_with_callback(tmp_path: Path) -> None:
    """Test streaming invalid plugin with callback."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "invalid2.sh"
    plugin_path.write_text("echo hi", encoding="utf-8")

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    received: list[tuple[str, str]] = []

    def on_chunk(chunk: tuple[str, str]) -> None:
        received.append(chunk)

    list(pm.execute_plugin_streaming("invalid2", conn, on_chunk=on_chunk))

    assert len(received) == 1
    assert "invalid" in received[0][1].lower()


def test_streaming_exception_with_callback(tmp_path: Path, monkeypatch) -> None:
    """Test streaming exception with callback."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "excstream2.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: excstream2
print("hi")
""",
    )

    def mock_popen(*args, **kwargs):
        raise OSError("Execution failed")

    monkeypatch.setattr("subprocess.Popen", mock_popen)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    received: list[tuple[str, str]] = []

    def on_chunk(chunk: tuple[str, str]) -> None:
        received.append(chunk)

    list(pm.execute_plugin_streaming("excstream2", conn, on_chunk=on_chunk))

    assert len(received) >= 1
    assert any("failed" in r[1].lower() for r in received)


def test_streaming_debug_logging(tmp_path: Path, monkeypatch) -> None:
    """Test streaming debug logging."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

        def error(self, msg, *args):
            pass

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "streamlog.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: streamlog
print("hi")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    list(pm.execute_plugin_streaming("streamlog", conn))

    assert any("streaming" in m.lower() for m in messages)
    assert any("finished" in m.lower() for m in messages)


def test_columns_env_variable(tmp_path: Path) -> None:
    """Test that COLUMNS is set from terminal size."""
    from unittest import mock

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "coltest.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: coltest
import os
print(f"COLUMNS={os.environ.get('COLUMNS', 'not set')}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    # Use mock.patch context manager to scope the mock tightly around execute_plugin,
    # preventing pytest-sugar from seeing it during test report rendering.
    with mock.patch("shutil.get_terminal_size", return_value=os.terminal_size((120, 40))):
        success, output, elapsed = pm.execute_plugin("coltest", conn)

    assert success is True
    assert "COLUMNS=120" in output


def test_columns_env_variable_oserror(tmp_path: Path) -> None:
    """Test COLUMNS when get_terminal_size raises OSError."""
    from unittest import mock

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "colerr.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: colerr
import os
print(f"COLUMNS={os.environ.get('COLUMNS', 'not set')}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    # Use mock.patch to scope the mock tightly around only execute_plugin,
    # preventing pytest-sugar from seeing it during test report rendering.
    with mock.patch("shutil.get_terminal_size", side_effect=OSError("No terminal")):
        success, output, elapsed = pm.execute_plugin("colerr", conn)

    assert success is True
    # COLUMNS should not be set when terminal size fails
    assert "COLUMNS=not set" in output


def test_plugin_manager_default_plugins_dir() -> None:
    """Test PluginManager with no plugins_dir uses default."""
    pm = PluginManager()
    # Default should be the plugins directory in the package
    assert "plugins" in str(pm.plugins_dir)


def test_path_is_relative_to_failure(tmp_path: Path, monkeypatch) -> None:
    """Test path resolution when is_relative_to raises exception."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "test.py",
        """#!/usr/bin/env python3
print("hi")
""",
    )

    # Create a symbolic link pointing outside the base directory
    target = tmp_path / "outside" / "target.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        """#!/usr/bin/env python3
# PLUGIN_NAME: outside
print("outside")
""",
        encoding="utf-8",
    )
    target.chmod(0o755)

    link = plugins_dir / "link.py"
    link.symlink_to(target)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # The symlink pointing outside should be skipped
    assert "outside" not in plugins
    assert any("outside base dir" in m.lower() for m in messages)


def test_empty_string_in_plugin_dirs(tmp_path: Path, monkeypatch) -> None:
    """Test that empty strings in LAZYSSH_PLUGIN_DIRS are skipped."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    # Set env with empty strings
    monkeypatch.setenv("LAZYSSH_PLUGIN_DIRS", "::/tmp/valid:")

    pm = PluginManager(plugins_dir=plugins_dir)
    paths = pm._get_search_paths()

    # Only valid paths should be included (not empty strings)
    assert not any(str(p) == "" for p in paths)


def test_streaming_with_args(tmp_path: Path) -> None:
    """Test streaming execution with arguments."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "streamargs.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: streamargs
import sys
print(f"args: {sys.argv[1:]}")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("streamargs", conn, args=["one", "two"]))

    assert any("one" in c[1] for c in chunks if c[0] == "stdout")
    assert any("two" in c[1] for c in chunks if c[0] == "stdout")


def test_streaming_shell_with_args(tmp_path: Path) -> None:
    """Test streaming shell plugin with arguments."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "streamshellargs.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: streamshellargs
echo "args: $@"
""",
    )
    plugin_path.chmod(0o755)

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("streamshellargs", conn, args=["x", "y"]))

    assert any("x" in c[1] or "y" in c[1] for c in chunks)


def test_streaming_stderr_output(tmp_path: Path) -> None:
    """Test streaming captures stderr."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "streamstderr.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: streamstderr
import sys
print("stdout line", flush=True)
print("stderr line", file=sys.stderr, flush=True)
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("streamstderr", conn))

    stdout_lines = [c[1] for c in chunks if c[0] == "stdout"]
    stderr_lines = [c[1] for c in chunks if c[0] == "stderr"]

    assert any("stdout line" in line for line in stdout_lines)
    assert any("stderr line" in line for line in stderr_lines)


def test_resolve_base_exception(tmp_path: Path, monkeypatch) -> None:
    """Test when resolving base path raises an exception."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "test.py",
        """#!/usr/bin/env python3
print("hi")
""",
    )

    # Mock resolve to fail for base path
    original_resolve = Path.resolve
    call_count = [0]

    def mock_resolve(self, strict=False):
        call_count[0] += 1
        # Fail on first call (base path resolution)
        if call_count[0] == 1 and str(self).endswith("plugins"):
            raise OSError("Cannot resolve base")
        return original_resolve(self, strict=strict)

    monkeypatch.setattr(Path, "resolve", mock_resolve)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # Should still work, using unresolved path
    assert "test" in plugins


def test_is_relative_to_exception(tmp_path: Path, monkeypatch) -> None:
    """Test is_relative_to raising exception."""
    messages = []

    class DummyLogger:
        def debug(self, msg, *args):
            messages.append(msg % args if args else msg)

    monkeypatch.setattr("lazyssh.plugin_manager.APP_LOGGER", DummyLogger(), raising=False)

    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "test.py",
        """#!/usr/bin/env python3
print("hi")
""",
    )

    # Mock is_relative_to to raise exception
    original_is_relative_to = Path.is_relative_to

    def mock_is_relative_to(self, other):
        if "test.py" in str(self):
            raise ValueError("Cannot compare")
        return original_is_relative_to(self, other)

    monkeypatch.setattr(Path, "is_relative_to", mock_is_relative_to)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)

    # The plugin should be skipped due to comparison failure
    assert "test" not in plugins
    assert any("outside base dir" in m.lower() for m in messages)


def test_plugin_type_none_fallback_python(tmp_path: Path) -> None:
    """Test plugin_type fallback when plugin_type attribute is None for Python file."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "notype.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: notype
print("no type defined")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    # The plugin should still work with type inference
    success, output, exec_time = pm.execute_plugin("notype", conn)
    assert success
    assert "no type defined" in output


def test_plugin_type_none_fallback_shell(tmp_path: Path) -> None:
    """Test plugin_type fallback when plugin_type attribute is None for shell file."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "notypesh.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: notypesh
echo "shell no type"
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, exec_time = pm.execute_plugin("notypesh", conn)
    assert success
    assert "shell no type" in output


def test_streaming_yields_remaining_output(tmp_path: Path) -> None:
    """Test streaming execution yields remaining stdout/stderr after process ends."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "flushout.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: flushout
import sys
# Print to both stdout and stderr without newlines at end
sys.stdout.write("stdout remaining")
sys.stdout.flush()
sys.stderr.write("stderr remaining")
sys.stderr.flush()
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("flushout", conn))

    stdout_content = "".join(c[1] for c in chunks if c[0] == "stdout")
    stderr_content = "".join(c[1] for c in chunks if c[0] == "stderr")

    assert "stdout remaining" in stdout_content
    assert "stderr remaining" in stderr_content


def test_streaming_drain_remaining_with_callback(tmp_path: Path) -> None:
    """Test streaming drains remaining output with callback."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    _write_file(
        plugins_dir / "draincb.py",
        """#!/usr/bin/env python3
# PLUGIN_NAME: draincb
import sys
# Write without newline to test drain behavior
sys.stdout.write("stdout_drain")
sys.stderr.write("stderr_drain")
""",
    )

    pm = PluginManager(plugins_dir=plugins_dir)
    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    received: list[tuple[str, str]] = []

    def on_chunk(chunk: tuple[str, str]) -> None:
        received.append(chunk)

    list(pm.execute_plugin_streaming("draincb", conn, on_chunk=on_chunk))

    stdout_content = "".join(c[1] for c in received if c[0] == "stdout")
    stderr_content = "".join(c[1] for c in received if c[0] == "stderr")

    assert "stdout_drain" in stdout_content
    assert "stderr_drain" in stderr_content


def test_execute_plugin_no_plugin_type_shell(tmp_path: Path, monkeypatch) -> None:
    """Test execute_plugin with shell file and no plugin_type attribute."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "notypeshell.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: notypeshell
echo "shell plugin"
""",
    )

    # Create a mock plugin with no plugin_type attribute
    class MockPlugin:
        def __init__(self):
            self.name = "notypeshell"
            self.file_path = plugin_path
            self.is_valid = True
            self.validation_errors = []

    pm = PluginManager(plugins_dir=plugins_dir)
    mock_plugin = MockPlugin()
    monkeypatch.setattr(
        pm, "get_plugin", lambda name: mock_plugin if name == "notypeshell" else None
    )

    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    success, output, elapsed = pm.execute_plugin("notypeshell", conn)

    assert success is True
    assert "shell plugin" in output


def test_streaming_shell_no_plugin_type(tmp_path: Path, monkeypatch) -> None:
    """Test streaming shell plugin without plugin_type attribute."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    plugin_path = plugins_dir / "noattrsh.sh"
    _write_file(
        plugin_path,
        """#!/bin/bash
# PLUGIN_NAME: noattrsh
echo "shell no attr"
""",
    )

    # Create a mock plugin without plugin_type attribute
    class MockPlugin:
        def __init__(self):
            self.name = "noattrsh"
            self.file_path = plugin_path
            self.is_valid = True
            self.validation_errors = []

    pm = PluginManager(plugins_dir=plugins_dir)
    mock_plugin = MockPlugin()
    monkeypatch.setattr(pm, "get_plugin", lambda name: mock_plugin if name == "noattrsh" else None)

    conn = SSHConnection(host="1.2.3.4", port=22, username="test", socket_path="/tmp/test")

    chunks = list(pm.execute_plugin_streaming("noattrsh", conn))

    stdout_content = "".join(c[1] for c in chunks if c[0] == "stdout")
    assert "shell no attr" in stdout_content
