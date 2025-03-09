# SCP Mode Guide

LazySSH includes a robust SCP (Secure Copy Protocol) mode for transferring files between your local machine and remote servers. This guide provides comprehensive information on using SCP mode effectively.

## Table of Contents

- [Entering SCP Mode](#entering-scp-mode)
- [The SCP Mode Interface](#the-scp-mode-interface)
- [Basic File Operations](#basic-file-operations)
- [Advanced Features](#advanced-features)
- [Command Reference](#command-reference)
- [Tips and Best Practices](#tips-and-best-practices)

## Entering SCP Mode

You can enter SCP mode from LazySSH's command mode by using the `scp` command:

```bash
# Specify a connection directly
lazyssh> scp myserver

# Or let LazySSH prompt you to select a connection
lazyssh> scp
```

If you don't specify a connection, LazySSH will display a list of active connections and prompt you to select one.

## The SCP Mode Interface

Once in SCP mode, you'll see a prompt that shows:

```
scp myserver:/current/remote/path [/local/download/directory]>
```

This prompt displays:
- The connection name (`myserver`)
- Your current remote directory (`/current/remote/path`)
- Your current local download directory (`/local/download/directory`)

## Basic File Operations

### Downloading Files

To download a file from the remote server:

```bash
# Basic usage
get remote_file.txt

# Specify a different local filename
get remote_file.txt local_copy.txt

# Use absolute paths
get /etc/nginx/nginx.conf ~/configs/nginx.conf
```

### Uploading Files

To upload a file to the remote server:

```bash
# Basic usage
put local_file.txt

# Specify a different remote filename
put local_file.txt uploaded_file.txt

# Use absolute paths
put ~/scripts/backup.sh /home/user/scripts/backup.sh
```

### Navigating Directories

#### Remote Navigation

```bash
# Change remote directory
cd /var/log

# Check current remote directory
pwd

# List remote directory contents
ls
ls /home/user/documents
```

#### Local Navigation

```bash
# Set local download directory
local ~/Downloads/server-files

# Check current local directory
local

# List local directory contents
lls
lls ~/other/directory
```

## Advanced Features

### Batch Downloads with `mget`

The `mget` command allows you to download multiple files matching a pattern:

```bash
# Download all log files
mget *.log

# Download all files in a remote directory
mget /var/log/nginx/*.gz
```

When using `mget`, LazySSH:
1. Displays all matching files with their sizes
2. Shows the total download size
3. Asks for confirmation before downloading
4. Shows progress as files are downloaded

### Human-Readable File Listings

Both `ls` and `lls` commands display file sizes in human-readable format (KB, MB, GB), making it easier to understand file sizes at a glance.

```bash
# Remote file listing with human-readable sizes
ls

# Local file listing with sizes and summary
lls
```

The `lls` command also displays a summary at the end, showing:
- Total number of files and directories
- Total size of all files in human-readable format

## Command Reference

| Command | Description | Syntax |
|---------|-------------|--------|
| `get` | Download a file | `get <remote_file> [<local_file>]` |
| `put` | Upload a file | `put <local_file> [<remote_file>]` |
| `mget` | Download multiple files | `mget <pattern>` |
| `ls` | List remote files | `ls [<remote_path>]` |
| `lls` | List local files | `lls [<local_path>]` |
| `cd` | Change remote directory | `cd <remote_path>` |
| `pwd` | Show current remote directory | `pwd` |
| `local` | Set/show local download directory | `local [<path>]` |
| `help` | Show help | `help [<command>]` |
| `exit` | Exit SCP mode | `exit` |

## Tips and Best Practices

### Efficient File Navigation

- Use tab completion to quickly find files and directories
- Press Tab after typing a partial filename to auto-complete
- Use `pwd` and `local` frequently to verify your current locations
- Use `ls` with specific directories to explore without changing your current location

### Download Organization

- Use the `local` command to create separate download directories for different purposes
- Set up a logical directory structure to keep downloaded files organized
- Consider using date-based directories for log files or other time-based downloads

### Handling Large Files

- Use the file size information displayed by `ls` to check file sizes before downloading
- When using `mget`, check the total download size displayed before confirming
- For very large downloads, consider using a more specialized tool or breaking the download into smaller chunks

### Using Path Shortcuts

- `~` expands to your home directory on both local and remote systems
- `.` refers to the current directory
- `..` refers to the parent directory
- These shortcuts work in all path-related commands

### Security Considerations

- Downloaded files maintain their original permissions
- Be cautious when uploading executable files or scripts
- Double-check paths when using `put` to avoid overwriting important files

### Common Workflows

**Log Analysis:**
```bash
cd /var/log
ls
mget apache2/*.log
exit
# Now process the logs locally
```

**Configuration Backup:**
```bash
cd /etc
mget *.conf
exit
# Now you have backups of all config files
```

**Deploying Updates:**
```bash
cd /var/www/myapp
put updated_app.zip
# Now unzip on the server
exit
``` 