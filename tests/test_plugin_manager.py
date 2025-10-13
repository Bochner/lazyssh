import os
import stat
from pathlib import Path

from lazyssh.models import SSHConnection
from lazyssh.plugin_manager import PluginManager


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


def test_validation_requires_shebang_and_exec_bit(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)

    # Missing shebang
    bad_path = plugins_dir / "bad.py"
    bad_path.write_text("print('no shebang')\n", encoding="utf-8")
    # Ensure executable bit so validation hits shebang check
    mode = bad_path.stat().st_mode
    bad_path.chmod(mode | stat.S_IXUSR)

    pm = PluginManager(plugins_dir=plugins_dir)
    plugins = pm.discover_plugins(force_refresh=True)
    meta = plugins["bad"]
    assert meta.is_valid is False
    assert any("shebang" in e.lower() for e in meta.validation_errors)


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
