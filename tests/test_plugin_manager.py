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
    assert any("shebang" in warning.lower() for warning in meta.validation_warnings)


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
    assert any("executable bit" in warning.lower() for warning in meta.validation_warnings)
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
