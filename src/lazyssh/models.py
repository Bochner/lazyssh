"""Models and shared types for LazySSH"""

from dataclasses import dataclass, field
from pathlib import Path


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
    dynamic_port: int | None = None
    identity_file: str | None = None
    shell: str | None = None
    no_term: bool = False
    tunnels: list[Tunnel] = field(default_factory=list)
    _next_tunnel_id: int = 1

    def __post_init__(self) -> None:
        # Ensure socket path is in /tmp/
        socket_path = Path(self.socket_path)
        if not str(socket_path).startswith("/tmp/"):
            name = socket_path.name
            self.socket_path = f"/tmp/{name}"

        # Expand user paths (like ~)
        self.socket_path = str(Path(self.socket_path).expanduser())

        # Create the downloads directory structure
        self._create_connection_dirs()

    def _create_connection_dirs(self) -> None:
        """Create the directory structure for this connection"""
        # Get the connection name from the socket path
        conn_name = Path(self.socket_path).name

        # Create connection download directory
        self.connection_dir = f"/tmp/lazyssh/{conn_name}.d"
        Path(self.connection_dir).mkdir(parents=True, exist_ok=True)
        Path(self.connection_dir).chmod(0o700)

        # Create downloads directory
        self.downloads_dir = f"{self.connection_dir}/downloads"
        Path(self.downloads_dir).mkdir(parents=True, exist_ok=True)
        Path(self.downloads_dir).chmod(0o700)

        # Create uploads directory
        self.uploads_dir = f"{self.connection_dir}/uploads"
        Path(self.uploads_dir).mkdir(parents=True, exist_ok=True)
        Path(self.uploads_dir).chmod(0o700)

    @property
    def conn_name(self) -> str:
        """Get the connection name"""
        return Path(self.socket_path).name

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
            connection_name=Path(self.socket_path).name,
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

    def get_tunnel(self, tunnel_id: str) -> Tunnel | None:
        """Get a tunnel by its unique identifier"""
        for tunnel in self.tunnels:
            if tunnel.id == tunnel_id:
                return tunnel
        return None
