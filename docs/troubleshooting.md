# LazySSH Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using LazySSH.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Connection Problems](#connection-problems)
- [Terminal Emulator Issues](#terminal-emulator-issues)
- [Tunneling Troubles](#tunneling-troubles)
- [SCP Mode Difficulties](#scp-mode-difficulties)
- [Graceful Shutdown Problems](#graceful-shutdown-problems)
- [Common Error Messages](#common-error-messages)

## Installation Issues

### Command Not Found

**Issue**: After installing LazySSH, you get a "command not found" error when trying to run it.

**Solution**:
- If you installed with `pip install --user`, add the user bin directory to your PATH:
  ```bash
  # Add to PATH temporarily
  export PATH="$HOME/.local/bin:$PATH"
  
  # Add permanently (for bash)
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```

### Missing Dependencies

**Issue**: Error about missing dependencies when starting LazySSH.

**Solution**:
- Install the required Terminator terminal emulator:
  ```bash
  # Ubuntu/Debian
  sudo apt install terminator
  
  # Fedora
  sudo dnf install terminator
  
  # RHEL/CentOS
  sudo yum install terminator
  ```

### Version Compatibility

**Issue**: Error messages about incompatible Python versions.

**Solution**:
- Ensure you're using Python 3.7 or higher:
  ```bash
  python3 --version
  ```
- If needed, install or upgrade Python:
  ```bash
  # Ubuntu/Debian
  sudo apt install python3
  
  # Upgrading pip
  python3 -m pip install --upgrade pip
  ```

## Connection Problems

### Authentication Failures

**Issue**: "Permission denied" errors when trying to connect.

**Solutions**:
1. Double-check username and password
2. Verify SSH key permissions:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   ```
3. Try connecting manually to debug:
   ```bash
   ssh -v username@host
   ```

### Socket File Errors

**Issue**: Errors related to socket files like "No such file or directory".

**Solutions**:
1. Check if socket files exist in `/tmp/`:
   ```bash
   ls -la /tmp/
   ```
2. Ensure proper permissions on the `/tmp/` directory:
   ```bash
   ls -ld /tmp/
   ```
3. Try closing and recreating the connection

### Connection Timeouts

**Issue**: SSH connection attempts time out.

**Solutions**:
1. Verify the server is reachable:
   ```bash
   ping hostname
   ```
2. Check if the SSH port is open:
   ```bash
   nc -zv hostname 22
   ```
3. Ensure no firewall is blocking the connection

## Terminal Emulator Issues

### Terminator Not Found

**Issue**: "Terminator not found" or similar error.

**Solution**:
- Install Terminator:
  ```bash
  sudo apt install terminator
  ```
- Or configure LazySSH to use a different terminal:
  ```bash
  export LAZYSSH_TERMINAL=gnome-terminal
  ```

### Terminal Doesn't Open

**Issue**: Terminal fails to open after connecting.

**Solutions**:
1. Check if the terminal emulator is working:
   ```bash
   terminator --version
   ```
2. Try setting a different terminal emulator:
   ```bash
   export LAZYSSH_TERMINAL=xterm
   ```
3. Manually open a terminal using the displayed command

## Tunneling Troubles

### Port Already in Use

**Issue**: "Address already in use" error when creating a tunnel.

**Solutions**:
1. Find what's using the port:
   ```bash
   sudo lsof -i:8080
   ```
2. Use a different port number:
   ```bash
   tunc myserver l 8081 localhost 80
   ```

### Tunnels Not Working

**Issue**: Tunnel is created but doesn't work.

**Solutions**:
1. Verify the tunnel is active with `list`
2. Check if the remote server allows port forwarding
3. Verify your application is connecting to the correct port
4. Check firewall rules on both local and remote systems

### SOCKS Proxy Connection Failed

**Issue**: Applications can't connect through your SOCKS proxy.

**Solutions**:
1. Verify the proxy is running with `list`
2. Ensure correct settings in your application (localhost, correct port)
3. For Firefox, enable "Proxy DNS when using SOCKS v5"
4. Try a different port number if necessary

## SCP Mode Difficulties

### File Transfer Fails

**Issue**: File transfer in SCP mode fails with errors.

**Solutions**:
1. Check file permissions on both systems
2. Verify paths exist on both systems
3. Try simpler relative paths
4. Check disk space on destination

### SCP Performance Issues

**Issue**: File transfers are slow.

**Solutions**:
1. Check your network connection speed
2. Try transferring smaller files
3. Consider using compression for text files
4. Verify the SSH connection is stable

### Path Resolution Problems

**Issue**: Files can't be found or paths don't resolve correctly.

**Solutions**:
1. Use absolute paths to avoid ambiguity
2. Check current working directories with `pwd` and `local`
3. Verify file existence before transfer
4. Be careful with special characters in filenames

## Graceful Shutdown Problems

### Connections Not Closing

**Issue**: SSH connections remain active after exiting LazySSH.

**Solutions**:
1. Use the `exit` command instead of killing the terminal
2. Manually close connections with `close` before exiting
3. Check for socket files in `/tmp/` and remove them:
   ```bash
   rm /tmp/connection_name
   ```

### Socket Files Not Cleaned Up

**Issue**: Socket files remain in `/tmp/` after exit.

**Solution**:
- Manually remove the socket files:
  ```bash
  rm /tmp/connection_name
  ```

## Common Error Messages

### "Control socket connect(...): No such file or directory"

**Causes**:
- The socket file doesn't exist or has been deleted
- Permission issues with the socket file
- Path to the socket file is incorrect

**Solutions**:
1. Close and recreate the connection
2. Check for socket file existence
3. Verify permissions on the socket file

### "Channel setup failed: ..." (During tunneling)

**Causes**:
- Remote server restricts port forwarding
- Port already in use
- Server firewall blocking the connection

**Solutions**:
1. Try a different port number
2. Check server SSH configuration
3. Verify firewall rules

### "Permission denied" (During file transfer)

**Causes**:
- Insufficient permissions for reading/writing files
- SSH key issues
- Path doesn't exist or isn't accessible

**Solutions**:
1. Check file permissions
2. Verify paths exist on both systems
3. Try running with sudo if appropriate
4. Check SSH key permissions

### "unix_listener: ... too long for Unix domain socket"

**Causes**:
- Socket path exceeds the maximum allowed length

**Solution**:
- Use a shorter connection name with `-socket`

### "Warning: Permanently added ... to the list of known hosts"

**Information**:
- This is normal behavior when connecting to a new server
- The server's key is being added to your known hosts file

**Action**:
- No action needed, this is expected 