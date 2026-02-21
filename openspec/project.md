# Project Context

## Purpose

LazySSH is a comprehensive SSH automation toolkit for managing persistent connections, tunnels, file transfers, and plugin-driven workflows through a modern command-line experience. The application centers on a single prompt_toolkit-powered command mode complemented by guided wizards and an extensible plugin system.

**Key Goals:**
- Provide an intuitive, keyboard-first interface for complex SSH operations
- Manage multiple SSH connections via control sockets and shared configuration storage
- Simplify tunnel and proxy creation with interactive wizard flows
- Deliver plugin extensibility for remote automation and reconnaissance
- Offer rich visual feedback for file transfers, status dashboards, and plugin output
- Maintain seamless terminal integration with dynamic terminal method selection

## Tech Stack

### Core Language & Runtime
- **Python 3.11+** - Primary language with modern type hints and features (3.11, 3.12, and 3.13 supported in pyproject.toml classifiers)

### Key Python Libraries
- **rich** (13.0.0+) - Rich text formatting, plugin output rendering, progress visualization
- **prompt_toolkit** (>=3.0.39, <3.1.0) - Interactive command mode with history and tab completion
- **click** (8.0.0+) - CLI option parsing for entry point flags
- **paramiko** (3.0.0+) - SSH protocol implementation
- **pexpect** (4.8.0+) - Interactive process control for SCP mode
- **tomli-w** (1.0.0+) - TOML writer for persisting connection configurations
- **python-dotenv** (1.0.0+) - Environment variable management
- **wcwidth** (0.2.5+) - Unicode width calculations for prompt rendering
- **art** (5.9+) - ASCII art banner generation
- **colorama** (0.4.6+) - Legacy Windows console color compatibility (installed but rarely needed)

### System Dependencies
- **OpenSSH client** - Core SSH functionality (required)
- **Terminator** - Optional terminal emulator; falls back to native subprocess terminal when absent

