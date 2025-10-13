# LazySSH Command Reference

This document provides a comprehensive reference for all LazySSH commands, their parameters, and usage examples.

## Table of Contents
- [Command Mode Commands](#command-mode-commands)
- [SCP Mode Commands](#scp-mode-commands)
- [Tab Completion](#tab-completion)

## Command Mode Commands

LazySSH's command mode provides the following commands:

### `lazyssh`

Creates a new SSH connection with optional tunnels and proxies.

**Syntax:**
```
lazyssh -ip <host_ip> -port <port> -user <username> -socket <name> [-proxy [port]] [-ssh-key <path>]
```

**Parameters:**
- `-ip <host_ip>`: The hostname or IP address of the remote server (required)
- `-port <port>`: The SSH port of the remote server (required, typically 22)
- `-user <username>`: The username for the SSH connection (required)
- `-socket <name>`: A unique name for the connection (required)
- `-proxy [port]`: Create a dynamic SOCKS proxy (optional, default port is 9050)
- `-ssh-key <path>`: Path to the SSH private key file (optional)

**Examples:**
```bash
# Basic connection
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver

# Connection with SOCKS proxy on default port (9050)
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy

# Connection with SOCKS proxy on custom port
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080

# Connection with a specific SSH key
lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -ssh-key ~/.ssh/id_rsa
```

### `tunc`

Creates a tunnel through an existing SSH connection.

**Syntax:**
```
tunc <connection_name> <type> <local_port> <remote_host> <remote_port>
```

**Parameters:**
- `connection_name`: Name of the existing SSH connection
- `type`: Tunnel type (`l` for local/forward, `r` for remote/reverse)
- `local_port`: Local port for the tunnel
- `remote_host`: Hostname or IP address for the remote end
- `remote_port`: Port number for the remote end

**Examples:**
```bash
# Forward tunnel (local port 8080 to remote port 80)
tunc myserver l 8080 localhost 80

# Reverse tunnel (remote port 3000 to local port 8080)
tunc myserver r 3000 localhost 8080
```

### `tund`

Deletes an existing tunnel.

**Syntax:**
```
tund <tunnel_id>
```

**Parameters:**
- `tunnel_id`: The ID of the tunnel to delete (shown in the `list` command output)

**Example:**
```bash
tund 1
```

### `list`

Lists all active SSH connections and tunnels.

**Syntax:**
```
list
```

**Example:**
```bash
list
```

### `open`

Opens a terminal session for an existing SSH connection.

**Syntax:**
```
open <connection_name>
```

**Parameters:**
- `connection_name`: Name of the existing SSH connection

**Example:**
```bash
open myserver
```

**Note:** This command creates a symmetric pair with the `close` command.

### `terminal`

Changes the terminal method used for opening terminal sessions.

**Syntax:**
```
terminal <method>
```

**Parameters:**
- `method`: Terminal method to use (`auto`, `native`, or `terminator`)
  - `auto`: Try terminator first, fallback to native (default)
  - `native`: Use native terminal (subprocess, allows returning to LazySSH)
  - `terminator`: Use terminator terminal emulator only

**Examples:**
```bash
terminal native
terminal auto
terminal terminator
```

**Note:** This setting persists for the current session only and doesn't affect already-open terminals.

### `close`

Closes an SSH connection and its associated tunnels.

**Syntax:**
```
close <connection_name>
```

**Parameters:**
- `connection_name`: Name of the SSH connection to close

**Example:**
```bash
close myserver
```

### `config` (or `configs`)

Displays all saved connection configurations.

**Syntax:**
```
config
```

**Example:**
```bash
config
# or
configs
```

**Description:**
Shows a table of all saved connection configurations including host, username, port, SSH key path, proxy settings, and other parameters. Configurations are stored in `/tmp/lazyssh/connections.conf` in TOML format.

### `connect`

Connects using a saved configuration.

**Syntax:**
```
connect <config_name>
```

**Parameters:**
- `config_name`: Name of the saved configuration to use

**Example:**
```bash
connect prod-server
```

**Description:**
Establishes a new SSH connection using all settings from a saved configuration. This automatically applies host, port, username, SSH key, proxy settings, and other parameters saved in the configuration.

### `save-config`

Saves the current or last connection configuration for reuse.

**Syntax:**
```
save-config <config_name>
```

**Parameters:**
- `config_name`: Name to save the configuration as (alphanumeric, dashes, and underscores only)

**Example:**
```bash
save-config prod-server
```

**Description:**
Saves the current or most recent connection parameters to `/tmp/lazyssh/connections.conf`. If a configuration with the same name exists, you'll be prompted to confirm overwriting it.

**Note:** LazySSH also prompts you to save a configuration automatically after successfully creating a new connection.

### `delete-config`

Deletes a saved connection configuration.

**Syntax:**
```
delete-config <config_name>
```

**Parameters:**
- `config_name`: Name of the configuration to delete

**Example:**
```bash
delete-config prod-server
```

**Description:**
Removes a saved configuration from `/tmp/lazyssh/connections.conf`. You'll be asked to confirm before deletion.

### `backup-config`

Creates a backup of the connections configuration file.

**Syntax:**
```
backup-config
```

**Example:**
```bash
backup-config
```

**Description:**
Creates a backup copy of `/tmp/lazyssh/connections.conf` as `/tmp/lazyssh/connections.conf.backup`. This allows you to safely restore your saved configurations if needed. The backup file is created atomically with proper permissions (600, owner read/write only). If a previous backup exists, it will be overwritten without prompting.

### `scp`

Enters SCP mode for file transfers with a specific connection.

**Syntax:**
```
scp [<connection_name>]
```

**Parameters:**
- `connection_name`: (Optional) Name of the existing SSH connection. If not provided, you'll be prompted to select one.

**Example:**
```bash
scp myserver
```

### `wizard`

Starts guided workflows for complex operations.

**Syntax:**
```
wizard <type>
```

**Parameters:**
- `type`: The type of wizard to start (`lazyssh` or `tunnel`)

**Examples:**
```bash
# Start SSH connection wizard
wizard lazyssh

# Start tunnel creation wizard
wizard tunnel
```

**Description:**
The wizard provides step-by-step guidance for creating SSH connections and tunnels. This is particularly helpful for new users or when setting up complex configurations.

### `clear`

Clears the terminal screen.

**Syntax:**
```
clear
```

**Example:**
```bash
clear
```

### `debug`

Toggles debug mode on or off. When enabled, shows detailed logging information in the console.

**Syntax:**
```
debug
```

**Example:**
```bash
debug
```

### `help`

Displays help information about available commands.

**Syntax:**
```
help [<command>]
```

**Parameters:**
- `command`: (Optional) The command to get detailed help for

**Examples:**
```bash
# Show all available commands
help

# Get help for a specific command
help tunc
```

### `exit` (or `quit`)

Exits LazySSH, closing all connections if confirmed.

**Syntax:**
```
exit
```

**Example:**
```bash
exit
```

## SCP Mode Commands

When in SCP mode, you have access to the following commands:

### `get`

Downloads a file from the remote server.

**Syntax:**
```
get <remote_file> [<local_file>]
```

**Parameters:**
- `remote_file`: Path to the file on the remote server
- `local_file`: (Optional) Path where the file should be saved locally. If not specified, downloads to the current local directory with the same filename.

**Example:**
```bash
get /etc/nginx/nginx.conf
get /var/log/syslog ./logs/system.log
```

### `put`

Uploads a file to the remote server.

**Syntax:**
```
put <local_file> [<remote_file>]
```

**Parameters:**
- `local_file`: Path to the local file
- `remote_file`: (Optional) Path where the file should be saved on the remote server. If not specified, uploads to the current remote directory with the same filename.

**Example:**
```bash
put ./config.json
put ./scripts/backup.sh /home/user/scripts/backup.sh
```

### `mget`

Downloads multiple files matching a pattern.

**Syntax:**
```
mget <pattern>
```

**Parameters:**
- `pattern`: Glob pattern to match files (e.g., *.txt, log*.gz)

**Example:**
```bash
mget *.log
mget /var/log/apache2/*.gz
```

### `ls`

Lists files in a remote directory.

**Syntax:**
```
ls [<remote_path>]
```

**Parameters:**
- `remote_path`: (Optional) Path to list. If not specified, lists the current remote directory.

**Example:**
```bash
ls
ls /var/log
```

### `lls`

Lists files in the local download directory.

**Syntax:**
```
lls [<local_path>]
```

**Parameters:**
- `local_path`: (Optional) Path to list. If not specified, lists the current local download directory.

**Example:**
```bash
lls
lls ./downloads
```

### `tree`

Displays a hierarchical tree view of the remote directory structure.

**Syntax:**
```
tree [<remote_path>]
```

**Parameters:**
- `remote_path`: (Optional) Path to display as a tree. If not specified, displays the current remote directory.

**Example:**
```bash
tree
tree /var/www/html
```

### `cd`

Changes the current remote directory.

**Syntax:**
```
cd <remote_path>
```

**Parameters:**
- `remote_path`: Path to change to on the remote server

**Example:**
```bash
cd /home/user/documents
cd ..
```

### `lcd`

Changes the local download directory.

**Syntax:**
```
lcd <local_path>
```

**Parameters:**
- `local_path`: Local path to set as the download directory

**Example:**
```bash
lcd ~/Downloads/server-files
lcd ../backup-files
```

### `pwd`

Shows the current remote working directory.

**Syntax:**
```
pwd
```

**Example:**
```bash
pwd
```

### `local`

Sets or displays the local download and upload directories.

**Syntax:**
```
local [<path>]
local [download|upload] <path>
```

**Parameters:**
- `path`: (Optional) Local path to set as the download/upload directory. If not specified, displays the current local directories.
- `download`: Specifies to set only the download directory
- `upload`: Specifies to set only the upload directory

**Example:**
```bash
local
local ~/Downloads/server-files
local download ~/Downloads/server-logs
local upload ~/Uploads/server-files
```

### `help`

Displays help information for SCP mode commands.

**Syntax:**
```
help [<command>]
```

**Parameters:**
- `command`: (Optional) The SCP mode command to get detailed help for

**Example:**
```bash
help
help mget
```

### `exit`

Exits SCP mode and returns to LazySSH command mode.

**Syntax:**
```
exit
```

**Example:**
```bash
exit
```

## Tab Completion

LazySSH features intelligent tab completion in both command and SCP modes:

### Command Mode Tab Completion

- **Command Names**: Press Tab to see available commands
- **Connection Names**: Automatically suggests connection names for commands like `open`, `close`, `scp`, and `tunc`
- **Configuration Names**: Suggests saved configuration names for commands like `connect` and `delete-config`
- **Terminal Methods**: Suggests `auto`, `native`, and `terminator` for the `terminal` command
- **Command Parameters**: Suggests relevant parameters for commands
- **File Paths**: Offers file path completion for commands requiring files

### SCP Mode Tab Completion

- **Command Names**: Press Tab to see available SCP mode commands
- **Remote Files**: Automatically suggests remote files when using `get`, `ls`, etc.
- **Local Files**: Suggests local files when using `put`, `lls`, etc.
- **Directory Paths**: Offers path completion for `cd` and similar commands
