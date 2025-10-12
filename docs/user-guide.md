# LazySSH User Guide

This guide provides a streamlined introduction to using LazySSH for SSH connection management, tunneling, and file transfers.

## Table of Contents

- [Installation](#installation)
- [Your First Connection](#your-first-connection)
- [Core Workflows](#core-workflows)
- [Saved Connection Configurations](#saved-connection-configurations)
- [Wizard Workflows](#wizard-workflows)
- [Terminal Methods](#terminal-methods)
- [Advanced Features](#advanced-features)

## Installation

### Prerequisites

- Python 3.11 or higher
- OpenSSH client installed

**Optional:**
- Terminator terminal emulator (for opening terminals in separate windows)

### Installation Methods

#### Using pip (Recommended)

```bash
# Install globally
pip install lazyssh

# Or with pipx
pipx install lazyssh

# Or install for current user only
pip install --user lazyssh
```

#### From Source

```bash
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh
pip install -e .
```

### Post-Installation

If you installed with `--user` and encounter "command not found" errors:

```bash
export PATH="$HOME/.local/bin:$PATH"

# Make it permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Your First Connection

Start LazySSH:

```bash
lazyssh
```

Create your first SSH connection:

```bash
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver
```

The `-socket` parameter gives your connection a memorable name for future commands.

View your active connections:

```bash
lazyssh> list
```

Open a terminal to your server:

```bash
lazyssh> open myserver
```

When you're done, close the connection:

```bash
lazyssh> close myserver
```

## Core Workflows

### Managing Connections

**Create with SSH key:**
```bash
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket prod -ssh-key ~/.ssh/id_rsa
```

**Create with SOCKS proxy:**
```bash
# Default port (9050)
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy

# Custom port
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy 8080
```

**List connections:**
```bash
lazyssh> list
```

**Close connection:**
```bash
lazyssh> close myserver
```

### Creating Tunnels

**Forward tunnel** (access remote service locally):
```bash
# Syntax: tunc <connection> l <local_port> <remote_host> <remote_port>
lazyssh> tunc myserver l 8080 localhost 80

# Now access remote port 80 via http://localhost:8080
```

**Reverse tunnel** (expose local service remotely):
```bash
# Syntax: tunc <connection> r <remote_port> <local_host> <local_port>
lazyssh> tunc myserver r 8080 localhost 3000

# Remote users can now access your local port 3000 via remote:8080
```

**Delete tunnel:**
```bash
lazyssh> tund 1  # Use tunnel ID from 'list' command
```

### File Transfers (SCP Mode)

Enter SCP mode for a connection:

```bash
lazyssh> scp myserver
```

Once in SCP mode:

```bash
# Navigate remote directories
scp myserver:/home/user> cd /var/log
scp myserver:/var/log> ls

# Visualize directory structure
scp myserver:/var/log> tree

# Download a file
scp myserver:/var/log> get app.log

# Download multiple files
scp myserver:/var/log> mget *.log

# Upload a file
scp myserver:/var/log> put local-file.txt

# Change local directory
scp myserver:/var/log> lcd ~/Downloads

# Exit SCP mode
scp myserver:/var/log> exit
```

## Saved Connection Configurations

LazySSH lets you save connection configurations for quick reuse. This eliminates repetitive typing and helps you manage multiple servers efficiently.

### Saving a Configuration

**Option 1: Save after connection (recommended)**

When you successfully create a connection, LazySSH will prompt you:

```bash
lazyssh> lazyssh -ip server.example.com -port 22 -user admin -socket myserver
# After connection succeeds
Save this connection configuration? (y/N): y
Enter config name [myserver]: prod-server
✓ Configuration saved as 'prod-server'
```

**Option 2: Save manually**

Save the current/last connection:

```bash
lazyssh> save-config prod-server
```

### Viewing Saved Configurations

List all saved configurations:

```bash
lazyssh> config
# or
lazyssh> configs
```

This displays a table with:
- Configuration name
- Host
- Username
- Port
- SSH key path
- Shell preference
- Proxy port (if any)
- No-term flag

**View at startup:**

```bash
lazyssh --config
```

### Connecting with Saved Configurations

Connect using a saved configuration:

```bash
lazyssh> connect prod-server
```

This automatically applies all saved settings:
- Host and port
- Username
- SSH key
- Proxy settings
- Shell preference
- Terminal options

### Managing Configurations

**Delete a configuration:**

```bash
lazyssh> delete-config prod-server
```

You'll be asked to confirm before deletion.

**Edit configurations manually:**

The config file is located at `/tmp/lazyssh/connections.conf` in TOML format:

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
shell = "/bin/zsh"

[backup-server]
host = "backup.example.com"
port = 22
username = "backup"
no_term = true
```

You can safely edit this file directly.

### Configuration File Format

**Available fields:**
- `host` (required) - Server hostname or IP address
- `port` (default: 22) - SSH port number
- `username` (required) - SSH username
- `ssh_key` (optional) - Path to SSH private key
- `proxy_port` (optional) - SOCKS proxy port (0 = no proxy)
- `shell` (optional) - Preferred shell (e.g., "/bin/bash", "/bin/zsh")
- `no_term` (optional) - Disable terminal allocation (true/false)

### Security Notes

- Config file permissions are automatically set to 600 (owner read/write only)
- Files are stored in `/tmp/lazyssh/` which is cleared on system reboot
- Only SSH key paths are stored, never the keys themselves
- Use SSH key authentication instead of passwords for better security
- The config file location in `/tmp` means configs won't persist after reboot (by design for security)

### Example Workflows

**Save frequently-used servers:**

```bash
# Production server with SSH key
lazyssh> lazyssh -ip prod.example.com -port 22 -user admin -ssh-key ~/.ssh/prod_key -socket prod
Save this connection configuration? (y/N): y
Enter config name [prod]: production
✓ Configuration saved as 'production'

# Development server with proxy
lazyssh> lazyssh -ip dev.example.com -port 2222 -user dev -proxy 9050 -socket dev
Save this connection configuration? (y/N): y
Enter config name [dev]: development
✓ Configuration saved as 'development'

# Later, reconnect quickly
lazyssh> connect production
lazyssh> connect development
```

**Quick server access:**

```bash
# Day 1: Set up your servers
lazyssh> connect production
lazyssh> connect staging
lazyssh> connect development

# Day 2+: Just connect
lazyssh> connect production
# Instant connection with all settings
```

**Batch setup:**

Create `/tmp/lazyssh/connections.conf` manually:

```toml
[web1]
host = "web1.example.com"
port = 22
username = "admin"
ssh_key = "/home/user/.ssh/id_rsa"

[web2]
host = "web2.example.com"
port = 22
username = "admin"
ssh_key = "/home/user/.ssh/id_rsa"

[db]
host = "db.example.com"
port = 22
username = "dbadmin"
ssh_key = "/home/user/.ssh/db_key"
```

Then connect:

```bash
lazyssh> connect web1
lazyssh> connect web2
lazyssh> connect db
```

## Wizard Workflows

LazySSH provides guided wizard workflows for complex operations that benefit from step-by-step assistance.

### SSH Connection Wizard

The `wizard lazyssh` command guides you through creating SSH connections:

```bash
lazyssh> wizard lazyssh
```

The wizard will prompt you for:
- Host IP address or hostname
- SSH port (defaults to 22)
- Username
- Connection name (socket)
- Optional SSH key path
- Optional SOCKS proxy port

### Tunnel Creation Wizard

The `wizard tunnel` command helps you create tunnels:

```bash
lazyssh> wizard tunnel
```

The wizard will guide you through:
- Selecting an existing connection
- Choosing tunnel type (forward or reverse)
- Setting local and remote ports
- Configuring host addresses

### When to Use Wizards

Use wizard workflows when:
- You're new to LazySSH and want guided assistance
- Creating complex tunnel configurations
- Setting up connections with multiple parameters
- You prefer step-by-step guidance over command syntax

For experienced users, direct commands remain available for faster operation.

## Terminal Methods

LazySSH supports two methods for opening terminal sessions:

### Native Terminal (Default)
- Runs SSH in your current terminal window
- No external dependencies required
- Exit SSH session with `exit` or Ctrl+D to return to LazySSH
- Best for quick access and managing multiple sessions

### Terminator Terminal
- Opens SSH in new Terminator windows
- Requires Terminator to be installed
- Best for keeping many terminals open simultaneously

### Switching Terminal Methods

**Change at runtime:**
```bash
# From command mode
lazyssh> terminal native
lazyssh> terminal terminator
lazyssh> terminal auto  # Auto-select best available
```

**Set via environment variable:**
```bash
# Auto-select (default: tries Terminator first, falls back to native)
export LAZYSSH_TERMINAL_METHOD=auto

# Force native terminal
export LAZYSSH_TERMINAL_METHOD=native

# Force Terminator
export LAZYSSH_TERMINAL_METHOD=terminator
```

## Advanced Features

### Dynamic SOCKS Proxy

Route browser traffic through your SSH connection:

```bash
# Create connection with SOCKS proxy
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy 9050

# Configure your browser to use SOCKS proxy at localhost:9050
# All traffic now tunneled through your SSH server
```

### Batch File Downloads

Download multiple files matching a pattern:

```bash
scp myserver> mget *.conf
# Shows matching files, total size, and asks for confirmation
```

### Directory Tree Visualization

View remote directory structure visually:

```bash
scp myserver> tree /var/www
# Displays color-coded hierarchical tree
```

### Multiple Connections

Manage multiple servers simultaneously:

```bash
lazyssh> lazyssh -ip server1.com -port 22 -user admin -socket server1
lazyssh> lazyssh -ip server2.com -port 22 -user admin -socket server2
lazyssh> list  # See all active connections
lazyssh> open server1
# Exit SSH session to return to LazySSH
lazyssh> open server2
```

### Tab Completion

Press Tab to auto-complete:
- Command names
- Connection names
- File paths (in SCP mode)
- Command parameters

### Help System

Get help anytime:

```bash
# Command mode help
lazyssh> help
lazyssh> help tunc

# SCP mode help
scp myserver> help
scp myserver> help mget
```

## Quick Reference

### Essential Commands

| Command | Description |
|---------|-------------|
| `lazyssh -ip <host> -port <port> -user <user> -socket <name>` | Create connection |
| `list` | Show all connections and tunnels |
| `config` | Display saved configurations |
| `connect <name>` | Connect using saved configuration |
| `save-config <name>` | Save current connection configuration |
| `delete-config <name>` | Delete saved configuration |
| `open <name>` | Open terminal session |
| `close <name>` | Close connection |
| `tunc <name> l <local_port> <remote_host> <remote_port>` | Create forward tunnel |
| `tunc <name> r <remote_port> <local_host> <local_port>` | Create reverse tunnel |
| `tund <tunnel_id>` | Delete tunnel |
| `scp <name>` | Enter SCP mode |
| `terminal <method>` | Change terminal method |
| `wizard <type>` | Start guided workflow (lazyssh, tunnel) |
| `help` | Show help |
| `exit` | Exit LazySSH |

### SCP Mode Commands

| Command | Description |
|---------|-------------|
| `get <file> [<local>]` | Download file |
| `put <file> [<remote>]` | Upload file |
| `mget <pattern>` | Download multiple files |
| `ls [<path>]` | List remote files |
| `tree [<path>]` | Show directory tree |
| `cd <path>` | Change remote directory |
| `lcd <path>` | Change local directory |
| `pwd` | Show current remote directory |
| `local [<path>]` | Set/show local directories |
| `exit` | Return to LazySSH |

For complete command reference, see [commands.md](commands.md).

For specialized guides, see:
- [SCP Mode Guide](scp-mode.md) - Detailed file transfer instructions
- [Tunneling Guide](tunneling.md) - Advanced tunneling scenarios
- [Troubleshooting](troubleshooting.md) - Solutions to common issues
