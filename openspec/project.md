# Project Context

## Purpose

LazySSH is a comprehensive SSH toolkit for managing connections, tunnels, and remote sessions with a modern CLI interface. It simplifies SSH connection management, tunnel creation, file transfers (SCP), and remote session handling through an elegant command-line interface with both interactive menu and command modes.

**Key Goals:**
- Provide an intuitive interface for complex SSH operations
- Manage multiple SSH connections with control sockets
- Simplify tunnel and proxy creation
- Offer rich visual feedback for file transfers and operations
- Enable seamless terminal integration for remote sessions

## Tech Stack

### Core Language & Runtime
- **Python 3.11+** - Primary language with modern type hints and features

### Key Python Libraries
- **rich** (13.0.0+) - Rich text formatting, progress bars, tree visualizations
- **colorama** (0.4.6+) - Cross-platform colored terminal output
- **click** (8.0.0+) - Command-line interface framework
- **prompt_toolkit** (3.0.39) - Interactive command-line interface with tab completion
- **paramiko** (3.0.0+) - SSH protocol implementation in Python
- **pexpect** (4.8.0+) - Process interaction and automation
- **python-dotenv** (1.0.0+) - Environment variable management
- **wcwidth** (0.2.5+) - Unicode character width calculations
- **art** (5.9+) - ASCII art generation

### System Dependencies
- **OpenSSH client** - Core SSH functionality (required)
- **Terminator** - Terminal emulator for session management (optional but recommended)

### Development Tools
- **black** - Code formatting (100 char line length)
- **isort** - Import sorting (black-compatible profile)
- **flake8** - Linting
- **pylint** - Additional linting
- **mypy** - Type checking
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **pre-commit** - Git hook management

## Project Conventions

### Code Style

**Formatting:**
- Line length: 100 characters (enforced by black)
- Target Python version: 3.11
- Import sorting: black-compatible profile with isort
- Type hints: Preferred but not strictly enforced (disallow_untyped_defs = false)

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
- `__main__.py` - Application entry point
- `command_mode.py` - Interactive command mode implementation
- `scp_mode.py` - File transfer mode implementation
- `ssh.py` - SSH connection management and operations
- `ui.py` - User interface components and rendering
- `models.py` - Data models and structures
- `config.py` - Configuration management
- `logging_module.py` - Centralized logging with specialized loggers

**Logging Strategy:**
- Specialized loggers: `APP_LOGGER`, `SSH_LOGGER`, `CMD_LOGGER`, `SCP_LOGGER`
- Connection-specific loggers available via `get_connection_logger()`
- Debug mode toggling with `set_debug_mode()`
- Structured logging functions: `log_ssh_command()`, `log_tunnel_creation()`, `log_file_transfer()`

**SSH Control Sockets:**
- Used for multiplexing SSH connections
- Enables persistent connections and connection reuse
- Socket management through connection tracking

**Interface Modes:**
1. Command mode (default) - Interactive shell with tab completion
2. Menu mode - Traditional menu-driven interface
3. SCP mode - File transfer interface with tree visualization

### Testing Strategy

**Test Organization:**
- Test files: `test_*.py` pattern in `tests/` directory
- Test functions: `test_*` prefix
- Test classes: `Test*` prefix

**Coverage:**
- Source tracking enabled for `src/` directory
- Tests excluded from coverage reports
- Run with: `pytest` and `pytest-cov`

**Quality Gates:**
- Pre-commit hooks for automated checking
- Manual run: `./pre-commit-check.sh`
- All checks must pass before commits

### Git Workflow

**Version Management:**
- Follows semantic versioning: MAJOR.MINOR.PATCH
- Version maintained in exactly two places:
  1. `pyproject.toml` - Package version
  2. `src/lazyssh/__init__.py` - `__version__` variable
- Use `scripts/release.py` to update versions (auto-updates both locations and creates git tags)
- **Never** add version information elsewhere

**Branching:**
- Feature branches from main
- Branch naming: Use descriptive names (e.g., `feature/add-x`, `fix/bug-y`, `70-feature-implement-openspec`)
- Issues tracked via GitHub Projects

**Commit Conventions:**
- Clear, descriptive commit messages
- Reference issue numbers where applicable

**Release Process:**
1. Update version with `python scripts/release.py X.Y.Z`
2. Update CHANGELOG.md with changes
3. Create git tag (automated by release script)
4. Build and publish to PyPI

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

**User Workflows:**
1. Create named connection with socket
2. Establish tunnels or proxies
3. Open terminal sessions
4. Transfer files via SCP mode
5. Manage and close connections

## Important Constraints

**Platform Requirements:**
- Linux/Unix systems (POSIX-compliant)
- macOS supported
- Windows not officially supported (WSL may work)

**Python Version:**
- Minimum: Python 3.11
- Type hint features from 3.11 used (e.g., `list[str]` instead of `List[str]`)

**External Dependencies:**
- OpenSSH client must be installed on the system
- Terminator terminal emulator recommended but optional
- Cannot function without SSH client

**Terminal Compatibility:**
- Relies on ANSI color codes
- Requires Unicode support for rich formatting
- Best experience with modern terminal emulators

**Security:**
- Relies on OpenSSH's security model
- Uses system SSH configuration
- SSH keys and authentication handled by OpenSSH

## External Dependencies

**System Commands:**
- `ssh` - Core SSH operations
- `which` - Executable checking
- `terminator` - Terminal emulator for session opening (optional)

**SSH Configuration:**
- Uses user's `~/.ssh/config` if present
- SSH key management through standard SSH infrastructure
- Known hosts and authentication via OpenSSH

**File System:**
- Control sockets stored in default SSH control path
- Log files managed by logging module
- Configuration files via python-dotenv

**Network:**
- Direct network access for SSH connections
- Port forwarding requires appropriate permissions
- SOCKS proxy binding to local ports
