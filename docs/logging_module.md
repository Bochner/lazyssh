# LazySSH Logging Module Documentation

## Overview

The LazySSH logging module provides robust logging capabilities throughout the application using Python's standard `logging` module enhanced with Rich library formatting. The logging system is designed to maintain detailed logs of all operations while providing configurable console output.

## Key Features

- Log all SSH connections, commands, tunnels, and file transfers
- Both file-based and console logging (console can be toggled)
- Connection-specific logs for detailed tracking
- Hierarchical log structure organized by connection
- File transfer statistics tracking
- Rich formatted console output when debug mode is enabled

## Log Directory Structure

```
/tmp/lazyssh/
├── logs/                              # Global logs directory
│   ├── lazyssh_YYYYMMDD.log           # Main application log
│   ├── lazyssh.ssh_YYYYMMDD.log       # SSH operations log
│   ├── lazyssh.command_YYYYMMDD.log   # Command mode operations log
│   └── lazyssh.scp_YYYYMMDD.log       # SCP operations log
│
├── <connection_name>.d/               # Connection-specific directory
│   ├── downloads/                     # Downloaded files
│   ├── uploads/                       # Files for uploading
│   └── logs/                          # Connection-specific logs
│       └── connection.log             # Connection activity log
│
└── <another_connection>.d/
    ├── downloads/
    ├── uploads/
    └── logs/
        └── connection.log
```

## Log Files Content

| Log File | Content Description |
|----------|---------------------|
| `lazyssh_YYYYMMDD.log` | General application events, startup, configuration |
| `lazyssh.ssh_YYYYMMDD.log` | SSH connection creation/termination, command execution, tunnel management |
| `lazyssh.command_YYYYMMDD.log` | Command mode operations, user input, command execution |
| `lazyssh.scp_YYYYMMDD.log` | SCP transfers, remote file operations |
| `<connection_name>.d/logs/connection.log` | All activity specific to the connection including commands and file transfers |

## Configuration and Usage

### Log Levels

The logging module supports standard Python logging levels:

- `DEBUG`: Detailed information, typically useful for troubleshooting
- `INFO`: Confirmation that things are working as expected
- `WARNING`: Indication that something unexpected happened
- `ERROR`: Due to a more serious problem, the software couldn't perform some function
- `CRITICAL`: A serious error indicating that the program itself may be unable to continue running

### Environment Variables

The logging level can be configured using the `LAZYSSH_LOG_LEVEL` environment variable:

```bash
export LAZYSSH_LOG_LEVEL=DEBUG  # Set logging level to DEBUG
```

Default logging level is `INFO` if not specified.

### Debug Mode

LazySSH provides a debug mode that can be enabled in two ways:

1. Using the `--debug` flag when starting the application
2. Using the `debug` command in the command interface

When debug mode is enabled, log messages are displayed in the console with Rich formatting. When disabled, logs are still written to files but not displayed in the console.

```
lazyssh --debug  # Start with debug logging enabled
```

Or from within the application:

```
lazyssh> debug  # Toggle debug mode on/off
```

## Transfer Statistics

The logging module tracks file transfer statistics for each connection:

- Number of files transferred
- Total bytes transferred
- Last update time

This information is logged after each file transfer and can be used to monitor transfer activity.

## Connection-Specific Logging

Each SSH connection has its own dedicated logger that writes to a connection-specific log file. This allows for easy tracking of activity on a per-connection basis.

### Connection Log Format

Connection logs use a simpler format: `timestamp - level - message` and include:

- Commands executed on the connection
- File transfers (uploads and downloads) with file sizes
- Transfer statistics

## Implementation Details

### Logger Hierarchy

LazySSH uses a hierarchical logger structure:

- `lazyssh` - Root logger for the application
  - `lazyssh.ssh` - SSH operations
  - `lazyssh.command` - Command mode operations
  - `lazyssh.scp` - SCP mode operations
  - `lazyssh.connection.<name>` - Connection-specific loggers

### File Handlers

Each logger has at least two handlers:

1. `RichHandler`: Displays logs in the console with Rich formatting (only active in debug mode)
2. `FileHandler`: Writes logs to the appropriate log file

### Customization Points

The logging module provides several functions for customizing logging:

- `set_debug_mode(enabled)`: Toggle debug mode on/off
- `get_logger(name, level, log_dir)`: Get or create a logger with specific settings
- `get_connection_logger(connection_name)`: Get or create a connection-specific logger

## Best Practices

1. **Use the debug command** rather than editing log levels manually
2. **Check connection-specific logs** for troubleshooting transfer issues
3. **Periodically clean up old log files** as they can accumulate over time
4. **Use `grep` on log files** to find specific information:
   ```bash
   grep "error" /tmp/lazyssh/logs/lazyssh.ssh_*.log
   ```

## Example Log Entries

### SSH Connection Log (lazyssh.ssh_YYYYMMDD.log):
```
2025-03-29 12:34:56 [INFO] lazyssh.ssh: Connection established: ubuntu@192.168.1.100:22, socket: /tmp/ubuntu
2025-03-29 12:35:10 [INFO] lazyssh.ssh: Dynamic proxy created on port 9050
```

### SCP Operation Log (lazyssh.scp_YYYYMMDD.log):
```
2025-03-29 12:40:22 [INFO] lazyssh.scp: File downloaded from ubuntu: /home/ubuntu/data.zip -> /tmp/lazyssh/ubuntu.d/downloads/data.zip (15.25MB)
2025-03-29 12:41:05 [INFO] lazyssh.scp: Transfer stats for ubuntu: 1 files, 15.25MB
```

### Connection-Specific Log (/tmp/lazyssh/ubuntu.d/logs/connection.log):
```
2025-03-29 12:34:56 - INFO - SSH connection established
2025-03-29 12:40:00 - INFO - SCP command executed: find /home/ubuntu -maxdepth 1 -type f -name 'data.zip' -printf '%f\n'
2025-03-29 12:40:22 - INFO - File downloaded: /home/ubuntu/data.zip -> /tmp/lazyssh/ubuntu.d/downloads/data.zip (15.25MB)
2025-03-29 12:41:05 - INFO - Transfer stats: 1 files, 15.25MB
```

## Internal Architecture

The logging module is implemented in `src/lazyssh/logging_module.py` and provides the following key functions:

- `setup_logger`: Creates and configures a logger with file and console handlers
- `get_logger`: Gets or creates a logger with the specified name and level
- `get_connection_logger`: Creates a connection-specific logger
- `log_ssh_connection`: Logs SSH connection details
- `log_ssh_command`: Logs SSH command execution
- `log_scp_command`: Logs SCP command execution
- `log_file_transfer`: Logs file transfer operations with details
- `update_transfer_stats`: Updates and logs file transfer statistics
- `format_size`: Formats byte sizes into human-readable strings

The module also maintains a global `transfer_stats` dictionary that tracks transfer statistics for each connection.
