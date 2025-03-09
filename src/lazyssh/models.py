"""Models and shared types for LazySSH"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Tunnel:
    id: str
    type: str  # 'forward' or 'reverse'
    local_port: int
    remote_host: str
    remote_port: int
    active: bool = True
    connection_name: str = ""


@dataclass
class SSHConnection:
    host: str
    port: int
    username: str
    socket_path: str
    dynamic_port: Optional[int] = None
    identity_file: Optional[str] = None
    tunnels: List[Tunnel] = field(default_factory=list)
    _next_tunnel_id: int = 1

    def __post_init__(self):
        # Ensure socket path is in /tmp/
        if not self.socket_path.startswith("/tmp/"):
            name = os.path.basename(self.socket_path)
            self.socket_path = f"/tmp/{name}"

        # Expand user paths (like ~)
        self.socket_path = os.path.expanduser(self.socket_path)

        # Create the downloads directory structure
        self._create_connection_dirs()

    def _create_connection_dirs(self):
        """Create the directory structure for this connection"""
        # Get the connection name from the socket path
        conn_name = os.path.basename(self.socket_path)

        # Create connection download directory
        self.connection_dir = f"/tmp/lazyssh/{conn_name}.d"
        os.makedirs(self.connection_dir, exist_ok=True)
        os.chmod(self.connection_dir, 0o700)

        # Create downloads directory
        self.downloads_dir = f"{self.connection_dir}/downloads"
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.chmod(self.downloads_dir, 0o700)

    @property
    def conn_name(self) -> str:
        """Get the connection name"""
        return os.path.basename(self.socket_path)

    def add_tunnel(
        self, local_port: int, remote_host: str, remote_port: int, is_reverse: bool = False
    ) -> Tunnel:
        """Add a new tunnel with a sequential identifier"""
        tunnel = Tunnel(
            id=str(self._next_tunnel_id),
            type="reverse" if is_reverse else "forward",
            local_port=local_port,
            remote_host=remote_host,
            remote_port=remote_port,
            connection_name=os.path.basename(self.socket_path),
        )
        self.tunnels.append(tunnel)
        self._next_tunnel_id += 1
        return tunnel

    def remove_tunnel(self, tunnel_id: str) -> bool:
        """Remove a tunnel by its unique identifier"""
        for i, tunnel in enumerate(self.tunnels):
            if tunnel.id == tunnel_id:
                self.tunnels.pop(i)
                return True
        return False

    def get_tunnel(self, tunnel_id: str) -> Optional[Tunnel]:
        """Get a tunnel by its unique identifier"""
        for tunnel in self.tunnels:
            if tunnel.id == tunnel_id:
                return tunnel
        return None
