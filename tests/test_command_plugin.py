from pathlib import Path

from lazyssh.command_mode import CommandMode
from lazyssh.models import SSHConnection
from lazyssh.ssh import SSHManager


def _make_connected(manager: SSHManager, name: str = "conn") -> SSHConnection:
    conn = SSHConnection(host="h", port=22, username="u", socket_path=f"/tmp/{name}")
    manager.connections[conn.socket_path] = conn
    return conn


def test_plugin_list_calls_display(monkeypatch):
    manager = SSHManager()
    cm = CommandMode(manager)

    called = {"listed": False}

    def fake_display(plugins):  # type: ignore
        called["listed"] = True

    monkeypatch.setattr("lazyssh.ui.display_plugins", fake_display)

    assert cm.cmd_plugin(["list"]) is True
    assert called["listed"] is True


def test_plugin_info_not_found(monkeypatch):
    manager = SSHManager()
    cm = CommandMode(manager)

    # Force empty discovery
    monkeypatch.setattr(cm.plugin_manager, "discover_plugins", lambda force_refresh=False: {})

    # Capture error via display
    messages = []

    def fake_error(msg):  # type: ignore
        messages.append(msg)

    monkeypatch.setattr("lazyssh.console_instance.display_error", fake_error)

    assert cm.cmd_plugin(["info", "nope"]) is False
    assert any("not found" in m.lower() for m in messages)


def test_plugin_run_executes(monkeypatch):
    manager = SSHManager()
    conn = _make_connected(manager, "abc")
    cm = CommandMode(manager)

    # Mock plugin lookup
    class Meta:
        is_valid = True
        validation_errors = []
        file_path = Path("/bin/echo")
        name = "echo"

    monkeypatch.setattr(cm.plugin_manager, "get_plugin", lambda name: Meta)

    # Mock execute_plugin to avoid actual subprocess execution
    monkeypatch.setattr(
        cm.plugin_manager,
        "execute_plugin",
        lambda plugin_name, connection, args=None: (True, "", 0.1),
    )

    # Ensure subprocess output is displayed without raising
    outputs = []

    def fake_display_output(output, t, success=True):  # type: ignore
        outputs.append(output)

    monkeypatch.setattr("lazyssh.ui.display_plugin_output", fake_display_output)

    # Execute
    assert cm.cmd_plugin(["run", "echo", conn.conn_name]) is True
