"""Models and shared types for LazySSH"""
from dataclasses import dataclass
from typing import Dict, Optional, List
import os

@dataclass
class SSHConnection:
    host: str
    port: int
    username: str
    socket_path: str
    dynamic_port: Optional[int] = None
    identity_file: Optional[str] = None
    tunnels: List[Dict] = None

    def __post_init__(self):
        self.tunnels = self.tunnels or []
        # Ensure socket path is in /tmp/lazyssh/
        if not self.socket_path.startswith('/tmp/lazyssh/'):
            name = os.path.basename(self.socket_path)
            self.socket_path = f'/tmp/lazyssh/{name}'
        self.socket_path = os.path.expanduser(self.socket_path)