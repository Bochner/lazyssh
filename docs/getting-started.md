# Getting Started with LazySSH

LazySSH wraps common SSH tasks in an interactive shell so you can manage connections, tunnels, and transfers without memorising long commands. This guide covers the everyday workflows to get you productive quickly.

## Prerequisites
- Python 3.11 or newer
- OpenSSH client (`ssh` on your PATH)
- Optional: Terminator terminal emulator (LazySSH falls back to the native terminal if it is missing)

## Install
```bash
pipx install lazyssh            # Recommended
# or
pip install lazyssh             # Install into the active environment
# or work from source
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh
pip install -e .
```

## Launch LazySSH
```bash
lazyssh
```
You will see the `lazyssh>` prompt with tab completion. Type `help` at any time to view available commands.

## Create Your First Connection
```bash
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver
```
- `-socket` gives the connection a short name used by other commands.
- Add `-ssh-key ~/.ssh/id_ed25519` to use a specific key.
- Add `-proxy` (optionally `-proxy 9050`) to spin up a SOCKS proxy.

Check current connections and tunnels:
```bash
lazyssh> list
```
Open an interactive terminal using the existing control socket:
```bash
lazyssh> open myserver
```
Close the connection when you are done:
```bash
lazyssh> close myserver
```

## Manage Saved Configurations
After creating a connection LazySSH can remember it for next time.
```bash
lazyssh> save-config myserver        # Saves connection parameters under "myserver"
lazyssh> config                      # Displays saved configurations
lazyssh> connect myserver            # Recreate the connection later
lazyssh> delete-config myserver      # Remove a stored configuration
lazyssh> backup-config               # Write a timestamped backup to /tmp/lazyssh
```
Show saved configs at startup (explicit path to the default file):
```bash
lazyssh --config /tmp/lazyssh/connections.conf
```

## Create Tunnels
```bash
# Forward/Local tunnel: expose remote port 80 on localhost:8080
lazyssh> tunc myserver l 8080 localhost 80

# Reverse tunnel: expose local port 8080 as remote port 3000
lazyssh> tunc myserver r 3000 localhost 8080

# Remove a tunnel by ID (see `list` output)
lazyssh> tund 1
```

## Transfer Files with SCP Mode
```bash
lazyssh> scp myserver         # Enter SCP mode
scp myserver:/home/admin> ls  # Remote listing
scp myserver:/home/admin> get backup.tar.gz
scp myserver:/home/admin> put ./local.txt
scp myserver:/home/admin> exit
```
Use tab completion inside SCP mode for both local and remote paths.

## Guided Workflows
Need a prompt-driven experience?
```bash
lazyssh> wizard lazyssh   # Step-by-step connection wizard
lazyssh> wizard tunnel    # Guided tunnel creation
```

## Terminal Methods and Debugging
- Change the terminal method on the fly: `lazyssh> terminal native`, `lazyssh> terminal terminator`, or `lazyssh> terminal auto`.
- Toggle runtime debug logs: `lazyssh> debug` (or start with `lazyssh --debug`). Logs live in `/tmp/lazyssh/logs`.

## Next Steps
- Read `docs/reference.md` for the full command and environment variable tables.
- Explore advanced scenarios in `docs/guides.md`.
- Check `docs/troubleshooting.md` if something does not work as expected.
