# LazySSH Plugin Development Guide

Welcome to LazySSH plugin development! This guide will help you create custom plugins to extend LazySSH's functionality.

## Table of Contents

- [What are Plugins?](#what-are-plugins)
- [Plugin Structure](#plugin-structure)
- [Environment Variables](#environment-variables)
- [Creating Your First Plugin](#creating-your-first-plugin)
- [Plugin Metadata](#plugin-metadata)
- [Executing Remote Commands](#executing-remote-commands)
- [Best Practices](#best-practices)
- [Security Considerations](#security-considerations)
- [Testing and Debugging](#testing-and-debugging)
- [Examples](#examples)

## What are Plugins?

Plugins are executable Python or shell scripts that run on your local machine and can execute commands on remote hosts through LazySSH's established SSH connections. They're perfect for:

- System enumeration and reconnaissance
- Automated security audits
- Batch operations across multiple systems
- Custom diagnostics and reporting
- Configuration management
- Log analysis

## Plugin Structure

A valid plugin must:

1. Be located in the `plugins/` directory
2. Have a `.py` (Python) or `.sh` (shell) extension
3. Have execute permissions (`chmod +x`)
4. Start with a shebang line (`#!/usr/bin/env python3` or `#!/bin/bash`)
5. Include metadata comments (recommended)

### Basic Plugin Template

```python
#!/usr/bin/env python3
# PLUGIN_NAME: my-plugin
# PLUGIN_DESCRIPTION: Brief description of what the plugin does
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

import os
import subprocess
import sys

def run_remote_command(command: str) -> tuple[int, str, str]:
    """Execute a command on the remote host"""
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")
    
    ssh_cmd = [
        "ssh",
        "-S", socket_path,
        "-o", "ControlMaster=no",
        f"{user}@{host}",
        command
    ]
    
    result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    # Your plugin logic here
    exit_code, stdout, stderr = run_remote_command("uname -a")
    if exit_code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nPlugin interrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

## Environment Variables

LazySSH provides these environment variables to your plugin:

| Variable | Description | Example |
|----------|-------------|---------|
| `LAZYSSH_SOCKET` | Control socket name | `myserver` |
| `LAZYSSH_HOST` | Remote host address | `192.168.1.100` |
| `LAZYSSH_PORT` | SSH port | `22` |
| `LAZYSSH_USER` | SSH username | `ubuntu` |
| `LAZYSSH_SOCKET_PATH` | Full path to control socket | `/tmp/myserver` |
| `LAZYSSH_SSH_KEY` | SSH key path (if used) | `/home/user/.ssh/id_rsa` |
| `LAZYSSH_PLUGIN_API_VERSION` | Plugin API version | `1` |

### Accessing in Python

```python
import os

socket = os.environ.get("LAZYSSH_SOCKET")
host = os.environ.get("LAZYSSH_HOST")
user = os.environ.get("LAZYSSH_USER")
```

### Accessing in Shell

```bash
#!/bin/bash

echo "Connected to: $LAZYSSH_USER@$LAZYSSH_HOST"
echo "Socket: $LAZYSSH_SOCKET"
```

## Creating Your First Plugin

### Step 1: Create the Plugin File

```bash
cd /path/to/lazyssh/src/lazyssh/plugins/
touch my_plugin.py
chmod +x my_plugin.py
```

### Step 2: Add Shebang and Metadata

```python
#!/usr/bin/env python3
# PLUGIN_NAME: my-plugin
# PLUGIN_DESCRIPTION: My first LazySSH plugin
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3
```

### Step 3: Implement Plugin Logic

```python
import os
import subprocess
import sys

def main():
    host = os.environ.get("LAZYSSH_HOST")
    print(f"Hello from {host}!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Step 4: Test Your Plugin

```bash
# In LazySSH command mode:
plugin list              # Should show your plugin
plugin info my-plugin    # Show plugin details
plugin run my-plugin myserver  # Execute it
```

## Plugin Metadata

Metadata is defined in comments at the top of your plugin file:

```python
# PLUGIN_NAME: short-name
# PLUGIN_DESCRIPTION: One-line description
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3, specific-tool
```

- **PLUGIN_NAME**: Short, kebab-case name (will be shown in plugin list)
- **PLUGIN_DESCRIPTION**: Brief one-line description
- **PLUGIN_VERSION**: Semantic version (MAJOR.MINOR.PATCH)
- **PLUGIN_REQUIREMENTS**: Comma-separated list of dependencies

## Executing Remote Commands

### Using SSH with Control Socket

The recommended way to execute remote commands is using SSH with the control socket:

```python
def run_remote_command(command: str, timeout: int = 30) -> tuple[int, str, str]:
    """Execute command on remote host"""
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")
    
    ssh_cmd = [
        "ssh",
        "-S", socket_path,      # Use control socket
        "-o", "ControlMaster=no",  # Don't try to be master
        f"{user}@{host}",
        command
    ]
    
    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)
```

### Handling Command Failures

```python
def safe_command(command: str, default: str = "N/A") -> str:
    """Run command and return output or default on failure"""
    exit_code, stdout, stderr = run_remote_command(command)
    if exit_code == 0 and stdout.strip():
        return stdout.strip()
    return default

# Usage
hostname = safe_command("hostname")
uptime = safe_command("uptime", default="Unknown")
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
try:
    exit_code, stdout, stderr = run_remote_command("some-command")
    if exit_code != 0:
        print(f"Warning: Command failed: {stderr}", file=sys.stderr)
        # Continue with other tasks or exit
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```

### 2. User Feedback

Provide clear progress indicators:

```python
print("  [*] Gathering system information...")
data = get_system_info()
print("  [✓] System information collected")

print("  [*] Checking network configuration...")
network = get_network_info()
print("  [✓] Network configuration collected")
```

### 3. Timeouts

Set appropriate timeouts for commands:

```python
# Quick command
exit_code, stdout, stderr = run_remote_command("hostname", timeout=5)

# Longer operation
exit_code, stdout, stderr = run_remote_command("apt list --installed", timeout=60)
```

### 4. Output Formatting

Format output for readability:

```python
def print_section(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")

print_section("System Information")
print(f"Hostname: {hostname}")
print(f"Uptime: {uptime}")
```

### 5. Graceful Degradation

Handle missing commands or permissions:

```python
# Check if command exists
if safe_command("which systemctl") != "N/A":
    services = safe_command("systemctl list-units --type=service")
else:
    services = "systemd not available"
```

## Security Considerations

### ⚠️ Important Security Notes

1. **Trust**: Only run plugins you trust. Plugins execute with your user privileges.

2. **Code Review**: Review plugin code before execution, especially from untrusted sources.

3. **Input Validation**: If your plugin accepts arguments, validate them:

```python
import re

def validate_hostname(hostname: str) -> bool:
    """Validate hostname format"""
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(pattern, hostname))
```

4. **Command Injection**: Never use string formatting for SSH commands:

```python
# BAD - Vulnerable to injection
command = f"grep {user_input} /etc/passwd"

# GOOD - Use proper escaping or avoid user input
command = "grep 'fixed_value' /etc/passwd"
```

5. **Sensitive Data**: Don't log or display sensitive information (passwords, keys, tokens).

6. **Permissions**: Request only necessary permissions. Inform users if elevated privileges are needed.

## Testing and Debugging

### Manual Testing

```bash
# Test plugin discovery
plugin list

# Test plugin info
plugin info my-plugin

# Test execution on a safe test connection
plugin run my-plugin test-server

# Check plugin exit code
echo $?  # 0 = success, non-zero = failure
```

### Debugging Tips

1. **Print Debug Information**:

```python
import os
import sys

# Print all LazySSH env vars
print("DEBUG: Environment variables", file=sys.stderr)
for key, value in os.environ.items():
    if key.startswith("LAZYSSH_"):
        print(f"  {key}={value}", file=sys.stderr)
```

2. **Test Commands Locally**:

```bash
# Test SSH command directly
ssh -S /tmp/myserver -o ControlMaster=no user@host "uname -a"
```

3. **Check SSH Connection**:

```bash
# Verify control socket exists
ls -l /tmp/myserver

# Check SSH master connection
ssh -S /tmp/myserver -O check user@host
```

4. **Capture Full Output**:

```python
# Capture both stdout and stderr
result = subprocess.run(ssh_cmd, capture_output=True, text=True)
print(f"Exit Code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
```

## Examples

### Example 1: Simple System Info Plugin

```python
#!/usr/bin/env python3
# PLUGIN_NAME: sysinfo
# PLUGIN_DESCRIPTION: Display basic system information
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

import os
import subprocess
import sys

def run_command(cmd):
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")
    
    result = subprocess.run(
        ["ssh", "-S", socket_path, "-o", "ControlMaster=no", 
         f"{user}@{host}", cmd],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def main():
    print("=== System Information ===\n")
    print(f"Hostname: {run_command('hostname')}")
    print(f"OS: {run_command('cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2')}")
    print(f"Kernel: {run_command('uname -r')}")
    print(f"Uptime: {run_command('uptime -p 2>/dev/null || uptime')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Example 2: Port Scanner Plugin

```python
#!/usr/bin/env python3
# PLUGIN_NAME: portscan
# PLUGIN_DESCRIPTION: Scan for open ports on remote host
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: python3

import os
import subprocess
import sys

def scan_port(port):
    socket_path = os.environ.get("LAZYSSH_SOCKET_PATH")
    host = os.environ.get("LAZYSSH_HOST")
    user = os.environ.get("LAZYSSH_USER")
    
    # Use timeout to check if port is open
    cmd = f"timeout 1 bash -c '</dev/tcp/localhost/{port}' && echo 'open' || echo 'closed'"
    
    result = subprocess.run(
        ["ssh", "-S", socket_path, "-o", "ControlMaster=no",
         f"{user}@{host}", cmd],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "open"

def main():
    common_ports = [21, 22, 23, 25, 80, 443, 3306, 5432, 8080]
    
    print("=== Port Scan Results ===\n")
    for port in common_ports:
        status = "OPEN" if scan_port(port) else "closed"
        if status == "OPEN":
            print(f"Port {port}: {status}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Example 3: Shell Script Plugin

```bash
#!/bin/bash
# PLUGIN_NAME: diskcheck
# PLUGIN_DESCRIPTION: Check disk usage and alert if > 80%
# PLUGIN_VERSION: 1.0.0
# PLUGIN_REQUIREMENTS: bash

set -e

# Execute command on remote host
remote_exec() {
    ssh -S "$LAZYSSH_SOCKET_PATH" -o ControlMaster=no \
        "${LAZYSSH_USER}@${LAZYSSH_HOST}" "$@"
}

echo "=== Disk Usage Check ==="
echo

# Get disk usage
df_output=$(remote_exec "df -h | grep -v tmpfs")

echo "$df_output"
echo

# Check for high usage
while IFS= read -r line; do
    usage=$(echo "$line" | awk '{print $5}' | tr -d '%')
    mount=$(echo "$line" | awk '{print $6}')
    
    if [ "$usage" -gt 80 ] 2>/dev/null; then
        echo "⚠️  WARNING: $mount is ${usage}% full!"
    fi
done <<< "$df_output"

echo
echo "✓ Disk check complete"
```

## Additional Resources

- **Built-in Plugins**: Check `enumerate.py` for a comprehensive example
- **Template**: See `example_template.py` for a complete plugin template
- **LazySSH Documentation**: See main README.md for usage information

## Getting Help

If you encounter issues:

1. Check plugin metadata and permissions
2. Test SSH connection: `ssh -S /tmp/socket -O check user@host`
3. Run with debug mode: `debug` command in LazySSH
4. Check LazySSH logs for error messages

## Contributing

Want to share your plugin? Consider contributing it to LazySSH:

1. Ensure it follows best practices
2. Add comprehensive error handling
3. Include clear documentation
4. Test on multiple systems
5. Submit a pull request

---

Happy plugin development! 🚀
