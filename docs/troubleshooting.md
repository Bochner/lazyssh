# Troubleshooting LazySSH

Quick fixes for the most common problems. If an issue persists, run LazySSH with `--debug` or toggle `lazyssh> debug` and review `/tmp/lazyssh/logs/`.

## Installation & Launch
### `lazyssh: command not found`
- Ensure `pipx` (recommended) or `pip` installation succeeded.
- If you used `pip install --user`, add `~/.local/bin` to your PATH:
  ```bash
  export PATH="$HOME/.local/bin:$PATH"
  ```

### Missing OpenSSH client
- Install the system package (e.g., `sudo apt install openssh-client` or `brew install openssh`).
- Re-run LazySSH; it will exit if the required dependency is still missing.

## Terminal & UI
### Terminator not available
- LazySSH falls back to the native terminal automatically.
- Force a specific method at runtime: `lazyssh> terminal native`.
- To prefer Terminator when installed, set `LAZYSSH_TERMINAL_METHOD=terminator`.

### Colors look wrong or unreadable
- Enable high contrast: `export LAZYSSH_HIGH_CONTRAST=true`.
- For plain text output: `export LAZYSSH_PLAIN_TEXT=true` or toggle `LAZYSSH_NO_RICH=true`.

## Connections
### SSH connection fails immediately
- Confirm host, port, and username are correct.
- Test with standard SSH: `ssh user@host -p port`.
- When using keys, ensure file permissions are correct (`chmod 600`).
- Check `lazyssh> debug` output for exact SSH errors.

### Saved configs do not appear
- Run `lazyssh --config /tmp/lazyssh/connections.conf` to load the default file.
- Confirm the file exists and has permissions `600`.
- Use `lazyssh> save-config name` after successfully creating a connection.

## Tunnels
### Tunnel created but traffic fails
- Verify the tunnel direction (`l` for forward, `r` for reverse).
- Ensure the target host/port is reachable from the remote side.
- Some remote services bind to 127.0.0.1; use the correct host in the command (e.g., `localhost`).
- Run `lazyssh> list` to confirm the tunnel is still active.

### SOCKS proxy not reachable
- When using `-proxy` without a value, LazySSH listens on `9050`; confirm nothing else uses the port.
- Configure your application to use SOCKS5 at `localhost:<port>`.

## SCP Mode
### `scp` command hangs or is slow
- Large directory listings may take time; use `scp host> tree /path` or `ls` with filters to scope results.
- Ensure the remote shell has permission to read/write the requested files.
- For bulk transfers use `mget` or `put` with explicit targets instead of wildcards.

### Upload fails with permission denied
- Check remote directory permissions and ownership.
- Use `lcd`/`local` to confirm the correct local upload directory.

## Plugins
### `plugin run <name>` not found
- Ensure the script is executable and located in one of the plugin directories.
- Set `LAZYSSH_PLUGIN_DIRS` to include custom locations.
- Run `plugin info <name>` to inspect metadata and validation errors.

### Python plugin marked invalid because it is not executable
- LazySSH automatically repairs execute permissions for packaged assets during startup.
- When a custom Python plugin cannot be chmod'd (read-only locations, network mounts, etc.), the manager falls back to invoking it via `python` and surfaces a validation warning; the plugin still runs.
- View warnings with `plugin info <name>`—the entry remains valid as long as no hard errors are listed.

### Where do enumeration summaries get saved?
- `plugin run enumerate <connection>` prints a Rich summary with Quick Wins (grouped by exploitation difficulty), Priority Findings with severity badges, and color-coded category panels. Both JSON and plain-text artifacts are written to the connection log directory (see the saved path in the final success message).
- Use `plugin run enumerate <connection> --json` to stream the structured payload, which includes the same `priority_findings` list with `exploit_commands` and `exploitation_difficulty` fields.

### Enumeration output looks plain or missing colors
- Ensure Rich is installed (`pip install rich`). LazySSH falls back to plain-text output when Rich is unavailable.
- Set `LAZYSSH_PLAIN_TEXT=true` to intentionally use plain-text mode with full feature parity (Quick Wins, severity badges, evidence items).

### Plugin exits with SSH errors
- Plugins reuse the existing control socket. Confirm the connection is active (`list`).
- Review plugin environment variables in `docs/reference.md` and check the script is using them correctly.
