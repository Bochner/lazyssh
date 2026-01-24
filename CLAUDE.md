# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- OPENSPEC:START -->
## OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Tool Version Management

This project uses **[mise](https://mise.jdx.dev/)** for tool version management. When you `cd` into the project directory, mise automatically activates the correct versions of Python and Ruff defined in `.mise.toml`.

```bash
# One-time setup
brew install mise         # or see https://mise.jdx.dev/getting-started.html
mise trust                 # Trust this project's .mise.toml
```

Tools are auto-activated when entering the directory - no manual version switching needed.

## Pre-commit Hooks

This project uses **pre-commit** to automatically run quality checks before each commit.

```bash
# One-time setup (after mise is installed)
mise install              # Install pre-commit via mise
make pre-commit-install   # Install git hooks
```

Hooks run automatically on `git commit`. To run manually:

```bash
make pre-commit           # Run all hooks on all files
```

Hooks include: trailing whitespace, ruff (lint + format), and mypy.

## Quality Gate

**All quality checks must pass before committing.** Pre-commit hooks enforce this automatically. To run manually:

```bash
make check                # Linting (ruff) + type checking (mypy)
```

For full verification including tests and build:

```bash
make verify               # check + test + build
```

## Build and Development Commands

```bash
# Setup
pipx install hatch        # Install Hatch (one-time)
make install              # Create environment

# Run the app
make run                  # or: hatch run lazyssh

# Development
make fmt                  # Format code (ruff format)
make fix                  # Auto-fix + format
make lint                 # Run linter (ruff check)
make test                 # Run tests with coverage
make check                # All quality checks (ruff + mypy) - REQUIRED before commits
make build                # Build package
```

Use `hatch run <command>` to run any command in the venv without activation.

## Architecture Overview

LazySSH is an SSH automation toolkit providing persistent connections, tunnels, file transfers, and plugin-driven workflows through an interactive CLI.

### Core Module Flow

```
__main__.py → CommandMode (prompt_toolkit shell)
                 ├── SSHManager (ssh.py) - connection lifecycle, tunnels, terminals
                 ├── SCPMode (scp_mode.py) - file transfers with tree visualization
                 ├── PluginManager (plugin_manager.py) - discovery/execution
                 └── Config (config.py) - TOML persistence
```

### Key Modules

| Module | Purpose |
|--------|---------|
| `command_mode.py` | Main prompt_toolkit shell with tab completion, wizards, and all user commands |
| `ssh.py` | SSH connection management, control sockets, tunnel creation, terminal method selection |
| `scp_mode.py` | File transfer interface with cached directory listings |
| `plugin_manager.py` | Plugin discovery from multiple paths, metadata validation, execution with env injection |
| `config.py` | TOML-backed config persistence with comment preservation |
| `console_instance.py` | Rich console/theme centralization, accessibility variants |
| `logging_module.py` | Specialized loggers: `APP_LOGGER`, `SSH_LOGGER`, `CMD_LOGGER`, `SCP_LOGGER` |

### Plugin System

Search order: `LAZYSSH_PLUGIN_DIRS` → `~/.lazyssh/plugins` → `/tmp/lazyssh/plugins` → packaged `plugins/`

Plugins receive connection context via environment variables: `LAZYSSH_SOCKET`, `LAZYSSH_HOST`, `LAZYSSH_PORT`, `LAZYSSH_USER`, etc.

### Runtime Directories

- `/tmp/lazyssh/connections.conf` - Saved configurations (TOML, 0600 permissions)
- `/tmp/lazyssh/{socket}.d/` - Per-connection workspace (downloads/, uploads/, logs/)
- `/tmp/lazyssh/plugins/` - Runtime plugin staging (0700 permissions)

## Code Conventions

- **Line length**: 100 characters
- **Linting/formatting**: Ruff (replaces black, isort, flake8, pylint)
- **Type checking**: mypy
- **Python version**: 3.11+ (use modern type hints like `list[str]` not `List[str]`)
- **Version location**: Single source of truth in `src/lazyssh/__init__.py`
- **Version updates**: Use `hatch version X.Y.Z`

## Environment Variables

**Terminal:**
- `LAZYSSH_TERMINAL_METHOD` - `auto`, `native`, or `terminator`

**Plugins:**
- `LAZYSSH_PLUGIN_DIRS` - Colon-separated additional plugin search paths

**UI:**
- `LAZYSSH_PLAIN_TEXT` - Minimal output for simple terminals
- `LAZYSSH_NO_ANIMATIONS` - Disable spinner animations
- `LAZYSSH_HIGH_CONTRAST` - High contrast theme
- `LAZYSSH_COLORBLIND_MODE` - Colorblind-friendly palette

## Cross-References

For detailed information, see:
- **[openspec/project.md](openspec/project.md)** - Full tech stack, conventions, domain context
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup, PR process, version management
