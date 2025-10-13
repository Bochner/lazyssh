# LazySSH

A comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface.

![LazySSH](https://raw.githubusercontent.com/Bochner/lazyssh/main/lazyssh.png)

## Overview

LazySSH simplifies SSH connection management with an elegant CLI interface. It helps you manage multiple connections, create tunnels, transfer files, and automate common SSH tasks.

### Key Features

- **Interactive Command Interface**: Smart command mode with tab completion and guided workflows
- **Connection Management**: Handle multiple SSH connections with control sockets
- **Saved Configurations**: Save and reuse connection configurations with TOML-based storage
- **Tunneling**: Create forward and reverse tunnels with simple commands
- **Dynamic Proxy**: Set up SOCKS proxy for secure browsing
- **SCP Mode**: Transfer files securely with rich visualization and progress tracking
- **Terminal Integration**: Open terminal sessions directly with runtime method switching
- **Plugin System**: Extend functionality with custom Python or shell scripts
- **Wizard Workflows**: Guided interactive workflows for complex operations
- **Rich Visual Elements**: Color coding, progress bars, and tree visualizations

## Quick Start

### Installation

```bash
# Install globally
pip install lazyssh

# Or with pipx (recommended)
pipx install lazyssh

# Or install for the current user only
pip install --user lazyssh
```

### Basic Usage

```bash
# Start LazySSH
lazyssh

# Create a new connection
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver

# Create a connection with dynamic SOCKS proxy
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080

# Create a tunnel
lazyssh> tunc myserver l 8080 localhost 80

# Open a terminal
lazyssh> open myserver

# Transfer files (SCP mode)
lazyssh> scp myserver

# Use plugins for automation
lazyssh> plugin list                    # List available plugins
lazyssh> plugin run enumerate myserver  # Run system enumeration

# Use wizard for guided workflows
lazyssh> wizard lazyssh
lazyssh> wizard tunnel

# In SCP mode: visualize remote directory tree
scp myserver:/home/user> tree

# Download files
scp myserver:/home/user> get config.json
```

## Plugin System

LazySSH features an extensible plugin system that allows you to run custom Python or shell scripts through established SSH connections. This enables automation, reconnaissance, and custom workflows without leaving LazySSH.

### Built-in Plugins

#### Enumerate Plugin

Performs comprehensive system enumeration including:
- OS and kernel information
- User accounts and groups
- Network configuration (interfaces, routes, listening ports)
- Running processes and services
- Installed packages (apt/yum/pacman)
- Filesystem information and mounts
- Environment variables
- Scheduled tasks (cron, systemd timers)
- Security configurations (firewall, SELinux/AppArmor)
- System logs
- Hardware information

```bash
lazyssh> plugin run enumerate myserver
```

### Using Plugins

```bash
# List all available plugins
lazyssh> plugin list

# Get detailed information about a plugin
lazyssh> plugin info enumerate

# Run a plugin on an established connection
lazyssh> plugin run <plugin-name> <socket-name>
```

### Creating Custom Plugins

Plugins are simple Python or shell scripts that can execute commands through SSH control sockets. See `src/lazyssh/plugins/README.md` for a comprehensive plugin development guide.

**Quick Example:**

```python
#!/usr/bin/env python3
# PLUGIN_NAME: my-plugin
# PLUGIN_DESCRIPTION: My custom automation script
# PLUGIN_VERSION: 1.0.0

import os
import subprocess
import sys

# LazySSH provides connection info via environment variables
host = os.environ.get("LAZYSSH_HOST")
user = os.environ.get("LAZYSSH_USER")
socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")

# Execute commands on remote host using SSH control socket
cmd = ["ssh", "-S", socket_path, "-o", "ControlMaster=no",
       f"{user}@{host}", "your-command-here"]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
```

Place your plugin in `src/lazyssh/plugins/`, make it executable (`chmod +x`), and it will be automatically discovered.

For detailed plugin development instructions, examples, and best practices, see the [Plugin Development Guide](src/lazyssh/plugins/README.md).

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

### Optional Dependencies

- **Terminator terminal emulator** - For opening terminals in external windows. If not installed, LazySSH will use a native terminal that runs in the current terminal window.

### Platform Support

LazySSH is compatible with:
- **Linux** - Full support
- **macOS** - Full support

**Windows Users:** Windows OpenSSH does not support SSH master mode (`-M` flag) which is required for LazySSH's persistent connection functionality. Windows users should use [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/install) to run LazySSH with full functionality.

## Terminal Methods

LazySSH supports two methods for opening SSH terminal sessions:

### Native Terminal (Default)
The native terminal method runs SSH as a subprocess in your current terminal window. This requires no external dependencies and works out of the box. **Important:** You can exit the SSH session (using `exit` or `Ctrl+D`) and return to LazySSH without closing the SSH connection, allowing you to manage multiple sessions easily.

### Terminator Terminal
If you have Terminator installed, LazySSH can open SSH sessions in new Terminator windows. This is useful if you want to keep multiple terminals open simultaneously.

### Configuration

You can control which terminal method to use either at runtime or via environment variable:

**Runtime configuration (recommended):**
```bash
# From command mode
lazyssh> terminal native      # Set terminal method to native
lazyssh> terminal auto        # Set terminal method to auto
lazyssh> terminal terminator  # Set terminal method to terminator
```

**Environment variable:**
```bash
# Automatically select best available method (default)
# Tries Terminator first, falls back to native
export LAZYSSH_TERMINAL_METHOD=auto

# Force native terminal (runs in current window)
export LAZYSSH_TERMINAL_METHOD=native

# Force Terminator (requires Terminator to be installed)
export LAZYSSH_TERMINAL_METHOD=terminator
```

**Default behavior (auto):**
- If Terminator is installed: Opens terminals in new Terminator windows
- If Terminator is not installed: Uses native terminal in current window
- Falls back gracefully if the preferred method fails

**Features:**
- Native terminal allows returning to LazySSH after exiting the SSH session
- Terminal method can be changed at runtime without restarting LazySSH
- Terminal method is displayed in the SSH connections status table

## Saved Connection Configurations

LazySSH allows you to save connection configurations for quick reuse. Configurations are stored securely in TOML format at `/tmp/lazyssh/connections.conf` with owner-only permissions (600).

### Saving Connections

After creating a successful connection, LazySSH will prompt you to save it:

```bash
lazyssh> lazyssh -ip server.example.com -port 22 -user admin -socket myserver
# After connection succeeds
Save this connection configuration? (y/N): y
Enter config name [myserver]: prod-server
✓ Configuration saved as 'prod-server'
```

Or save manually from command mode:

```bash
lazyssh> save-config prod-server
```

### Using Saved Configurations

**View saved configurations:**
```bash
lazyssh> config
# Displays table of all saved configurations
```

**Connect using a saved configuration:**
```bash
lazyssh> connect prod-server
```

**Delete a saved configuration:**
```bash
lazyssh> delete-config prod-server
```

### Configuration File Format

Configurations are stored in TOML format at `/tmp/lazyssh/connections.conf`:

```toml
[prod-server]
host = "server.example.com"
port = 22
username = "admin"
ssh_key = "/home/user/.ssh/id_rsa"

[dev-server]
host = "192.168.1.100"
port = 2222
username = "developer"
proxy_port = 9050
```

### Security Considerations

- **File Permissions**: Config file is automatically set to mode 600 (owner read/write only)
- **Location**: Files are stored in `/tmp/lazyssh/` which is cleared on system reboot
- **SSH Keys**: Only paths to SSH keys are stored, not the keys themselves
- **Sensitive Data**: Consider using SSH keys instead of password authentication
- **Manual Editing**: You can safely edit the TOML file directly if needed

### CLI Flag

View configurations at startup:

```bash
lazyssh --config
```

Or specify a custom config file path:

```bash
lazyssh --config /path/to/custom/connections.conf
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
