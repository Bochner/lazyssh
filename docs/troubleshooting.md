# LazySSH Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using LazySSH.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Platform Support](#platform-support)
- [Connection Problems](#connection-problems)
- [Terminal Issues](#terminal-issues)
- [Tunneling Problems](#tunneling-problems)
- [SCP Mode Issues](#scp-mode-issues)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### Command Not Found

**Issue**: After installing LazySSH, you get a "command not found" error.

**Solution**:
```bash
# Add user bin directory to PATH
export PATH="$HOME/.local/bin:$PATH"

# Make it permanent (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Make it permanent (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Missing Required Dependencies

**Issue**: Error about missing OpenSSH client.

**Solution**:
```bash
# Ubuntu/Debian
sudo apt install openssh-client

# Fedora/RHEL
sudo dnf install openssh-clients

# macOS (usually pre-installed)
# Verify with: ssh -V
```

### Optional Dependency Notice

**Not an error**: Warning about Terminator being missing.

LazySSH will work perfectly with the native terminal method. Terminator is optional.

**To install Terminator (optional):**
```bash
# Ubuntu/Debian
sudo apt install terminator

# Fedora/RHEL
sudo dnf install terminator

# macOS
brew install terminator
```

### Version Compatibility

**Issue**: Incompatible Python version errors.

**Solution**:
```bash
# Check Python version (need 3.11+)
python3 --version

# Ubuntu/Debian
sudo apt install python3.11

# Upgrade pip
python3 -m pip install --upgrade pip
```

## Platform Support

### Linux

Full support for all LazySSH features.

### macOS

Full support for all LazySSH features.

**Note**: Terminator is optional. LazySSH works great with native terminal using Terminal.app, iTerm2, or any other terminal emulator.

### Windows

**Important**: LazySSH requires Windows Subsystem for Linux (WSL).

Windows OpenSSH does not support SSH control sockets (master mode `-M` flag), which is essential for LazySSH's persistent connection functionality.

**Setup LazySSH on Windows:**
1. Install WSL:
   ```powershell
   wsl --install
   ```
2. Restart your computer if required
3. Open WSL (Ubuntu or your preferred distribution)
4. Install LazySSH in WSL:
   ```bash
   pip install lazyssh
   ```
5. Use LazySSH normally within WSL

## Connection Problems

### Authentication Failures

**Issue**: "Permission denied" errors when connecting.

**Solutions**:

1. Verify credentials are correct
2. Check SSH key permissions:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   chmod 644 ~/.ssh/id_rsa.pub
   ```
3. Test connection manually:
   ```bash
   ssh -v username@host
   ```
4. Verify SSH key is added to remote authorized_keys:
   ```bash
   ssh-copy-id username@host
   ```

### Socket File Errors

**Issue**: "No such file or directory" errors related to sockets.

**Solutions**:

1. Check if socket files exist:
   ```bash
   ls -la /tmp/
   ```
2. Verify `/tmp/` directory permissions:
   ```bash
   ls -ld /tmp/
   ```
3. Close and recreate the connection:
   ```bash
   lazyssh> close myserver
   lazyssh> lazyssh -ip host -port 22 -user admin -socket myserver
   ```

### Connection Timeouts

**Issue**: SSH connection attempts time out.

**Solutions**:

1. Verify server is reachable:
   ```bash
   ping hostname
   ```
2. Check if SSH port is open:
   ```bash
   nc -zv hostname 22
   ```
3. Check firewall rules
4. Verify network connectivity

## Terminal Issues

### Choosing Terminal Method

You can use either native or Terminator terminal method.

**Configure terminal method:**

```bash
# Runtime (recommended)
lazyssh> terminal native      # Use native terminal
lazyssh> terminal terminator  # Use Terminator
lazyssh> terminal auto        # Auto-select

# Environment variable
export LAZYSSH_TERMINAL_METHOD=native     # Force native
export LAZYSSH_TERMINAL_METHOD=terminator # Force Terminator
export LAZYSSH_TERMINAL_METHOD=auto       # Auto-select (default)
```

### Native Terminal Issues

**Issue**: Terminal doesn't open or behaves unexpectedly.

**Solutions**:

1. Verify SSH client is working:
   ```bash
   ssh -V
   ```
2. Test SSH connection manually:
   ```bash
   ssh username@host
   ```
3. Check LazySSH connection is active:
   ```bash
   lazyssh> list
   ```
4. Try recreating the connection

**Expected Behavior**: With native terminal, you can exit the SSH session (using `exit` or Ctrl+D) and return to LazySSH. The SSH connection remains active.

### Terminator Issues

**Issue**: Terminator fails to open terminals.

**Solutions**:

1. Verify Terminator is installed:
   ```bash
   terminator --version
   ```
2. Test Terminator manually:
   ```bash
   terminator
   ```
3. Switch to native terminal if Terminator has issues:
   ```bash
   lazyssh> terminal native
   ```
4. Check Terminator configuration

### Terminal Method Not Changing

**Issue**: Terminal method doesn't seem to change.

**Solution**:

The terminal method setting applies to new terminal sessions only. Already-open terminals are not affected. The current method is shown in the `list` command output.

## Tunneling Problems

### Port Already in Use

**Issue**: "Address already in use" error when creating tunnel.

**Solutions**:

1. Find what's using the port:
   ```bash
   sudo lsof -i:8080
   ```
2. Use a different port:
   ```bash
   lazyssh> tunc myserver l 8081 localhost 80
   ```
3. Kill the process using the port (if safe to do so):
   ```bash
   kill <PID>
   ```

### Tunnel Not Working

**Issue**: Tunnel created but connections fail.

**Solutions**:

1. Verify tunnel is active:
   ```bash
   lazyssh> list
   ```
2. Check remote service is running
3. Verify firewall rules on both local and remote
4. Test with simple command:
   ```bash
   curl localhost:8080
   ```
5. Check server SSH config allows port forwarding:
   ```
   # In /etc/ssh/sshd_config
   AllowTcpForwarding yes
   ```

### SOCKS Proxy Connection Failed

**Issue**: Applications can't connect through SOCKS proxy.

**Solutions**:

1. Verify proxy is running:
   ```bash
   lazyssh> list
   # Check Dynamic Port column
   ```
2. Check application proxy settings:
   - Host: `localhost`
   - Port: `9050` (or your custom port)
   - Type: SOCKS v5
3. For Firefox, enable "Proxy DNS when using SOCKS v5"
4. Test with curl:
   ```bash
   curl --socks5 localhost:9050 https://example.com
   ```

### Remote Port Restrictions

**Issue**: Can't bind to ports < 1024 on remote server.

**Solution**:

Use high-numbered ports (> 1024):
```bash
lazyssh> tunc myserver r 8080 localhost 80
```

## SCP Mode Issues

### File Transfer Fails

**Issue**: File transfer fails with errors.

**Solutions**:

1. Check file permissions on both systems
2. Verify paths exist:
   ```bash
   scp myserver> pwd
   scp myserver> local
   ```
3. Use absolute paths to avoid ambiguity
4. Check disk space on destination:
   ```bash
   df -h
   ```
5. Verify SSH connection is active:
   ```bash
   scp myserver> exit
   lazyssh> list
   ```

### Cannot Change Directory

**Issue**: `cd` command fails or permission denied.

**Solutions**:

1. Verify directory exists:
   ```bash
   scp myserver> ls /path/to/directory
   ```
2. Check permissions:
   ```bash
   scp myserver> ls -ld /path/to/directory
   ```
3. Use absolute paths
4. Try parent directory and work down

### Tree Command Slow or Freezes

**Issue**: `tree` command takes very long or appears frozen.

**Solutions**:

1. Use on specific subdirectories instead of root:
   ```bash
   scp myserver> tree /home/user/project
   ```
2. Wait for completion (large directories take time)
3. Use `ls` for quick directory view
4. Check you have permissions for all subdirectories

### File Listing Shows No Results

**Issue**: `ls` command shows nothing.

**Solutions**:

1. Verify you're in the right directory:
   ```bash
   scp myserver> pwd
   ```
2. Check permissions:
   ```bash
   scp myserver> ls -la
   ```
3. Try absolute path:
   ```bash
   scp myserver> ls /home/user
   ```

### Path Resolution Problems

**Issue**: Files can't be found or paths don't work.

**Solutions**:

1. Use absolute paths to avoid confusion
2. Check current directories:
   ```bash
   scp myserver> pwd
   scp myserver> local
   ```
3. Verify file exists:
   ```bash
   scp myserver> ls -l /path/to/file
   ```
4. Watch for special characters in filenames

## Common Error Messages

### "Control socket connect(...): No such file or directory"

**Causes**:
- Socket file doesn't exist or was deleted
- Permission issues with socket file
- Incorrect socket path

**Solutions**:

1. Close and recreate connection:
   ```bash
   lazyssh> close myserver
   lazyssh> lazyssh -ip host -port 22 -user admin -socket myserver
   ```
2. Check socket file exists:
   ```bash
   ls -la /tmp/
   ```
3. Verify permissions on socket file

### "Channel setup failed: ..." (Tunneling)

**Causes**:
- Remote server restricts port forwarding
- Port already in use
- Firewall blocking connection

**Solutions**:

1. Try different port
2. Check server SSH config
3. Verify firewall rules
4. Ensure `AllowTcpForwarding yes` in sshd_config

### "Permission denied" (File Transfer)

**Causes**:
- Insufficient file permissions
- SSH key issues
- Path doesn't exist or isn't accessible

**Solutions**:

1. Check file permissions:
   ```bash
   ls -l /path/to/file
   ```
2. Verify SSH connection is working
3. Check SSH key permissions (600 for private key)
4. Try with absolute paths

### "unix_listener: ... too long for Unix domain socket"

**Cause**: Socket path exceeds maximum allowed length.

**Solution**:

Use a shorter connection name:
```bash
# Instead of
lazyssh> lazyssh -ip host -port 22 -user admin -socket my-very-long-server-name

# Use
lazyssh> lazyssh -ip host -port 22 -user admin -socket server1
```

### "Warning: Permanently added ... to the list of known hosts"

**Information**: This is normal when connecting to a new server for the first time.

The server's key is being added to your `~/.ssh/known_hosts` file. No action needed.

## Getting More Help

If you continue to experience issues:

1. Enable debug mode:
   ```bash
   lazyssh> debug
   ```
2. Check log files:
   ```bash
   ls -la /tmp/lazyssh/logs/
   ```
3. Test SSH connection manually:
   ```bash
   ssh -v username@host
   ```
4. Review the user guide and command reference
5. Check GitHub issues for similar problems
6. Create a new GitHub issue with:
   - LazySSH version
   - Operating system
   - Error message
   - Steps to reproduce

For general usage questions, see:
- [User Guide](user-guide.md)
- [Command Reference](commands.md)
- [SCP Mode Guide](scp-mode.md)
- [Tunneling Guide](tunneling.md)
