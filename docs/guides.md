# LazySSH Guides

Short recipes for advanced use-cases. Each section builds on the basics covered in `docs/getting-started.md`.

## Tunnelling Patterns
### Forward (Local) Tunnels
Expose a remote service on your local machine:
```bash
lazyssh> tunc web l 8080 localhost 80
# Visit http://localhost:8080 locally
```

### Reverse Tunnels
Expose a local service to the remote host:
```bash
lazyssh> tunc web r 3000 localhost 8080
# Remote host reaches http://localhost:3000 -> your local port 8080
```

### Dynamic SOCKS Proxy
Combine a connection with `-proxy` to route browser traffic through SSH:
```bash
lazyssh> lazyssh -ip bastion.example.com -port 22 -user admin -socket proxy -proxy
# Configure applications to use SOCKS proxy localhost:9050
```

### Tunnels at a Glance
- Use `list` to view tunnel IDs and statuses.
- Use `tund <id>` to remove a tunnel without dropping the connection.
- Forward tunnels show traffic direction `localhost -> remote`. Reverse tunnels invert it.

## File Transfer Workflows
### Choose Download & Upload Directories
```bash
scp prod> local               # Display current local directories
scp prod> local /tmp/downloads
```

### Batch Downloads
```bash
scp prod> mget logs/*.log
# Confirms file list, total size, then downloads with progress bars
```

### Directory Trees & Filtering
```bash
scp prod> tree /var/www
scp prod> ls -l /var/www | grep ".log"
```

### Resuming Transfers
`get` and `put` automatically overwrite files after confirmation. For large files, keep connections active to take advantage of the underlying control socket.

## Automation with Plugins
LazySSH runs local Python or shell scripts that reuse existing control sockets.

### Where Plugins Live
Search order (first match wins):
1. Directories specified in `LAZYSSH_PLUGIN_DIRS` (colon-separated)
2. `~/.lazyssh/plugins`
3. `/tmp/lazyssh/plugins` (created on startup)
4. Packaged `lazyssh/plugins/` directory

### Create a Plugin
```bash
mkdir -p ~/.lazyssh/plugins
cat <<'PY' > ~/.lazyssh/plugins/uptime.py
#!/usr/bin/env python3
# PLUGIN_NAME: uptime
# PLUGIN_DESCRIPTION: Collect uptime and load information
# PLUGIN_VERSION: 1.0.0

import os
import subprocess

host = os.environ["LAZYSSH_HOST"]
user = os.environ["LAZYSSH_USER"]
socket_path = os.environ["LAZYSSH_SOCKET_PATH"]

result = subprocess.run(
    ["ssh", "-S", socket_path, f"{user}@{host}", "uptime"],
    check=True,
    capture_output=True,
    text=True,
)
print(result.stdout.strip())
PY
chmod +x ~/.lazyssh/plugins/uptime.py
```
Run it:
```bash
lazyssh> plugin run uptime myserver
```
See `docs/reference.md` for the full environment variable list and explore `docs/Plugin/example_template.py` for a more comprehensive template.

### Tips
- Use `plugin info <name>` to verify metadata and execution permissions.
- Plugins inherit your local environment (PATH, python modules, etc.).
- Keep plugins idempotent; they may run multiple times during automation workflows.
