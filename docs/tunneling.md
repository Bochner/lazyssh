# SSH Tunneling Guide

LazySSH provides powerful SSH tunneling capabilities for securely forwarding ports between your local machine and remote servers.

## Table of Contents

- [Tunnel Types](#tunnel-types)
- [Forward Tunnels](#forward-tunnels)
- [Reverse Tunnels](#reverse-tunnels)
- [Dynamic SOCKS Proxy](#dynamic-socks-proxy)
- [Managing Tunnels](#managing-tunnels)
- [Real-World Scenarios](#real-world-scenarios)
- [Troubleshooting](#troubleshooting)

## Tunnel Types

LazySSH supports three types of tunnels:

1. **Forward Tunnels (Local)**: Access remote services through local ports
2. **Reverse Tunnels (Remote)**: Expose local services through remote ports
3. **Dynamic SOCKS Proxy**: Flexible proxy for routing application traffic

## Forward Tunnels

Forward tunnels allow you to access services on a remote network through a local port.

### Creating Forward Tunnels

```bash
# Syntax
lazyssh> tunc <connection> l <local_port> <remote_host> <remote_port>

# Example: Access remote web server locally
lazyssh> tunc myserver l 8080 localhost 80
```

Now connect to `localhost:8080` to access the remote server's port 80.

### How It Works

```
Your Computer → localhost:8080 → SSH Tunnel → Remote Server → remote_host:80
```

### Common Uses

**Access remote web interface:**
```bash
lazyssh> tunc myserver l 8080 localhost 80
# Visit http://localhost:8080 in your browser
```

**Connect to remote database:**
```bash
lazyssh> tunc myserver l 3306 localhost 3306
# Connect your database client to localhost:3306
```

**Access service behind firewall:**
```bash
lazyssh> tunc myserver l 8080 internal-server 80
# Access internal-server:80 through your SSH connection
```

## Reverse Tunnels

Reverse tunnels allow remote machines to access services on your local machine.

### Creating Reverse Tunnels

```bash
# Syntax
lazyssh> tunc <connection> r <remote_port> <local_host> <local_port>

# Example: Expose local dev server remotely
lazyssh> tunc myserver r 8080 localhost 3000
```

Remote users can now access your local port 3000 via `remote_server:8080`.

### How It Works

```
Remote Server → remote_server:8080 → SSH Tunnel → Your Computer → localhost:3000
```

### Common Uses

**Share local development server:**
```bash
lazyssh> tunc myserver r 8080 localhost 3000
# Others can access your dev server at remote_server:8080
```

**Expose local service through VPS:**
```bash
lazyssh> tunc vps r 80 localhost 8080
# Your local service now accessible via VPS public IP
```

**Bypass NAT/firewall:**
```bash
lazyssh> tunc server r 2222 localhost 22
# Allow remote SSH access to your machine behind NAT
```

## Dynamic SOCKS Proxy

A dynamic SOCKS proxy provides flexible routing of application traffic through your SSH connection.

### Creating a SOCKS Proxy

Create a proxy when establishing your SSH connection:

```bash
# Default port (9050)
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy

# Custom port
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy 8080
```

### Using the SOCKS Proxy

**Configure Firefox:**
1. Settings → Network Settings → Manual proxy configuration
2. SOCKS Host: `localhost`
3. Port: `9050` (or your custom port)
4. Select SOCKS v5
5. Check "Proxy DNS when using SOCKS v5"

**Command-line tools:**
```bash
# curl
curl --socks5 localhost:9050 https://example.com

# wget
wget --socks-proxy=localhost:9050 https://example.com

# ssh
ssh -o ProxyCommand='nc -x localhost:9050 %h %p' user@destination
```

### Common Uses

- **Secure browsing on public Wi-Fi**: Route all browser traffic through encrypted tunnel
- **Access geo-restricted content**: Browse as if you're at your server's location
- **Bypass network restrictions**: Tunnel through firewalls and content filters
- **Protect sensitive traffic**: Encrypt data on untrusted networks

## Managing Tunnels

### Listing Tunnels

View all active connections and tunnels:

```bash
lazyssh> list
```

Shows:
- Connection names
- Tunnel IDs
- Tunnel types (forward/reverse)
- Port mappings
- SOCKS proxy status

### Deleting Tunnels

Remove a specific tunnel:

```bash
lazyssh> tund <tunnel_id>

# Example
lazyssh> tund 1
```

Get the tunnel ID from the `list` command output.

## Real-World Scenarios

### Secure Database Access

Access production database from local tools:

```bash
# Create connection
lazyssh> lazyssh -ip db-server.com -port 22 -user admin -socket proddb

# Forward database port
lazyssh> tunc proddb l 5432 localhost 5432

# Connect with local tools
# psql -h localhost -p 5432 -U dbuser production
```

### Development Server Sharing

Share your local work with remote team:

```bash
# Connect to VPS
lazyssh> lazyssh -ip vps.example.com -port 22 -user admin -socket myvps

# Expose local dev server
lazyssh> tunc myvps r 8080 localhost 3000

# Team accesses at: http://vps.example.com:8080
```

### Secure Remote Administration

Access web admin interface blocked by firewall:

```bash
# SSH to jump host
lazyssh> lazyssh -ip jump.corp.com -port 22 -user admin -socket jump

# Forward admin interface
lazyssh> tunc jump l 8443 admin-server 443

# Access at: https://localhost:8443
```

### Multi-Service Access

Access multiple services through one connection:

```bash
# Create connection
lazyssh> lazyssh -ip server.com -port 22 -user admin -socket multi

# Forward multiple ports
lazyssh> tunc multi l 8080 localhost 80       # Web
lazyssh> tunc multi l 3306 localhost 3306     # MySQL
lazyssh> tunc multi l 6379 localhost 6379     # Redis
lazyssh> tunc multi l 9200 localhost 9200     # Elasticsearch

# All services now accessible locally
```

### Secure Public Wi-Fi Usage

Browse safely on untrusted networks:

```bash
# Create connection with SOCKS proxy
lazyssh> lazyssh -ip home-server.com -port 22 -user admin -socket home -proxy

# Configure browser to use localhost:9050
# All traffic now encrypted through your home server
```

### Remote Docker Registry Access

Access private registry behind firewall:

```bash
# Forward registry port
lazyssh> tunc myserver l 5000 localhost 5000

# Use registry
# docker pull localhost:5000/myimage
```

## Troubleshooting

### Port Already in Use

**Problem:** "Address already in use" error

**Solution:**
```bash
# Check what's using the port
lsof -i:8080

# Use a different port
lazyssh> tunc myserver l 8081 localhost 80
```

### Connection Refused

**Problem:** Tunnel created but connection refused

**Solutions:**
- Verify remote service is running
- Check firewall rules on remote server
- Ensure correct host/port in tunnel command
- Verify SSH connection is active: `list`

### Remote Port Restricted

**Problem:** Can't bind to remote port <1024

**Solution:**
```bash
# Use high-numbered ports (>1024)
lazyssh> tunc myserver r 8080 localhost 80
```

### SOCKS Proxy Not Working

**Problem:** Applications can't connect through proxy

**Solutions:**
- Verify proxy is active: `list`
- Check application proxy settings
- Ensure SOCKS v5 is selected
- Enable "Proxy DNS" in browser settings
- Try with command-line tool first to isolate issue

### Tunnel Drops Frequently

**Problem:** Tunnel disconnects regularly

**Solutions:**
- Check SSH connection stability
- Verify network quality
- Consider adding SSH keep-alive:
  ```bash
  # In ~/.ssh/config
  Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
  ```

### Permission Denied

**Problem:** Can't create tunnel

**Solutions:**
- Verify SSH connection is active
- Check server allows port forwarding (`AllowTcpForwarding` in sshd_config)
- Ensure you have necessary permissions

## Quick Reference

### Forward Tunnel Examples

```bash
# Web server
tunc myserver l 8080 localhost 80

# Database
tunc myserver l 3306 db-internal 3306

# RDP
tunc myserver l 3389 windows-box 3389

# VNC
tunc myserver l 5900 localhost 5900
```

### Reverse Tunnel Examples

```bash
# Web server
tunc myserver r 8080 localhost 3000

# SSH access
tunc myserver r 2222 localhost 22

# Application API
tunc myserver r 8000 localhost 8000
```

### SOCKS Proxy

```bash
# Create with default port
lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy

# Create with custom port
lazyssh -ip server.com -port 22 -user admin -socket proxy -proxy 8080
```

For general command syntax, see [commands.md](commands.md).
