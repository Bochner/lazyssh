# SSH Tunneling Guide

LazySSH provides powerful SSH tunneling capabilities that allow you to securely forward ports between your local machine and remote servers. This guide explains the different tunneling options and how to use them effectively.

## Table of Contents

- [Understanding SSH Tunnels](#understanding-ssh-tunnels)
- [Forward Tunnels](#forward-tunnels)
- [Reverse Tunnels](#reverse-tunnels)
- [Dynamic SOCKS Proxy](#dynamic-socks-proxy)
- [Managing Tunnels](#managing-tunnels)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

## Understanding SSH Tunnels

SSH tunneling creates an encrypted connection between ports on different machines, allowing secure data transfer through potentially insecure networks. LazySSH supports three main types of tunnels:

1. **Forward Tunnels**: Forward a local port to a remote server (local → remote)
2. **Reverse Tunnels**: Forward a remote port to your local machine (remote → local)
3. **Dynamic SOCKS Proxy**: Create a flexible SOCKS proxy through your SSH connection

## Forward Tunnels

Forward tunnels (local port forwarding) allow you to access a service on a remote network through a local port on your machine.

### Creating a Forward Tunnel

```bash
# Syntax
lazyssh> tunc <connection_name> l <local_port> <remote_host> <remote_port>

# Example: Forward local port 8080 to port 80 on the remote server
lazyssh> tunc myserver l 8080 localhost 80
```

**Parameters:**
- `connection_name`: Name of your SSH connection
- `l`: Specifies a local/forward tunnel
- `local_port`: The port on your local machine that will forward to the remote port
- `remote_host`: The destination host from the perspective of the SSH server
- `remote_port`: The port on the remote host to connect to

### How Forward Tunnels Work

```
[Your Computer] → [Local Port 8080] → [SSH Connection] → [Remote Server] → [Remote Host:Port 80]
```

When you connect to `localhost:8080` on your machine, the connection is tunneled through SSH to `remote_host:80` as seen from the perspective of the remote server.

### Common Forward Tunnel Use Cases

- Accessing a remote web server securely (`localhost:8080` → `remote:80`)
- Connecting to a database server behind a firewall (`localhost:3306` → `database_server:3306`)
- Accessing a remote service that is only bound to localhost on the remote server

## Reverse Tunnels

Reverse tunnels (remote port forwarding) allow remote machines to access a service on your local machine through a port on the remote server.

### Creating a Reverse Tunnel

```bash
# Syntax
lazyssh> tunc <connection_name> r <remote_port> <local_host> <local_port>

# Example: Forward remote port 8080 to port 3000 on your local machine
lazyssh> tunc myserver r 8080 localhost 3000
```

**Parameters:**
- `connection_name`: Name of your SSH connection
- `r`: Specifies a remote/reverse tunnel
- `remote_port`: The port on the remote server that will forward to your local port
- `local_host`: The destination host from the perspective of your local machine
- `local_port`: The port on your local machine to connect to

### How Reverse Tunnels Work

```
[Remote Server] → [Remote Port 8080] → [SSH Connection] → [Your Computer] → [Local Port 3000]
```

When someone connects to port 8080 on the remote server, the connection is tunneled back through SSH to port 3000 on your machine.

### Common Reverse Tunnel Use Cases

- Sharing a local development server with others
- Exposing a local web server through a remote VPS with a public IP
- Allowing remote access to a service behind a NAT or firewall

## Dynamic SOCKS Proxy

A dynamic SOCKS proxy provides a flexible way to route traffic through your SSH connection, allowing applications to access various services through the remote server.

### Creating a Dynamic SOCKS Proxy

You create a dynamic SOCKS proxy when establishing an SSH connection:

```bash
# With default port (9050)
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy

# With custom port
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -proxy 8080
```

### Using the SOCKS Proxy

Once created, you can configure applications to use your SOCKS proxy:

**Web Browser (Firefox):**
1. Go to Settings/Preferences
2. Search for "proxy"
3. Configure manual proxy settings
4. Set SOCKS Host to "localhost" and Port to "9050" (or your custom port)
5. Select "SOCKS v5"

**Command Line Tools:**
```bash
# curl example
curl --socks5 localhost:9050 https://example.com

# wget example
wget --socks-proxy=localhost:9050 https://example.com
```

### Common SOCKS Proxy Use Cases

- Secure browsing through an encrypted tunnel
- Accessing region-restricted content through a server in another location
- Bypassing network restrictions by tunneling through SSH
- Protecting your traffic on untrusted networks

## Managing Tunnels

### Listing Tunnels

To view all active tunnels:

```bash
lazyssh> list
```

This displays:
- Tunnel ID
- Type (forward or reverse)
- Local port
- Remote host and port
- The connection they belong to

### Deleting Tunnels

To remove a tunnel:

```bash
# Syntax
lazyssh> tund <tunnel_id>

# Example
lazyssh> tund 1
```

The tunnel ID is shown in the output of the `list` command.

## Common Use Cases

### Accessing a Remote Database

```bash
# Create a connection
lazyssh> lazyssh -ip database.example.com -port 22 -user dbadmin -socket dbserver

# Forward local port 3306 to the database port on the remote server
lazyssh> tunc dbserver l 3306 localhost 3306

# Now you can connect to the database using: localhost:3306
```

### Exposing a Local Development Server

```bash
# Create a connection to your VPS
lazyssh> lazyssh -ip vps.example.com -port 22 -user admin -socket myvps

# Create a reverse tunnel from VPS port 8080 to your local development server
lazyssh> tunc myvps r 8080 localhost 3000

# Now people can access your development server at: vps.example.com:8080
```

### Secure Browsing on Public Wi-Fi

```bash
# Create a connection with a SOCKS proxy
lazyssh> lazyssh -ip home.example.com -port 22 -user user -socket home -proxy

# Configure your browser to use the SOCKS proxy at localhost:9050
# Now your browsing traffic is encrypted through your home server
```

## Troubleshooting

### Tunnel Creation Failures

If you encounter errors when creating tunnels:

1. **Port already in use**: Try a different local port
   ```bash
   # If port 8080 fails with "address already in use"
   lazyssh> tunc myserver l 8081 localhost 80
   ```

2. **Remote port restricted**: Some remote ports (<1024) require root privileges
   ```bash
   # Try using a higher port number
   lazyssh> tunc myserver r 8080 localhost 80
   ```

3. **Connection issues**: Verify the SSH connection is active
   ```bash
   lazyssh> list
   ```

### SOCKS Proxy Problems

If your SOCKS proxy isn't working:

1. **Verify proxy is active**: Check that the connection with SOCKS is running
   ```bash
   lazyssh> list
   ```

2. **Check application configuration**: Ensure your application is correctly configured to use the SOCKS proxy

3. **DNS resolution**: Some applications need to be configured to resolve DNS through the proxy (e.g., Firefox's "Proxy DNS when using SOCKS v5" option)

### Performance Issues

If tunnel performance is slow:

1. **Compression**: SSH compression may help with text-heavy traffic
2. **Multiple tunnels**: Avoid creating too many tunnels through a single connection
3. **Connection quality**: The tunnel can only be as fast as your SSH connection 