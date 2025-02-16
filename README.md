# LazySSH

A comprehensive Python-based SSH toolkit for managing SSH connections, tunnels, and remote command execution.

## Components

### 1. pyssh.py
SSH connection manager that provides:
- Customizable SSH connections with control socket support
- Dynamic port forwarding
- Verbosity control
- User-friendly command confirmation

```bash
python pyssh.py -ip TARGET_IP -port PORT -host HOSTNAME -user USERNAME [-v] [-D DYNAMIC_PORT]
```

### 2. sshtun.py
Advanced SSH tunnel manager with features:
- Forward and reverse tunnel creation
- Multiple tunnel management
- SSH control socket tracking
- Interactive CLI interface

Commands:
- `add <path> <user> <ssh_server>`: Add new SSH control socket
- `remove <path>`: Remove SSH control socket
- `l <path> <local_port> <remote_host> <remote_port>`: Create forward tunnel
- `r <path> <local_port> <remote_host> <remote_port>`: Create reverse tunnel
- `kill <tunnel_number>`: Kill specific tunnel
- `list`: List active tunnels
- `sockets`: List active sockets

### 3. sshint.py
Interactive SSH command interface that provides:
- Command history with arrow key support
- Basic system information commands
- Safe command execution through SSH socket

```bash
python sshint.py --socket SOCKET_PATH
```

Available commands:
- `w`: Display logged-in users
- `date`: Show current date/time
- `date -u`: Show UTC date/time
- `id`: Display user/group IDs

## Installation

No installation required. Just clone the repository and ensure you have Python 3.x installed.

```bash
git clone https://github.com/yourusername/lazyssh.git
cd lazyssh
```

## Requirements
- Python 3.x
- SSH client installed on the system
- `readline` module (typically included with Python)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Notes

- Always verify SSH connections and tunnels before use
- Be cautious with control socket permissions
- Review tunnel configurations before implementation
- Use strong authentication methods

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.