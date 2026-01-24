# LazySSH

LazySSH is a modern CLI for managing SSH connections, tunnels, file transfers, and automation from one interactive prompt.

![LazySSH](https://raw.githubusercontent.com/Bochner/lazyssh/main/lazyssh.png)

## Highlights
- Interactive command mode with tab completion for every workflow
- Persistent SSH control sockets so sessions, tunnels, and transfers stay fast
- Forward, reverse, and dynamic SOCKS tunnels with friendly status tables
- Rich SCP mode with trees, batch downloads, and progress indicators
- Plugin system for local Python/shell automation that reuses open sockets

## Install
```bash
# Recommended
pipx install lazyssh

# Or use pip
pip install lazyssh

# From source (requires Hatch)
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh
pipx install hatch  # or: pip install hatch
hatch build
pip install dist/*.whl
```

Dependencies: Python 3.11+, OpenSSH client, and optionally the Terminator terminal emulator (LazySSH falls back to the native terminal automatically).

## Quick Start
```bash
# Launch the interactive shell
lazyssh

# Create a new connection (SSH key and SOCKS proxy optional)
lazyssh> lazyssh -ip 192.168.1.100 -port 22 -user admin -socket myserver -ssh-key ~/.ssh/id_ed25519

# Review active connections and tunnels
lazyssh> list

# Open a terminal session in the current window
lazyssh> open myserver

# Save the connection for next time
lazyssh> save-config myserver

# Show saved configs at startup (explicit path to the default file)
$ lazyssh --config /tmp/lazyssh/connections.conf

# Create a forward tunnel to a remote web service
lazyssh> tunc myserver l 8080 localhost 80

# Enter SCP mode to transfer files
lazyssh> scp myserver
scp myserver:/home/admin> get backup.tar.gz
```

Need a guided setup? Run `lazyssh> wizard lazyssh` for a prompt-driven connection workflow.

## Development

```bash
git clone https://github.com/Bochner/lazyssh.git && cd lazyssh
pipx install hatch        # Install build tool (one-time)
make install              # Setup environment
make run                  # Run lazyssh
make check                # Lint + type check
make test                 # Run tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Learn More
- [Getting Started](docs/getting-started.md) – first-run walkthroughs and everyday workflows
- [Reference](docs/reference.md) – command lists, environment variables, and config file details
- [Guides](docs/guides.md) – advanced tunnels, SCP tips, and automation with plugins
- [Troubleshooting](docs/troubleshooting.md) – quick fixes for connection, terminal, or SCP issues
- [Maintainers](docs/maintainers.md) – development environment, logging, and releasing

## Contributing
Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and coding standards.

## License
LazySSH is released under the MIT License.
