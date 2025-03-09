"""Models and shared types for LazySSH"""

import os
from dataclasses import dataclass
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
    tunnels: List[Tunnel] = None
    _next_tunnel_id: int = 1

    def __post_init__(self):
        self.tunnels = self.tunnels or []
        # Ensure socket path is in /tmp/lazyssh/
        if not self.socket_path.startswith("/tmp/lazyssh/"):
            name = os.path.basename(self.socket_path)
            self.socket_path = f"/tmp/lazyssh/{name}"
        self.socket_path = os.path.expanduser(self.socket_path)

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
