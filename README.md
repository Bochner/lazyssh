# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

![LazySSH](https://raw.githubusercontent.com/Bochner/lazyssh/main/lazyssh.png)

## Overview

LazySSH simplifies SSH connection management with an elegant CLI interface. It helps you manage multiple connections, create tunnels, transfer files, and automate common SSH tasks.

### Key Features

- **Dual Interface Modes**: Interactive menu mode or command mode with smart tab completion
- **Connection Management**: Handle multiple SSH connections with control sockets
- **Tunneling**: Create forward and reverse tunnels with simple commands
- **Dynamic Proxy**: Set up SOCKS proxy for secure browsing
- **SCP Mode**: Transfer files securely between local and remote systems
- **Terminal Integration**: Open terminal sessions directly from LazySSH
- **Human-Readable Output**: Sizes and formatting optimized for readability

## Quick Start

### Installation

```bash
# Install globally
pip install lazyssh

# Or install for the current user only
pip install --user lazyssh
```

### Basic Usage

```bash
# Start LazySSH in command mode (default)
lazyssh

# Create a new connection
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver

# Create a connection with dynamic SOCKS proxy
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080

# Create a tunnel
lazyssh> tunc myserver l 8080 localhost 80

# Open a terminal
lazyssh> term myserver

# Transfer files (SCP mode)
lazyssh> scp myserver
```

## Documentation

For detailed documentation, please see the [docs directory](docs/):

- [User Guide](docs/user-guide.md): Comprehensive guide to using LazySSH
- [Command Reference](docs/commands.md): Details on all available commands
- [SCP Mode Guide](docs/scp-mode.md): How to use the file transfer capabilities
- [Tunneling Guide](docs/tunneling.md): Creating and managing SSH tunnels
- [Troubleshooting](docs/troubleshooting.md): Common issues and solutions
- [Development Guide](docs/development.md): Information for contributors
- [Publishing Guide](docs/publishing.md): How to publish the package

## Requirements

- Python 3.11+
- OpenSSH client
- Terminator terminal emulator

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
