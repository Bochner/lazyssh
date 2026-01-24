# Maintainers Guide

## Development Stack

- **[Hatch](https://hatch.pypa.io/)** - Project management, builds, publishing
- **[Ruff](https://docs.astral.sh/ruff/)** - Linting and formatting (replaces black, isort, flake8, pylint)
- **[mise](https://mise.jdx.dev/)** - Tool version management (Python, Ruff)

## Setup

```bash
git clone https://github.com/Bochner/lazyssh.git && cd lazyssh
pipx install hatch     # One-time
make install           # Setup environment
make run               # Run lazyssh
```

## Commands

```bash
make install   # Setup Hatch environment
make run       # Run lazyssh (hatch run lazyssh)
make fmt       # Format code
make fix       # Auto-fix + format
make lint      # Run linter
make test      # Run tests (shows coverage)
make check     # All quality checks
make build     # Build package
make clean     # Clean artifacts
```

Use `hatch run <command>` to run any command in the venv without activation.

## Logging

- `--debug` flag for verbose logging
- Logs in `/tmp/lazyssh/logs/`
- Toggle at runtime: `lazyssh> debug`

## Releases

```bash
hatch version 1.2.3                    # Set version
make check                             # Verify
git commit -am 'v1.2.3' && git tag v1.2.3
git push && git push --tags            # CI publishes to PyPI
```

Manual publish: `make publish`

## Useful Paths

- Config: `/tmp/lazyssh/connections.conf`
- Plugins: `/tmp/lazyssh/plugins/`
- Logs: `/tmp/lazyssh/logs/`
