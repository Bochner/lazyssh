"""Tests for models module - SSHConnection, Tunnel, and related dataclasses."""

from pathlib import Path
from unittest import mock

import pytest

from lazyssh.models import SSHConnection, Tunnel


class TestTunnel:
    """Tests for the Tunnel dataclass."""

    def test_tunnel_creation_defaults(self) -> None:
        """Test that Tunnel can be created with required fields and defaults."""
        tunnel = Tunnel(
            id="1",
            type="forward",
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
        )
        assert tunnel.id == "1"
        assert tunnel.type == "forward"
        assert tunnel.local_port == 8080
        assert tunnel.remote_host == "localhost"
        assert tunnel.remote_port == 80
        assert tunnel.active is True
        assert tunnel.connection_name == ""

    def test_tunnel_creation_with_all_fields(self) -> None:
        """Test Tunnel creation with all fields specified."""
        tunnel = Tunnel(
            id="2",
            type="reverse",
            local_port=9090,
            remote_host="example.com",
            remote_port=443,
            active=False,
            connection_name="my-conn",
        )
        assert tunnel.id == "2"
        assert tunnel.type == "reverse"
        assert tunnel.local_port == 9090
        assert tunnel.remote_host == "example.com"
        assert tunnel.remote_port == 443
        assert tunnel.active is False
        assert tunnel.connection_name == "my-conn"


