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
- **SCP Mode**: Transfer files securely between local and remote systems with rich visualization
- **Terminal Integration**: Open terminal sessions directly from LazySSH
- **Human-Readable Output**: Sizes and formatting optimized for readability
- **Rich Visual Elements**: Color coding, progress bars, and tree visualizations

## Quick Start

### Installation

```bash
# Install globally
pip install lazyssh
pipx install lazyssh

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
lazyssh> open myserver

# Transfer files (SCP mode)
lazyssh> scp myserver

# In SCP mode: visualize remote directory tree
scp myserver:/home/user> tree

# Download files
scp myserver:/home/user> get config.json
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

### Optional Dependencies

- **Terminator terminal emulator** - For opening terminals in external windows. If not installed, LazySSH will use a native Python terminal that runs in the current terminal window.

### Platform Support

LazySSH is compatible with:
- **Linux** - Full support
- **macOS** - Full support
- **Windows** - Full support (requires OpenSSH for Windows)

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
lazyssh> terminal native    # Set terminal method to native
lazyssh> terminal auto      # Set terminal method to auto
lazyssh> terminal terminator  # Set terminal method to terminator

# From menu mode: Select "8. Change terminal method"
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

**New in this version:**
- Native terminal now allows returning to LazySSH after exiting the SSH session
- Terminal method can be changed at runtime without restarting LazySSH
- Terminal method is displayed in the SSH connections status table

## License

MIT License

## GitHub Project Board

This repository uses GitHub Projects for issue and PR tracking. To use the automated project board features:

### Setting Up Project Board

For detailed setup instructions, see [.github/setup-project-board.md](.github/setup-project-board.md).

Quick setup:
1. Create a new project at: https://github.com/users/YOUR_USERNAME/projects
2. Name it "LazySSH Development" 
3. Configure the Status field with the predefined options
4. Link your repository to the project

### Workflow Automation

The repository includes automated workflows that will:
- Add new issues and PRs to the project board
- Update status based on labels and PR state
- Sync existing items when manually triggered

To manually trigger a sync of all open issues and PRs:
1. Go to Actions → Project Board Automation
2. Click "Run workflow"
3. Check "Sync all open issues and PRs"
4. Click "Run workflow"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
