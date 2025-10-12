# SCP Mode Guide

LazySSH's SCP mode provides a streamlined interface for transferring files between your local machine and remote servers with rich visual feedback and progress tracking.

## Table of Contents

- [Getting Started](#getting-started)
- [File Operations](#file-operations)
- [Navigation](#navigation)
- [Advanced Features](#advanced-features)
- [Command Reference](#command-reference)
- [Common Workflows](#common-workflows)

## Getting Started

### Entering SCP Mode

From LazySSH command mode:

```bash
# Enter SCP mode for a specific connection
lazyssh> scp myserver

# Or let LazySSH prompt you to select a connection
lazyssh> scp
```

### Understanding the Prompt

Once in SCP mode, you'll see:

```
scp myserver:/current/remote/path [↓/local/download | ↑/local/upload]>
```

This shows:
- **Connection name**: `myserver`
- **Remote directory**: `/current/remote/path`
- **Download directory**: `/local/download` (marked with ↓)
- **Upload directory**: `/local/upload` (marked with ↑)

## File Operations

### Downloading Files

```bash
# Download single file
get remote_file.txt

# Download with different local name
get remote_file.txt local_copy.txt

# Download with absolute paths
get /etc/nginx/nginx.conf ~/configs/nginx.conf
```

### Uploading Files

```bash
# Upload single file
put local_file.txt

# Upload with different remote name
put local_file.txt uploaded_file.txt

# Upload with absolute paths
put ~/scripts/backup.sh /home/user/scripts/backup.sh
```

### Batch Downloads

Download multiple files matching a pattern:

```bash
# Download all log files
mget *.log

# Download compressed files from a specific directory
mget /var/log/nginx/*.gz
```

LazySSH will:
1. Show matching files with sizes
2. Display total download size
3. Ask for confirmation
4. Show progress for each file

## Navigation

### Remote Navigation

```bash
# Change remote directory
cd /var/log

# Check current location
pwd

# List remote files
ls
ls /home/user/documents

# View directory tree
tree
tree /home/user/projects
```

### Local Navigation

```bash
# Set local download/upload directory
local ~/Downloads/server-files

# Change download directory
lcd ~/Downloads/server-logs

# Set specific directories
local download ~/Downloads/server-files
local upload ~/Uploads/server-files

# View current local directories
local

# List local files
lls
lls ~/other/directory
```

## Advanced Features

### Directory Tree Visualization

The `tree` command displays a hierarchical, color-coded view of remote directories:

```bash
tree
tree /var/www/html
```

Features:
- Visual tree representation
- Color-coded file types
- File and directory counts

### Human-Readable Listings

File listings display sizes in human-readable format (KB, MB, GB):

```bash
# Remote listing
ls

# Local listing with summary
lls
```

The `lls` command shows:
- File count and directory count
- Total size of all files

### Progress Tracking

File transfers show:
- Real-time progress bars
- Transfer speed
- Time remaining
- Total bytes transferred

## Command Reference

| Command | Description |
|---------|-------------|
| `get <file> [<local>]` | Download a file |
| `put <file> [<remote>]` | Upload a file |
| `mget <pattern>` | Download multiple files matching pattern |
| `ls [<path>]` | List remote files |
| `lls [<path>]` | List local files |
| `tree [<path>]` | Display remote directory tree |
| `cd <path>` | Change remote directory |
| `lcd <path>` | Change local download directory |
| `pwd` | Show current remote directory |
| `local [<path>]` | Set/show local download/upload directories |
| `help [<command>]` | Show help information |
| `exit` | Return to LazySSH |

### Tab Completion

Press Tab to auto-complete:
- Command names
- Remote file and directory paths
- Local file and directory paths

## Common Workflows

### Log File Analysis

```bash
# Navigate to logs
cd /var/log

# Get overview of structure
tree

# List files
ls

# Download all Apache logs
mget apache2/*.log

# Return to LazySSH
exit
```

### Configuration Backup

```bash
# Navigate to config directory
cd /etc

# View structure
tree nginx

# Download all config files
mget *.conf

# Exit
exit
```

### Application Deployment

```bash
# Navigate to deployment directory
cd /var/www/myapp

# Upload application package
put updated_app.zip

# Verify upload
ls -lh updated_app.zip

# Exit
exit
```

### Batch File Synchronization

```bash
# Set organized download location
local ~/Downloads/server-backup-2025-10

# Navigate to target directory
cd /home/user/important-docs

# Download everything
mget *

# Exit
exit
```

## Tips

### Efficient Navigation

- Use `pwd` and `local` frequently to verify your location
- Use `ls <path>` to explore without changing directories
- Use `tree` for quick overview of complex structures
- Tab completion works for both remote and local paths

### Path Shortcuts

- `~` expands to home directory (local and remote)
- `.` refers to current directory
- `..` refers to parent directory

### File Management

- Check file sizes with `ls` before downloading large files
- Use `mget` confirmation prompt to verify total download size
- Organize downloads with `lcd` or `local` commands
- Use date-based directories for log files

### Performance

- `tree` may be slow on very large directories - use on specific subdirectories
- Batch downloads with `mget` are more efficient than multiple `get` commands
- Progress bars show transfer speed and time estimates

### Security

- Downloaded files maintain their original permissions
- Verify paths carefully when using `put` to avoid overwriting files
- Be cautious with executable files and scripts

For complete command syntax, see [commands.md](commands.md).
