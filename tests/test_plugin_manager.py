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


def test_execute_plugin_passes_env_and_captures_output(tmp_path: Path, monkeypatch) -> None:
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