### Build & Development Tools
- **[Hatch](https://hatch.pypa.io/)** - Modern Python project manager (build, environments, versioning, multi-version testing via `hatch test`)
- **[mise](https://mise.jdx.dev/)** - Polyglot tool version manager (Python, Ruff, pre-commit)
- **[Ruff](https://docs.astral.sh/ruff/)** - Fast linter and formatter (replaces black, isort, flake8, pylint, pyupgrade)
- **[pre-commit](https://pre-commit.com/)** - Git hook framework for automated quality checks before commits
- **mypy** - Type checking
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **pytest-html** - HTML test report generation

### Artifacts Directory
Test and coverage reports are generated into the `artifacts/` directory:
- `artifacts/coverage/` - HTML coverage reports from pytest-cov
- `artifacts/unit/` - HTML test reports from pytest-html

## Project Conventions

### Code Style

**Formatting:**
- Line length: 100 characters (enforced by Ruff)
- Import sorting: Ruff (isort-compatible)
- Type hints: Strictly enforced via mypy (`disallow_untyped_defs = true`)

**Naming Conventions:**
- Modules: `snake_case` (e.g., `command_mode.py`, `logging_module.py`, `scp_mode.py`)
- Classes: `PascalCase` (e.g., `ConnectionManager`, `TunnelConfig`)
- Functions/Methods: `snake_case` (e.g., `check_dependencies`, `log_ssh_command`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `APP_LOGGER`, `CMD_LOGGER`)
- Private members: Single leading underscore (e.g., `_check_executable`)

**Documentation:**
- All modules should have module-level docstrings
- Public functions should have docstrings with Args and Returns sections
- Use triple-quoted strings for docstrings

### Architecture Patterns

**Module Organization:**
- `__main__.py` - CLI entry point; initializes logging, configuration file, runtime plugin directory, and command mode
- `command_mode.py` - prompt_toolkit-powered command shell with core commands, guided wizards, config management, and plugin execution
- `scp_mode.py` - File transfer mode with cached directory listings and throttled completions
- `ssh.py` - SSH connection lifecycle, tunnel management, and terminal method selection (`auto`/`native`/`terminator`)
- `config.py` - TOML-backed configuration persistence, validation, and backup utilities
- `plugin_manager.py` - Plugin discovery, metadata validation, search-order resolution, and execution helpers
- `plugins/` - Packaged built-in plugins (currently the `enumerate` recon plugin)
- `console_instance.py` - Centralized Rich console/theme management with environment-driven overrides
- `ui.py` - Rendering helpers for dashboards, plugin metadata, and output formatting
- `models.py` - Dataclasses for SSH connections, tunnels, and runtime directories
- `logging_module.py` - Centralized logging setup, connection-specific loggers, and transfer statistics

**Logging Strategy:**
- Specialized loggers: `APP_LOGGER`, `SSH_LOGGER`, `CMD_LOGGER`, `SCP_LOGGER`
- Connection-specific loggers available via `get_connection_logger()`
- Debug mode toggling with `set_debug_mode()`
- Structured logging functions: `log_ssh_command()`, `log_tunnel_creation()`, `log_file_transfer()`
- Plugin executions and enumeration reports written to `/tmp/lazyssh/{connection}.d/logs`

**SSH Control Sockets:**
- Used for multiplexing SSH connections
- Enables persistent connections and connection reuse
- Socket management through connection tracking

**Interface Modes:**
1. Command mode (default) - prompt_toolkit shell with tab completion, config management, terminal controls, and plugin commands
2. Guided wizards - `wizard lazyssh` and `wizard tunnel` provide step-by-step workflows within command mode
3. SCP mode - File transfer interface with tree visualization, caching, and throttled completions

**Configuration Management:**
- Saved connections persisted in `/tmp/lazyssh/connections.conf` (TOML) with 0600 permissions and comment preservation
- Commands: `config`/`configs` (list), `connect`, `save-config`, `delete-config`, `backup-config`
- Entry point accepts `--config` flag to load alternate files; successful loads are echoed in startup tables
- Validation covers required fields, socket name normalization, SSH key hints, and port parsing

**Plugin Architecture:**
- Search order: `LAZYSSH_PLUGIN_DIRS` (left→right, absolute paths) → `~/.lazyssh/plugins` → `/tmp/lazyssh/plugins` → packaged `plugins/`
- Packaged plugins are ensured executable at runtime; `/tmp/lazyssh/plugins` created with 0700 permissions
- Metadata read from `# PLUGIN_*` headers; executables must include a shebang and pass validation
- Supports Python (`.py`) and shell (`.sh`) plugins; executability is required before discovery succeeds
- Plugin API exposes context via env vars: `LAZYSSH_SOCKET`, `LAZYSSH_SOCKET_PATH`, `LAZYSSH_HOST`, `LAZYSSH_PORT`, `LAZYSSH_USER`, `LAZYSSH_PLUGIN_API_VERSION`, plus optional `LAZYSSH_SSH_KEY` and `LAZYSSH_SHELL`
- Command-mode integration: `plugin list`, `plugin info <name>`, `plugin run <name> <socket>` with tab completion and formatted output
- Built-in `enumerate` plugin ships under `src/lazyssh/plugins/` providing reconnaissance reports and log file export

**Enumerate Plugin (v2.0.0):**
- **Batched script execution**: Executes a single remote script gathering all telemetry in one SSH round-trip for minimal latency
- **Priority findings summary**: Heuristics flag elevated risks including:
  - Sudo/wheel group membership and passwordless sudo entries
  - SUID/SGID binaries
  - World-writable directories outside temp paths
  - Externally accessible network listeners
  - Insecure sshd configuration (PermitRootLogin, PasswordAuthentication, etc.)
  - Suspicious scheduled tasks (cron jobs with curl, wget, nc, etc.)
  - Kernel version drift from package inventory
- **JSON export**: Use `--json` flag for machine-readable output
- **Log persistence**: Survey results saved to connection workspace (`/tmp/lazyssh/{socket}.d/logs/survey_*.json` and `.txt`)
- **Dracula-themed Rich output**: Styled tables and panels with severity indicators (high/medium/info)

**UI Configuration:**
- `console_instance.py` centralizes Rich console setup, Dracula-themed defaults, and accessibility variants
- Environment toggles: `LAZYSSH_HIGH_CONTRAST`, `LAZYSSH_COLORBLIND_MODE`, `LAZYSSH_NO_RICH`, `LAZYSSH_NO_ANIMATIONS`, `LAZYSSH_PLAIN_TEXT`, `LAZYSSH_REFRESH_RATE`
- UI respects plain-text mode for minimal terminals and adjusts layout padding/animations accordingly

**Terminal Configuration:**
- Default terminal method sourced from `LAZYSSH_TERMINAL_METHOD` (`auto`, `native`, `terminator`)
- `terminal <method>` updates runtime preference; `open <socket>` spawns session using the active method
- Native fallback leverages subprocess-based PTY handling when Terminator is unavailable

### Testing Strategy

**Test Organization:**
- Test files: `test_*.py` pattern in `tests/` directory
- Test functions: `test_*` prefix
- Test classes: `Test*` prefix

**Coverage:**
- **97% branch coverage required** - enforced via `fail_under = 97` in pyproject.toml
- Source tracking enabled for `src/` directory
- Tests excluded from coverage reports
- Run with: `make test` (wraps `hatch run test`) or `hatch test` for multi-version testing
- Dedicated suites cover plugin discovery/execution (`tests/test_plugin_manager.py`, `tests/test_command_plugin.py`) and UI environment toggles

**Test Isolation for CI/CD:**
All tests must be isolated from external dependencies to ensure reliable CI execution:
- **Subprocess operations** (`subprocess.run`, `subprocess.Popen`) MUST be mocked to prevent actual process execution
- **Interactive prompts** (`Confirm.ask`, `Prompt.ask`, `input()`) MUST be mocked to prevent stdin blocking
- **Network operations** (SSH connections, sockets) MUST be mocked to prevent network dependencies
- **SCPMode tests** with active connections MUST mock `connect()` subprocess calls
- **Plugin execution tests** MUST either mock `execute_plugin()` or use small controlled test scripts

**Timeout Protection:**
- pytest-timeout is configured with a 30-second per-test timeout
- If a test hangs, the timeout captures the stack trace identifying the blocking operation
- Timeout method is `thread` for cross-platform compatibility

**HTML Reports:**
- Coverage HTML reports: `artifacts/coverage/` (generated by pytest-cov)
- Test result reports: `artifacts/unit/report.html` (generated by pytest-html)
- Reports are self-contained and can be viewed in a browser

**Multi-Version Testing:**
- `hatch test` runs the test suite across Python 3.11, 3.12, and 3.13
- CI matrix ensures compatibility across all supported Python versions

**Quality Gates:**
- **Pre-commit hooks** automatically run quality checks before each commit
- Install hooks: `make pre-commit-install` (one-time setup after mise is installed)
- Run hooks manually: `make pre-commit` (runs on all files)
- Hooks include: trailing whitespace removal, Ruff (lint + format), mypy type checking
- Run `hatch run check` or `make check` for all quality checks
- Run `make verify` for full verification (check + test + build)
- All checks must pass before commits

**Pre-commit Workflow:**
1. Install mise and run `mise install` to get pre-commit
2. Run `make pre-commit-install` to configure git hooks
3. On each `git commit`, hooks run automatically and block commits with issues
4. Fix any reported issues and re-commit

### Git Workflow

**Version Management:**
- Follows semantic versioning: MAJOR.MINOR.PATCH
- Version maintained in single source of truth: `src/lazyssh/__init__.py` (`__version__` variable)
- Hatch reads version dynamically from this file
- Use `hatch version X.Y.Z` to update versions
- **Never** add version information elsewhere

**Branching:**
- Feature branches from main
- Branch naming: Use descriptive names (e.g., `feature/add-x`, `fix/bug-y`, `70-feature-implement-openspec`)
- Issues tracked via GitHub Projects

**Commit Conventions:**
- Clear, descriptive commit messages
- Reference issue numbers where applicable

**Release Process:**
1. Update version with `hatch version X.Y.Z`
2. Update CHANGELOG.md with changes
3. Commit and create git tag: `git tag -a vX.Y.Z -m 'Release vX.Y.Z'`
4. Push with tags: `git push && git push --tags`
5. GitHub Actions builds and publishes to PyPI

## Domain Context

**SSH Concepts:**
- **Control Sockets** - Master connections that can be shared by multiple sessions
- **Multiplexing** - Reusing a single SSH connection for multiple sessions
- **Forward Tunnels** - Local port forwarding (local → remote)
- **Reverse Tunnels** - Remote port forwarding (remote → local)
- **Dynamic Tunnels** - SOCKS proxy for dynamic port forwarding
- **Socket Names** - User-defined identifiers for managing multiple connections

**Common Operations:**
- Connection creation with control socket
- Tunnel management (create, list, close)
- Terminal session opening
- File transfers with SCP
- Directory tree visualization for remote filesystems
- Configuration management (save, connect, delete, backup)
- Plugin discovery and execution for remote automation

**User Workflows:**
1. Launch command mode (optionally load configs via `--config`)
2. Establish connections through `lazyssh` command or `wizard lazyssh` flow
3. Persist configurations and reuse them with `connect <name>`
4. Create tunnels with `wizard tunnel` or direct `tunc` commands
5. Execute plugins (`plugin run enumerate <socket>`) for reconnaissance or automation
6. Use SCP mode for transfers and manage/open/close sessions as needed

## Important Constraints

**Platform Requirements:**
- Linux/Unix systems (POSIX-compliant) - Full support
- macOS - Full support
- Windows - Not supported natively; Windows users should use Windows Subsystem for Linux (WSL)

**Python Version:**
- Minimum: Python 3.11, with 3.12 and 3.13 also tested and supported
- Type hint features from 3.11 used (e.g., `list[str]` instead of `List[str]`)
- CI matrix tests against 3.11, 3.12, and 3.13

**External Dependencies:**
- OpenSSH client must be installed on the system
- Terminator terminal emulator optional; native fallback keeps functionality
- Cannot function without SSH client

**Terminal Compatibility:**
- Relies on ANSI color codes
- Requires Unicode support for rich formatting
- Best experience with modern terminal emulators

**Runtime Directories:**
- `/tmp/lazyssh/connections.conf` stores saved configurations (0600 permissions)
- `/tmp/lazyssh/{socket}.d/` contains downloads, uploads, and logs for each connection
- `/tmp/lazyssh/plugins/` is created on startup for runtime/temporary plugins (0700 permissions)

**Security:**
- Relies on OpenSSH's security model
- Uses system SSH configuration
- SSH keys and authentication handled by OpenSSH

## Environment Configuration

- `LAZYSSH_TERMINAL_METHOD` controls default terminal strategy (`auto`, `native`, `terminator`)
- `LAZYSSH_PLUGIN_DIRS` (colon-separated, absolute) prepends custom plugin search paths
- UI toggles: `LAZYSSH_HIGH_CONTRAST`, `LAZYSSH_COLORBLIND_MODE`, `LAZYSSH_NO_RICH`, `LAZYSSH_NO_ANIMATIONS`, `LAZYSSH_PLAIN_TEXT`, `LAZYSSH_REFRESH_RATE`
- Plugins receive connection context via env vars (`LAZYSSH_SOCKET`, `LAZYSSH_SOCKET_PATH`, `LAZYSSH_HOST`, `LAZYSSH_PORT`, `LAZYSSH_USER`, `LAZYSSH_PLUGIN_API_VERSION`, optional `LAZYSSH_SSH_KEY`, `LAZYSSH_SHELL`)

## External Dependencies

**System Commands:**
- `ssh` - Core SSH operations
- `terminator` - Terminal emulator for session opening (optional)

**Note:** Executable detection is handled by Python's built-in `shutil.which()` for cross-platform compatibility.

**SSH Configuration:**
- Uses user's `~/.ssh/config` if present
- SSH key management through standard SSH infrastructure
- Known hosts and authentication via OpenSSH

**File System:**
- Control sockets created under `/tmp/<socket>` using OpenSSH multiplexing
- Connection workspaces at `/tmp/lazyssh/{socket}.d/` with `downloads/`, `uploads/`, and `logs/`
- Saved configurations persisted to `/tmp/lazyssh/connections.conf` (TOML with comment preservation)
- Runtime plugin staging directory `/tmp/lazyssh/plugins/` (auto-created with secure permissions)
- Optional `.env` files supported through `python-dotenv`

**Network:**
- Direct network access for SSH connections
- Port forwarding requires appropriate permissions
- SOCKS proxy binding to local ports
