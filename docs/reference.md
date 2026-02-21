# LazySSH Reference

Concise reference for commands, flags, environments, and configuration used across LazySSH.

## CLI Flags
| Flag | Description |
|------|-------------|
| `--debug` | Enable verbose logging to the console (also writes to `/tmp/lazyssh/logs`) |
| `--config /path/to/connections.conf` | Load and display saved configurations on startup. Use `/tmp/lazyssh/connections.conf` for the default file. |

## Command Mode
| Command | Description |
|---------|-------------|
| `lazyssh -ip <host> -port <port> -user <user> -socket <name> [-ssh-key <path>] [-proxy [port]] [-shell <name>] [-no-term]` | Establish a new SSH control socket. `-proxy` without a value uses port `9050`. |
| `list` | Show active connections plus their tunnels. |
| `open <name>` | Open a shell session for the named connection using the configured terminal method. |
| `close <name>` | Close the connection and clean up its control socket. |
| `terminal <auto|native|terminator>` | Switch terminal method at runtime. |
| `wizard lazyssh` / `wizard tunnel` | Interactive wizards for connection or tunnel setup. |
| `help [command]` | Display help for the main prompt. |
| `clear` | Clear the terminal screen. |
| `exit` / `quit` | Exit LazySSH (closes active connections after confirmation). |
| `debug` | Toggle runtime debug logging. |

### Configuration Commands
| Command | Description |
|---------|-------------|
| `config` / `configs` | Show saved configurations from `/tmp/lazyssh/connections.conf`. |
| `save-config <name>` | Persist the most recent connection parameters under `<name>`. |
| `connect <name>` | Recreate a connection from a saved configuration. |
| `delete-config <name>` | Remove a stored configuration (asks for confirmation). |
| `backup-config` | Create a timestamped backup copy of the config file in `/tmp/lazyssh`. |

### Tunnels
| Command | Description |
|---------|-------------|
| `tunc <name> l <local_port> <remote_host> <remote_port>` | Forward/local tunnel (local → remote). |
| `tunc <name> r <remote_port> <local_host> <local_port>` | Reverse tunnel (remote → local). |
| `tund <tunnel_id>` | Remove a tunnel by ID (see `list` output). |

### Plugins
| Command | Description |
|---------|-------------|
| `plugin` / `plugin list` | List discovered plugins. |
| `plugin info <name>` | Display metadata and validation status for a plugin. |
| `plugin run <name> <connection>` | Execute a plugin using the specified connection's control socket. |

#### Built-In `enumerate` Plugin
- Collects system, user, network, filesystem, and security telemetry with a single batched remote script to minimize round trips.
- **Quick Wins** section at the top groups exploitable findings by difficulty tier (Instant, Easy, Moderate) with actionable exploit commands prefixed by `$`.
- **Priority Findings** table with severity badges (critical, high, medium, info), inline exploit commands, and up to 4 evidence items per finding.
- **Category panels** with color-coded borders: red for categories containing critical findings, yellow for probe failures, green for clean categories.
- Human-friendly probe display names (e.g., "SUID Binaries" instead of `suid`) with raw key shown in dim text.
- GTFOBins cross-reference for SUID binaries, sudo-allowed commands, and capabilities.
- Kernel exploit suggester matching ~15 CVEs against the running kernel version.
- Full plain-text parity for all Rich features (accessible via `LAZYSSH_PLAIN_TEXT=true`).
- Persists both `survey_<timestamp>.json` (structured payload with `priority_findings`) and a plain-text summary in the connection log directory for later triage.
- Use `--json` for machine-readable structured output.

## SCP Mode Commands
Enter with `scp <connection>` or simply `scp` to choose from active connections.

| Command | Description |
|---------|-------------|
| `ls [path]` | List remote directory contents. |
| `tree [path]` | Show a remote directory tree. |
| `cd <path>` / `pwd` | Change or display the remote working directory. |
| `lcd <path>` / `local [path]` | Change or display the local transfer directory. |
| `get <remote> [local]` | Download a file. |
| `put <local> [remote]` | Upload a file. |
| `mget <pattern>` | Batch download using glob patterns (asks for confirmation). |
| `lls [path]` | List local files. |
| `debug` | Toggle verbose transfer logging while in SCP mode. |
| `help [command]` | Show SCP-mode help. |
| `exit` | Return to command mode. |

## Environment Variables (User Configurable)
| Variable | Purpose | Default |
|----------|---------|---------|
| `LAZYSSH_TERMINAL_METHOD` | Preferred terminal method (`auto`, `native`, `terminator`). | `auto` |
| `LAZYSSH_SSH_PATH` | Override the path to the `ssh` binary. | `/usr/bin/ssh` |
| `LAZYSSH_TERMINAL` | Override the Terminator binary name/path. | `terminator` |
| `LAZYSSH_CONTROL_PATH` | Base directory for control sockets. | `/tmp/` |
| `LAZYSSH_HIGH_CONTRAST` | Use the high-contrast theme (`true`/`false`). | `false` |
| `LAZYSSH_COLORBLIND_MODE` | Use the colorblind-friendly theme. | `false` |
| `LAZYSSH_NO_RICH` | Disable Rich formatting (forces basic output). | `false` |
| `LAZYSSH_PLAIN_TEXT` | Plain text mode that overrides all visual theming. | `false` |
| `LAZYSSH_NO_ANIMATIONS` | Disable progress bars and animations. | `false` |
| `LAZYSSH_REFRESH_RATE` | Refresh interval for live tables (1-10). | `4` |
| `LAZYSSH_PLUGIN_DIRS` | Colon-separated list of extra plugin directories. | *(empty)* |
| `LAZYSSH_LOG_LEVEL` | Logging level (`DEBUG`, `INFO`, etc.). | `INFO` |

## Environment Variables Exposed to Plugins
LazySSH injects these variables when running a plugin so scripts can access connection metadata.

| Variable | Description |
|----------|-------------|
| `LAZYSSH_SOCKET` | Short connection name (socket identifier). |
| `LAZYSSH_SOCKET_PATH` | Full path to the control socket file. |
| `LAZYSSH_HOST` | Remote host name or IP. |
| `LAZYSSH_PORT` | Remote SSH port. |
| `LAZYSSH_USER` | SSH username. |
| `LAZYSSH_SSH_KEY` | SSH key path if one was specified. |
| `LAZYSSH_SHELL` | Preferred shell if configured. |
| `LAZYSSH_PLUGIN_API_VERSION` | Plugin API version (`1`). |

## Connections Configuration File
LazySSH stores saved connections in `/tmp/lazyssh/connections.conf` (permissions `600`). Keys map directly to the parameters accepted by the `lazyssh` command.

| Key | Required | Description |
|-----|----------|-------------|
| `host` | ✅ | SSH host name or IP address. |
| `port` | ✅ | SSH port number. |
| `username` | ✅ | SSH username. |
| `socket_name` | ✅ | Name used for the control socket (maps to `/tmp/<socket_name>`). |
| `ssh_key` | ❌ | Path to a private key file. |
| `shell` | ❌ | Preferred shell when opening terminals. |
| `no_term` | ❌ | `true` to skip terminal allocation. |
| `proxy_port` | ❌ | Port number for a dynamic SOCKS proxy. |

Example:
```toml
[prod]
host = "server.example.com"
port = 22
username = "admin"
socket_name = "prod"
ssh_key = "~/.ssh/id_ed25519"
proxy_port = 9050
```