class TestSSHConnection:
    """Tests for the SSHConnection dataclass."""

    def test_ssh_connection_creation(self, tmp_path: Path) -> None:
        """Test basic SSHConnection creation."""
        socket_path = str(tmp_path / "testsock")
        conn = SSHConnection(
            host="192.168.1.1",
            port=22,
            username="testuser",
            socket_path=socket_path,
        )
        assert conn.host == "192.168.1.1"
        assert conn.port == 22
        assert conn.username == "testuser"
        # Socket path should be moved to /tmp/
        assert conn.socket_path.startswith("/tmp/")
        assert conn.dynamic_port is None
        assert conn.identity_file is None
        assert conn.shell is None
        assert conn.no_term is False
        assert conn.tunnels == []
        assert conn._next_tunnel_id == 1

    def test_socket_path_moved_to_tmp(self) -> None:
        """Test that socket paths not in /tmp are moved there."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/home/user/mysock",
        )
        # Socket should be moved to /tmp/
        assert conn.socket_path == "/tmp/mysock"

    def test_socket_path_in_tmp_preserved(self) -> None:
        """Test that socket paths already in /tmp are preserved."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/already-in-tmp",
        )
        assert conn.socket_path == "/tmp/already-in-tmp"

    def test_socket_path_with_tilde_expansion(self) -> None:
        """Test that ~ in socket paths is expanded when at start of path."""
        # When path starts with ~, expanduser expands it
        # But since it doesn't start with /tmp/, it gets moved to /tmp/
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="~/mysock",
        )
        # The path should be moved to /tmp/ and should contain the socket name
        assert conn.socket_path == "/tmp/mysock"

    def test_connection_dirs_created(self) -> None:
        """Test that connection directories are created on init."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/dirtest",
        )

        # Check connection_dir is set
        assert conn.connection_dir == "/tmp/lazyssh/dirtest.d"
        assert Path(conn.connection_dir).exists()
        assert Path(conn.connection_dir).stat().st_mode & 0o777 == 0o700

        # Check downloads_dir is set
        assert conn.downloads_dir == "/tmp/lazyssh/dirtest.d/downloads"
        assert Path(conn.downloads_dir).exists()
        assert Path(conn.downloads_dir).stat().st_mode & 0o777 == 0o700

        # Check uploads_dir is set
        assert conn.uploads_dir == "/tmp/lazyssh/dirtest.d/uploads"
        assert Path(conn.uploads_dir).exists()
        assert Path(conn.uploads_dir).stat().st_mode & 0o777 == 0o700

    def test_conn_name_property(self) -> None:
        """Test the conn_name property returns socket name."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/my-connection-name",
        )
        assert conn.conn_name == "my-connection-name"

    def test_add_tunnel_forward(self) -> None:
        """Test adding a forward tunnel."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/tunnel-test",
        )

        tunnel = conn.add_tunnel(
            local_port=8080,
            remote_host="localhost",
            remote_port=80,
            is_reverse=False,
        )

        assert tunnel.id == "1"
        assert tunnel.type == "forward"
        assert tunnel.local_port == 8080
        assert tunnel.remote_host == "localhost"
        assert tunnel.remote_port == 80
        assert tunnel.connection_name == "tunnel-test"
        assert len(conn.tunnels) == 1
        assert conn._next_tunnel_id == 2

    def test_add_tunnel_reverse(self) -> None:
        """Test adding a reverse tunnel."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/reverse-tunnel-test",
        )

        tunnel = conn.add_tunnel(
            local_port=9090,
            remote_host="example.com",
            remote_port=443,
            is_reverse=True,
        )

        assert tunnel.id == "1"
        assert tunnel.type == "reverse"
        assert tunnel.local_port == 9090
        assert tunnel.remote_host == "example.com"
        assert tunnel.remote_port == 443

    def test_add_multiple_tunnels(self) -> None:
        """Test adding multiple tunnels increments IDs."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/multi-tunnel-test",
        )

        tunnel1 = conn.add_tunnel(8080, "localhost", 80)
        tunnel2 = conn.add_tunnel(9090, "localhost", 90)
        tunnel3 = conn.add_tunnel(10000, "localhost", 100)

        assert tunnel1.id == "1"
        assert tunnel2.id == "2"
        assert tunnel3.id == "3"
        assert len(conn.tunnels) == 3
        assert conn._next_tunnel_id == 4

    def test_remove_tunnel_success(self) -> None:
        """Test removing an existing tunnel."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/remove-tunnel-test",
        )

        conn.add_tunnel(8080, "localhost", 80)
        tunnel2 = conn.add_tunnel(9090, "localhost", 90)
        conn.add_tunnel(10000, "localhost", 100)

        result = conn.remove_tunnel(tunnel2.id)

        assert result is True
        assert len(conn.tunnels) == 2
        assert all(t.id != "2" for t in conn.tunnels)

    def test_remove_tunnel_not_found(self) -> None:
        """Test removing a non-existent tunnel returns False."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/remove-notfound-test",
        )

        conn.add_tunnel(8080, "localhost", 80)

        result = conn.remove_tunnel("999")

        assert result is False
        assert len(conn.tunnels) == 1

    def test_get_tunnel_success(self) -> None:
        """Test getting an existing tunnel by ID."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/get-tunnel-test",
        )

        conn.add_tunnel(8080, "localhost", 80)
        tunnel2 = conn.add_tunnel(9090, "localhost", 90)

        found = conn.get_tunnel(tunnel2.id)

        assert found is not None
        assert found.id == tunnel2.id
        assert found.local_port == 9090

    def test_get_tunnel_not_found(self) -> None:
        """Test getting a non-existent tunnel returns None."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/get-notfound-test",
        )

        conn.add_tunnel(8080, "localhost", 80)

        found = conn.get_tunnel("999")

        assert found is None

    def test_ssh_connection_with_optional_fields(self) -> None:
        """Test SSHConnection with all optional fields set."""
        conn = SSHConnection(
            host="server.example.com",
            port=2222,
            username="admin",
            socket_path="/tmp/full-conn-test",
            dynamic_port=1080,
            identity_file="~/.ssh/id_ed25519",
            shell="/bin/zsh",
            no_term=True,
        )

        assert conn.host == "server.example.com"
        assert conn.port == 2222
        assert conn.username == "admin"
        assert conn.dynamic_port == 1080
        assert conn.identity_file == "~/.ssh/id_ed25519"
        assert conn.shell == "/bin/zsh"
        assert conn.no_term is True

    def test_connection_dir_permissions_set_correctly(self) -> None:
        """Test that all connection directories have 0700 permissions."""
        conn = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/perm-test",
        )

        # Check all directories have correct permissions
        for dir_path in [conn.connection_dir, conn.downloads_dir, conn.uploads_dir]:
            mode = Path(dir_path).stat().st_mode & 0o777
            assert mode == 0o700, f"Directory {dir_path} has mode {oct(mode)}, expected 0o700"

    def test_tunnels_default_factory(self) -> None:
        """Test that tunnels list is not shared between instances."""
        conn1 = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/factory-test1",
        )
        conn2 = SSHConnection(
            host="localhost",
            port=22,
            username="user",
            socket_path="/tmp/factory-test2",
        )

        conn1.add_tunnel(8080, "localhost", 80)

        assert len(conn1.tunnels) == 1
        assert len(conn2.tunnels) == 0

    def test_mkdir_error_handling(self) -> None:
        """Test that directory creation errors are handled gracefully."""
        with mock.patch.object(Path, "mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            with pytest.raises(PermissionError):
                SSHConnection(
                    host="localhost",
                    port=22,
                    username="user",
                    socket_path="/tmp/mkdir-error-test",
                )
