# LazySSH User Guide

This guide provides a comprehensive overview of using LazySSH, a tool designed to simplify SSH connection management, tunneling, and file transfers.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Interface Modes](#interface-modes)
- [Basic Workflow](#basic-workflow)
- [Advanced Usage](#advanced-usage)
- [Environment Variables](#environment-variables)

## Introduction

LazySSH is designed to make managing SSH connections easier and more efficient. It leverages SSH control sockets to maintain persistent connections, enabling quick access to remote servers, simplified tunnel creation, and streamlined file transfers without repeatedly typing credentials.

## Installation

### Prerequisites

Before installing LazySSH, ensure you have:

- Python 3.11 or higher
- OpenSSH client installed
- Terminator terminal emulator

### Installation Methods

#### Using pip (Recommended)

```bash
# Install for all users (may require sudo)
pip install lazyssh

# Or install for current user only
pip install --user lazyssh
```

#### From Source

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Install
pip install .

# Or for development mode
pip install -e .
```

### Post-Installation

If you installed with `pip install --user` and encounter "command not found" errors:

```bash
# Add to your PATH manually
export PATH="$HOME/.local/bin:$PATH"

# To make it permanent, add this line to your ~/.bashrc file
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Interface Modes

LazySSH offers two interface modes to accommodate different user preferences.

### Command Mode

Command mode is the default interface, providing a command-line experience with smart tab completion.

```bash
# Start in command mode
lazyssh
```

You'll be presented with a prompt: `lazyssh>`

### Prompt Mode

Prompt mode offers a menu-driven interface ideal for beginners or those who prefer guided options.

```bash
# Start in prompt mode
lazyssh --prompt
```

You'll see a numbered menu with options to:
1. Create new SSH connection
2. Destroy tunnel
3. Create tunnel
4. Open terminal
5. Close connection
6. Switch to command mode
7. Exit

### Switching Between Modes

- From command mode to prompt mode: Type `mode` and press Enter
- From prompt mode to command mode: Select option 6

## Basic Workflow

### 1. Creating a Connection

```bash
# In command mode
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver

# With identity file (SSH key)
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -ssh-key ~/.ssh/id_rsa
```

The `-socket` parameter assigns a unique name to your connection, which you'll use to reference it in other commands.

### 2. Listing Connections

```bash
list
```

This shows all active connections with details including:
- Connection name
- Host
- Username
- Port
- Dynamic Port (if any)
- Active Tunnels
- Socket Path

### 3. Opening a Terminal

```bash
# Open a terminal for the connection named "myserver"
open myserver
```

This launches a terminal window connected to your server using the configured terminal method.

### 4. Creating Tunnels

#### Forward Tunnel

```bash
# Syntax: tunc <connection_name> l <local_port> <remote_host> <remote_port>
tunc myserver l 8080 localhost 80
```

This forwards your local port 8080 to port 80 on the remote server, allowing you to access a remote web server via http://localhost:8080.

#### Reverse Tunnel

```bash
# Syntax: tunc <connection_name> r <remote_port> <local_host> <local_port>
tunc myserver r 8080 localhost 3000
```

This forwards remote port 8080 to your local port 3000, enabling someone on the remote server to access your local service.

### 5. Deleting Tunnels

```bash
# Syntax: tund <tunnel_id>
tund 1
```

The tunnel ID can be found in the output of the `list` command.

### 6. File Transfers (SCP Mode)

```bash
# Enter SCP mode for a specific connection
scp myserver
```

In SCP mode, you'll have access to commands for transferring files securely:
- `get <remote_file> [<local_file>]` - Download a file
- `put <local_file> [<remote_file>]` - Upload a file
- `mget <pattern>` - Download multiple files
- `ls [<path>]` - List remote files
- `lls [<path>]` - List local files
- `tree [<path>]` - Display remote directory structure in a tree view
- `cd <path>` - Change remote directory
- `lcd <path>` - Change local download directory
- `pwd` - Show remote directory
- `local [<path>]` - Set/show local download/upload directories
- `exit` - Return to LazySSH

### 7. Closing Connections

```bash
# Close a specific connection
close myserver

# Exit LazySSH (will prompt to close active connections)
exit
```

## Advanced Usage

### Dynamic SOCKS Proxy

Create a SOCKS proxy for secure browsing through your SSH connection:

```bash
# With default port (9050)
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy

# With custom port
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080
```

Then configure your browser or applications to use the SOCKS proxy at `localhost:9050` (or your custom port).

### SCP Mode Advanced Features

#### Batch Downloads

Download multiple files matching a pattern:

```
scp myserver
scp myserver> mget *.log
```

This will:
1. Show you matching files with sizes
2. Calculate total download size
3. Ask for confirmation
4. Download all matching files

#### Directory Tree Visualization

View the structure of remote directories in a hierarchical tree format:

```
scp myserver> tree /var/www
```

This will display a color-coded tree of all files and directories, making it easy to understand complex directory structures at a glance.

#### Remote File Navigation

```
scp myserver> cd /var/log
scp myserver> pwd
scp myserver> ls
```

#### Setting Download Directory

```
scp myserver> local ~/Downloads
scp myserver> lcd ~/Downloads/server-logs
```

## Environment Variables

LazySSH can be customized using environment variables:

- `LAZYSSH_SSH_PATH`: Path to the SSH executable (default: `/usr/bin/ssh`)
- `LAZYSSH_TERMINAL`: Terminal emulator to use (default: `terminator`)
- `LAZYSSH_CONTROL_PATH`: Base path for control sockets (default: `/tmp/`)

Example:

```bash
# Set a custom terminal
export LAZYSSH_TERMINAL=gnome-terminal
``` 