# Changelog

All notable changes to LazySSH will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Enumeration Probe Expansion**: Added ~40 new probes across 6 new categories for comprehensive privilege escalation scanning
  - **Capabilities**: Binary capability discovery (`getcap`) with dangerous capability filtering
  - **Container Escape**: Docker group membership, socket access, container indicators, Kubernetes service account detection
  - **Credentials**: Readable shadow file, SSH private keys, cloud credential files (AWS/GCP/Azure), database configs, shell history secrets, `.env` files
  - **Writable Paths**: Writable PATH directories, `/etc/passwd`, `/etc/shadow`, cron files, systemd services, log files, `/tmp` sticky bit, SGID directories
  - **Library Hijack**: `LD_PRELOAD`/`LD_LIBRARY_PATH` opportunities, Python/Ruby path injection, writable shared library directories
  - **Interesting Files**: Backup archives, mail spools, `/opt` directory contents, core dumps, `.bash_history` files
  - Expanded existing categories with NFS exports, `doas.conf`, polkit rules, and `pkexec` version probes
- **GTFOBins Cross-Reference**: Embedded database of ~100 exploitable binaries with SUID, sudo, and capabilities exploitation techniques
  - Automatic cross-referencing of discovered SUID binaries and sudo-allowed commands against GTFOBins
  - Actionable exploit commands included directly in findings output
  - Lookup functions for SUID, sudo, and capabilities exploitation vectors
- **Kernel Exploit Suggester**: Built-in database of ~15 kernel CVEs (DirtyPipe, DirtyCOW, PwnKit, Overlayfs, Netfilter, Baron Samedit, Polkit, Sequoia, GameOver(lay), Looney Tunables, nf_tables, Dirty Cred, etc.)
  - Robust kernel version parsing (handles formats like `5.10.100-generic`, `4.15.0-213-generic`)
  - Automatic matching against running kernel version with CVE details and references
- **Autopwn Engine**: Automated exploitation of discovered vulnerabilities with user confirmation
  - Supports writable `/etc/passwd` exploitation, GTFOBins SUID/sudo exploitation, Docker container escape, writable cron injection, and writable systemd service modification
  - `--autopwn` flag to enable automatic exploitation after enumeration
  - `--dry-run` flag to preview exploitation commands without executing
  - Interactive confirmation before each exploit attempt
- **Quick Wins Summary**: New output section highlighting immediately exploitable findings
  - Findings grouped by exploitation difficulty: Instant, Easy, Moderate
  - Displayed at the top of enumeration output for rapid triage
  - Available in both Rich and plain-text rendering modes
- **Critical Severity Level**: Added `critical` severity for the most dangerous findings (e.g., writable passwd, known kernel exploits)
- **Upload-and-Execute Plugin**: New built-in plugin for uploading and executing binaries on remote hosts
  - Upload any local binary via SCP and execute it remotely with configurable arguments
  - Automatic remote staging directory creation and cleanup
  - `--msfvenom` flag for automatic payload generation with architecture-appropriate defaults
  - `PAYLOAD_PRESETS` with pre-configured payloads for Linux (x86, x64, ARM, MIPS) and architecture auto-detection
  - Interactive mode with Rich prompts: choose upload, msfvenom generation, or upload-only workflows
  - `--dry-run` mode to preview all commands without execution
  - Background execution, timeout, and output capture options
  - Handler command generation for Metasploit multi/handler setup
- **Architecture Auto-Detection**: Remote architecture detection module using SSH control socket
  - Detects OS and CPU architecture via `uname -m` and `uname -s`
  - Maps to msfvenom-compatible architecture/platform strings
- **New Environment Variable**: `LAZYSSH_CONNECTION_DIR` injected into plugin execution environment, providing the per-connection workspace directory path

### Changed
- **Enumeration JSON Output**: `exploitation_difficulty` and `exploit_commands` fields now included in priority findings JSON payload
- **Enumeration Finding Detail**: Exploit commands displayed inline with finding evidence when available

## [1.6.0] - 2026-01-24

### Added
- **Test Isolation Infrastructure**: Comprehensive test isolation requirements for CI/CD compatibility
  - Added `pytest-timeout` with 30-second timeout per test using thread method
  - Documented mocking patterns for subprocess, interactive prompts, and plugin execution
  - Updated `conftest.py` with isolation fixtures and guidance
- **Pre-commit Hooks**: Automatic quality checks before each commit
  - Integrated trailing whitespace, ruff (lint + format), and mypy hooks
  - Added `make pre-commit-install` and `make pre-commit` targets
- **Tool Version Management**: Added `.mise.toml` for automatic tool version activation
  - Python, Ruff, and pre-commit versions managed by mise
  - Tools auto-activate when entering the project directory
- **HTML Test Reports**: Test infrastructure generates HTML coverage reports in `artifacts/`
  - Added `pytest-html` for rich test result visualization
  - Coverage reports available in both CLI and HTML formats
- **Full Test Coverage**: Achieved 100% test coverage across all modules

### Changed
- **BREAKING:** Modernized build system from legacy scripts to Hatch
  - Replaced flake8 and legacy linting with Ruff for formatting, linting, and import sorting
  - Version management now handled natively by Hatch (`hatch version X.Y.Z`)
  - Simplified GitHub Actions workflows for CI and publishing
- **Documentation Updates**: Comprehensive updates to build and development documentation
  - Updated CLAUDE.md with test isolation requirements and mocking patterns
  - Revised CONTRIBUTING.md with new tool management workflow
  - Updated openspec/project.md with build tools and test infrastructure details

### Removed
- **BREAKING:** Removed `scripts/release.py` and Makefile `release` target
  - Version management is now handled by `hatch version` command
  - Release workflow simplified to use Hatch directly

## [1.5.1] - 2025-10-13

### Added
- User plugin directories with clear precedence and environment override
  - Search order: `LAZYSSH_PLUGIN_DIRS` (left→right) → `~/.lazyssh/plugins` → packaged `plugins/`
  - Non-existent directories are ignored without errors
  - Safety: symlinks escaping base directories are skipped
- Runtime enforcement that packaged plugins are executable post-install
- Documentation updates for plugin locations and `LAZYSSH_PLUGIN_DIRS`
- Introduced severity-ranked priority findings to the `enumerate` plugin covering sudo membership, passwordless sudo rules, SUID/SGID binaries, world-writable paths, exposed services, weak SSH settings, suspicious schedulers, and kernel drift, rendered through Rich panels with a plain-text fallback and included in the JSON artifacts.

### Changed
- Refactored `enumerate` to execute a single batched remote script defined in `_enumeration_plan.py`, reducing round trips, capturing stdout/stderr metadata per probe, and persisting both JSON and plain-text survey outputs under the connection log directory.
- Hardened plugin discovery by ensuring `/tmp/lazyssh/plugins` exists with 0700 permissions, repairing missing execute bits on packaged Python plugins when possible, falling back to interpreter execution with warnings, and surfacing validation warnings in `plugin info`.
- Moved command and SCP history files to `/tmp/lazyssh` with secure permissions and added a `shutil.get_terminal_size` fallback when determining terminal width.

### Tests
- Coverage for env/user directory discovery, precedence, and non-existent dirs
- Validation that runtime sets exec bit on packaged plugins
- Added targeted coverage for plugin manager permission repair, directory precedence, runtime directory provisioning, and warning propagation.
- Added unit tests exercising the enumeration priority findings pipeline and JSON payload structure.

### Documentation
- Reworked user documentation with a streamlined README plus new `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, and `docs/maintainers.md`, alongside refreshed troubleshooting guidance aligned with the updated workflows.

## [1.5.0] - 2025-10-13

### Added
- **Plugin System**: Extensible plugin architecture for custom automation and workflows
  - Plugin discovery and validation system
  - Support for Python (.py) and shell (.sh) script plugins
  - Plugin metadata extraction from structured comments
  - Environment variable-based plugin API for connection context
  - `plugin` command with `list`, `run`, and `info` subcommands
  - Tab completion for plugin names and socket names
  - Plugin execution with real-time output streaming
  - Error handling and execution time tracking
  - Built-in plugin development template
- **Enumerate Plugin**: Comprehensive system enumeration and reconnaissance
  - OS and kernel information gathering
  - User accounts and group enumeration
  - Network configuration discovery (interfaces, routes, ports)
  - Process and service enumeration
  - Installed package detection (apt, yum, pacman)
  - Filesystem and mount information
  - Environment variable extraction
  - Scheduled task discovery (cron, systemd timers)
  - Security configuration checks (firewall, SELinux, AppArmor)
  - System logs summary
  - Hardware information
  - JSON and human-readable output formats
- **Plugin Development Guide**: Comprehensive documentation for plugin creators
  - Plugin structure and metadata format
  - Environment variable reference
  - Remote command execution patterns
  - Best practices and security considerations
  - Testing and debugging guide
  - Multiple example plugins (Python and shell)
- **UI Components for Plugins**: Rich-formatted plugin display functions
  - Plugin listing table with status indicators
  - Detailed plugin information panels
  - Plugin execution output formatting
  - Execution time display

## [1.4.2] - 2025-10-12

### Added
- **UI Environment Variables Support**: Comprehensive environment variable system for UI customization and accessibility
  - `LAZYSSH_HIGH_CONTRAST`: Enable high contrast theme variant for better visibility
  - `LAZYSSH_NO_RICH`: Disable Rich library features for basic terminal compatibility
  - `LAZYSSH_REFRESH_RATE`: Control refresh rate for live updates (integer, 1-10)
  - `LAZYSSH_NO_ANIMATIONS`: Disable progress animations and spinners
  - `LAZYSSH_COLORBLIND_MODE`: Enable colorblind-friendly theme variant
  - `LAZYSSH_PLAIN_TEXT`: Force plain text rendering without Rich formatting
- **Environment Variable Integration**: Seamless integration with existing Dracula theme system
  - Automatic parsing and validation of environment variables during UI initialization
  - Support for multiple boolean value formats (true/false, 1/0, yes/no, on/off)
  - Integer validation for refresh rate with bounds checking (1-10)
  - Graceful fallback to default values for invalid or missing variables
- **Comprehensive Test Coverage**: Unit tests for all environment variable functionality
  - Test coverage for boolean environment variable parsing
  - Test coverage for integer environment variable validation
  - Test coverage for theme switching integration
  - Test coverage for refresh rate bounds checking
  - Test coverage for animation disable functionality
  - Test coverage for plain text mode rendering
- **Dracula Theme Implementation**: Complete visual overhaul with modern color palette
  - Implemented comprehensive Dracula color scheme (#282a36, #f8f8f2, #8be9fd, #50fa7b, #ffb86c, #ff79c6, #bd93f9, #ff5555, #f1fa8c, #6272a4)
  - Centralized theme management with `LAZYSSH_THEME` in `ui.py`
  - Semantic color mapping for consistent visual hierarchy (info, success, error, warning, header, accent, etc.)
  - Enhanced syntax highlighting with Dracula colors for better code readability
- **Accessibility Theme Support**: Multiple theme variants for different accessibility needs
  - High contrast theme using Dracula colors with enhanced visibility
  - Colorblind-friendly theme with improved color differentiation
  - Maintained WCAG compliance across all theme variants
- **Rich Library Standardization**: Comprehensive UI component enhancements
  - Centralized console instance management with consistent theme application
  - Standardized table formatting with Dracula color scheme
  - Enhanced panel layouts with consistent border styles and padding
  - Improved progress bar styling with Dracula colors
  - Advanced Rich features integration (layout system, markdown rendering, live updates)
- **UI Performance Optimizations**: Performance monitoring and optimization features
  - `benchmark_rich_rendering()` function for performance analysis
  - `optimize_console_performance()` for optimized console instances
  - `profile_ui_performance()` for UI performance profiling and recommendations
  - Cached table templates for repeated use scenarios
  - Batch rendering updates for efficient UI operations
- **Enhanced SCP Mode Completion**: Improved tab completion behavior in SCP mode
  - Filtered current directory from completion suggestions to reduce redundancy
  - Added prevention of redundant directory changes when already in target directory
  - Enhanced user experience with more relevant completion suggestions
- **Console Instance Management**: Centralized console management system
  - New `console_instance.py` module for unified console handling
  - Centralized theme application across all UI components
  - Improved performance with optimized console configuration
  - Consistent styling and behavior across command mode, SCP mode, and terminal integration

### Changed
- **GitHub Issue Templates**: Streamlined and simplified issue submission process
  - Reduced required fields in bug report template to minimize friction
  - Simplified feature request template with clearer, shorter prompts
  - Improved user experience for issue submission while maintaining information quality
  - Reduced cognitive load for users submitting issues
- **BREAKING:** Complete visual theme overhaul across entire application
  - All UI components now use Dracula color palette instead of basic terminal colors
  - Updated banner design with sophisticated ASCII art and Dracula styling
  - Enhanced table headers, panels, and status displays with consistent Dracula colors
  - Improved visual hierarchy and information distinction throughout the application
- **Enhanced UI Components**: Upgraded all Rich library components
  - Tables now use consistent Dracula color scheme for headers and rows
  - Panels feature improved styling with Dracula colors for titles and subtitles
  - Progress bars enhanced with Dracula color scheme for better visual feedback
  - Status messages and prompts use semantic Dracula colors for better readability
- **Console Management**: Centralized console instance with theme consistency
  - All modules now use shared console instance from `ui.py`
  - Consistent theme application across command mode, SCP mode, and terminal integration
  - Improved console performance with optimized configuration settings
- **Documentation Updates**: Enhanced troubleshooting guide with environment variable details
  - Added comprehensive documentation for all supported environment variables
  - Specified exact accepted values and precedence rules
  - Updated user guide with environment variable usage examples

### Technical Improvements
- Enhanced `ui.py` with environment variable parsing and validation functions
- Added `parse_boolean_env_var()` and `parse_integer_env_var()` utility functions
- Integrated environment variable support with existing theme system
- Updated `.github/ISSUE_TEMPLATE/` files with simplified templates
- Added comprehensive test suite for UI environment variable functionality
- Updated `ui.py` with comprehensive Dracula theme definition and accessibility themes
- Enhanced `ssh.py` with Dracula-colored command display and syntax highlighting
- Improved `scp_mode.py` styling for file transfer interface with Dracula colors
- Updated `command_mode.py` styling for command interface with consistent theme
- Enhanced `__main__.py` startup messages with Dracula theme styling
- Added performance benchmarking and optimization utilities
- Created new `console_instance.py` module for centralized console management
- Improved code formatting and removed trailing whitespace across all files
- Enhanced SCP mode completion logic for better user experience

## [1.4.1] - 2025-10-12

### Added
- **Wizard Command**: New guided workflow system for complex operations
  - `wizard lazyssh` - Interactive guided SSH connection creation with step-by-step prompts
  - `wizard tunnel` - Interactive guided tunnel creation with parameter collection
  - Simplified user experience for users who prefer guided workflows over command-line arguments
  - Maintains all existing functionality while providing an alternative interface

### Changed
- **BREAKING:** Removed dual-mode system entirely
  - Eliminated prompt mode (menu-driven interface) completely
  - Removed `--prompt` command-line flag
  - Removed `mode` command and all mode-switching functionality
  - LazySSH now defaults to command mode interface only
  - Simplified codebase by removing 797 lines of obsolete mode-related code
- **BREAKING:** Removed mode-related UI elements and messaging
  - Updated help text to remove mode references
  - Removed mode switching logic from main application flow
  - Cleaned up command completion to remove mode-related suggestions

### Removed
- **BREAKING:** Prompt mode interface and all associated functionality
  - Removed `prompt_mode_main()` function
  - Removed `handle_menu_action()` and `main_menu()` functions
  - Removed all prompt mode menu functions from UI module
  - Removed mode-related imports and dependencies
- **BREAKING:** Mode switching commands and flags
  - Removed `mode` command from command mode
  - Removed `--prompt` command-line argument
  - Removed mode-related help text and error messages

### Migration Notes
- **IMPORTANT:** Users who relied on prompt mode should use the new `wizard` command instead
  - Old: `lazyssh --prompt` → New: `lazyssh` (then use `wizard` command)
  - Old: `mode` command → New: Not needed (no modes exist)
  - The `wizard` command provides similar guided experience to the old prompt mode
  - All existing command mode functionality remains unchanged


## [1.4.0] - 2025-10-12

### Added
- **Connection Configuration Management**: Comprehensive system for saving and managing SSH connection configurations
  - Save connection configurations after establishing connections (prompted automatically)
  - Store configurations in TOML format at `/tmp/lazyssh/connections.conf`
  - Support for all connection parameters: host, port, username, SSH key, shell, proxy port, terminal preference
  - Atomic file operations with proper error handling and 600 file permissions for security
  - Comment preservation in configuration file
  - Automatic config file initialization with helpful examples on first use
- **Configuration Backup System**:
  - `backup-config` command to create backup of connections.conf file
  - Backups saved as `connections.conf.backup` with same security permissions (600)
  - Graceful handling of missing config files and I/O errors
  - Protection against accidental data loss before making changes
- **Always-Visible Configuration Display**:
  - Loaded configurations now displayed on startup (when configs exist)
  - Configuration table shown after every command (like active SSH connections)
  - Consistent display ordering: configs → connections → tunnels
  - Better awareness of available saved connections at all times
- **New Commands for Configuration Management**:
  - `config` / `configs` - Display all saved configurations in a formatted table
  - `connect <config-name>` - Connect using a saved configuration
  - `save-config <config-name>` - Save current connection as a named configuration
  - `delete-config <config-name>` - Delete a saved configuration
  - `backup-config` - Create backup of configuration file
- **CLI Configuration Support**:
  - `--config` flag to load and display saved configurations on startup
  - Supports custom config file path or uses default `/tmp/lazyssh/connections.conf`
  - Non-blocking startup if config file doesn't exist
- **Enhanced Tab Completion**:
  - `connect` command suggests saved configuration names
  - `delete-config` command suggests saved configuration names
  - `save-config` command suggests active connection names
  - `backup-config` command with tab completion support
  - Dynamic completion cache that updates when configs are modified
- **Configuration Validation**:
  - Config name validation (alphanumeric, dash, underscore only)
  - Required field validation (host, port, username, socket_name)
  - SSH key file existence warnings (non-blocking)
  - Socket name conflict detection with user prompt
  - Port number validation
  - TOML parsing error handling with clear messages
- **UI Components**:
  - Rich table display for saved configurations
  - Color-coded configuration display matching SSH status table style
  - Confirmation prompts for overwriting existing configurations
  - Helpful error messages and guidance for configuration operations

### Changed
- Enhanced `config.py` module with new configuration management functions
- Updated `__main__.py` with save prompt after connection creation
- Extended `command_mode.py` with configuration commands and tab completion
- Improved `ui.py` with configuration display function
- Pre-commit checks now validate TOML syntax in configuration files

### Security
- Configuration files created with 600 permissions (owner read/write only)
- Configuration directory created with 700 permissions
- Atomic file write operations prevent corruption
- Safe handling of sensitive information (SSH keys, connection details)


## [1.3.5] - 2025-10-12

### Added
- **SCP Mode Performance Optimizations**: Implemented intelligent caching and throttling system
  - Directory listing cache with configurable 30-second TTL reduces redundant SSH commands
  - Completion throttling (300ms delay) limits query frequency during rapid typing
  - Cache automatically invalidates on directory changes (`cd`, `put` commands)
  - Expected 80-90% reduction in SSH commands during typical completion workflows
  - Cache-first strategy for both `ls` and `find` commands
- **Debug Command in SCP Mode**: Added `debug` command to toggle debug logging on/off at runtime
  - Consistent behavior with command mode debug toggle
  - Accepts optional argument for explicit control (`debug on`, `debug off`)
  - No restart required to enable/disable verbose logging
  - Debug logs always saved to `/tmp/lazyssh/logs` regardless of debug mode state

### Changed
- **Documentation Modernization**: Comprehensive update to all documentation files
  - Simplified README.md with focus on quick start and essential features
  - Restructured user-guide.md as streamlined user journey (installation → first connection → workflows)
  - Updated commands.md with current command names, removed redundant tutorial content
  - Simplified scp-mode.md and tunneling.md to focus on practical usage patterns
  - Updated troubleshooting.md to reflect current architecture
  - Corrected all references from `terminal <connection>` to `open <connection>`
  - Fixed environment variable names throughout (`LAZYSSH_TERMINAL_METHOD`)
  - Marked Terminator as optional with native terminal as default
  - Documented runtime terminal method switching
  - Updated SCP mode documentation to reflect caching and optimization features
- **Code Quality Improvements**: Enhanced variable naming consistency and code organization in SCP mode

### Removed
- Removed `install.sh` script (installation via pip/pipx only)
- Cleaned up obsolete OpenSpec CLI specification files from repository

### Performance
- SCP mode tab completion now significantly faster on high-latency connections
- Reduced network traffic during file path completion
- More responsive user experience during rapid typing in SCP mode


## [1.3.4] - 2025-10-11

### Changed
- **BREAKING:** Removed native Windows support
  - Windows OpenSSH does not support SSH control sockets (master mode `-M` flag) which is essential for LazySSH's persistent connection functionality
  - Windows users should use Windows Subsystem for Linux (WSL) to run LazySSH with full functionality
  - Documentation updated to reflect WSL requirement for Windows users
  - Platform support now officially limited to Linux and macOS

### Fixed
- Fixed SCP mode connection when no arguments provided
  - Running `scp` without arguments now correctly enters SCP mode after connection selection
  - Previously, socket path was not set after interactive connection selection, causing immediate exit
  - Existing behavior when connection is provided as argument remains unchanged


## [1.3.3] - 2025-10-11

### Added
- Terminal method can now be changed at runtime without restarting LazySSH
  - Added `terminal <method>` command in command mode to set terminal method (auto, native, terminator)
  - Terminal method now displayed in SSH connections status table
- State management for terminal method preference in SSHManager class
- New `open` command for opening terminal sessions, creating symmetry with the `close` command

### Changed
- **BREAKING:** Native terminal mode now uses subprocess instead of os.execvp()
  - Users can now exit SSH sessions (with `exit` or Ctrl+D) and return to LazySSH
  - LazySSH process remains running while native terminal is open
  - SSH connection remains active after closing terminal session
  - This allows managing multiple sessions and switching between connections
- **BREAKING:** Split `terminal` command functionality into two separate commands:
  - `open <ssh_id>` - Opens a terminal session (replaces `terminal <ssh_id>`)
  - `terminal <method>` - Changes terminal method only (auto, native, terminator)
  - This provides clearer command separation and better user experience
- `open_terminal_native()` now returns boolean (True/False) instead of None
- `open_terminal()` now returns boolean indicating success/failure
- Updated help text and documentation to reflect new command structure
- Tab completion now context-aware: `terminal` suggests methods only, `open` suggests connections only

### Migration Notes
- **IMPORTANT:** The `terminal <ssh_id>` command for opening terminals has been replaced with `open <ssh_id>`
  - Old: `terminal myserver` → New: `open myserver`
  - If you use the old syntax, LazySSH will show a helpful error message guiding you to use `open`
  - The `terminal` command now only changes terminal methods: `terminal native`, `terminal auto`, `terminal terminator`
- Users who relied on native mode exiting LazySSH will now return to LazySSH instead
- To exit LazySSH completely, use the exit menu option or command
- All existing functionality remains compatible except for the command name change above

## [1.3.2] - 2025-10-11

### Added
- Native Python terminal mode as fallback when external terminal emulator is not available
  - Uses Python's subprocess with PTY allocation for SSH sessions
  - No external terminal emulator required for basic terminal functionality
  - Works across all platforms (Linux, macOS, Windows)
- Windows platform support
  - Cross-platform executable detection using Python's `shutil.which()`
  - LazySSH now runs natively on Windows without crashes
- Terminal method configuration via `LAZYSSH_TERMINAL_METHOD` environment variable
  - Supported values: `auto`, `terminator`, `native`
  - Default is `auto` (tries available methods in order)
- Automatic terminal method detection and selection
- Enhanced logging for terminal method selection and fallback behavior

### Changed
- Terminator is now a truly optional dependency
  - Application no longer exits if Terminator is not installed
  - Displays warning message for missing optional dependencies
  - Falls back to native terminal mode automatically
- Improved dependency checking to distinguish required vs optional dependencies
  - SSH is required (openssh-client)
  - Terminator is optional (falls back to native mode)
- Replaced subprocess calls to `which` command with `shutil.which()` for cross-platform compatibility
- Updated executable detection in both `__init__.py` and `ssh.py`

### Fixed
- Fixed critical bug where missing Terminator prevented application startup
- Fixed Windows compatibility issue with executable detection
- Improved error handling for terminal opening failures

## [1.3.1] - 2025-10-10

### Added
- Comprehensive pre-commit check script with auto-fix capabilities
  - Added automatic code formatting and quality checks
  - Implemented security scanning with bandit and safety
  - Added command-line options: `--no-fix`, `--dry-run`, `--skip-tests`, `--skip-build`, `--verbose`
  - Enhanced error reporting with actionable feedback
  - Added support for isolated virtual environment (`.pre-commit-venv`) for pre-commit hooks
- Overhauled Makefile with comprehensive development commands
  - Added 25+ new make targets for development workflow
  - Implemented color-coded output for better readability
  - Added virtual environment management commands (`venv-info`)
  - Added dependency management commands (`deps-check`, `deps-update`)
  - Added code quality commands (`fmt`, `fix`, `lint`, `check`, `verify`)
  - Added testing commands with coverage support
  - Added build and release automation
  - Enhanced documentation with detailed help text
- Updated `.gitignore` to exclude pre-commit virtual environment

### Changed
- Improved pre-commit checks robustness
  - Added `set -o pipefail` to ensure pipeline failures are caught
  - Enhanced error handling for grep commands with `|| true`
  - Improved coverage file cleanup
  - Better handling of empty output in word count operations
- Updated development documentation with comprehensive guide for new Makefile and pre-commit system
- Improved variable naming consistency in `scp_mode.py`

### Removed
- Removed obsolete project management files
  - Deleted `.github/PROJECT_MANAGEMENT.md`
  - Deleted `.github/workflows/streamlined-project-management.yml`
  - Deleted `PROJECT_BOARD_SETUP.md`
  - Deleted `docs/project-management.md`

## [1.3.0] - 2025-03-29

### Added
- Implemented robust logging system using Python's logging module and rich.logging
- Added logging for all SSH connections, commands, tunnels, and file transfers
- Created dedicated log directory at /tmp/lazyssh/logs with proper permissions
- Added separate loggers for different components (SSH, Command Mode, SCP Mode)
- Implemented both console and file logging with rich formatting
- Added environment variable support for log level configuration (LAZYSSH_LOG_LEVEL)
- Added 'debug' command to toggle console log visibility (logs to files always enabled)
- Added --debug CLI flag to enable debug logging from startup
- Enhanced SCP mode logging with connection-specific logs at /tmp/lazyssh/<connection_name>.d/logs
- Improved file transfer logging in SCP mode with detailed size reporting and transfer statistics
- Added tracking and logging of total files and bytes transferred per connection

### Fixed
- Fixed incorrect file count in transfer statistics when uploading or downloading single files
- Fixed mget command to properly log each downloaded file and update total statistics
- Added progress bar display for file uploads in SCP mode similar to downloads
- Fixed SCP upload directory structure to be parallel to downloads directory (/tmp/lazyssh/<connection_name>.d/uploads)
- Fixed datetime usage in logging module to correctly format timestamps
- Fixed SCP prompt coloring to ensure consistent visual appearance
- Corrected variable naming inconsistencies in SCPMode class
- Prevented double connection establishment when entering SCP mode
- Fixed remote command execution to properly handle CompletedProcess return values
- Removed "lazy" command alias to prevent it from appearing in tab completion
- Consistent replacement of os.path with pathlib for modern Python practices
- Fixed tab completion to only show valid commands defined in the command dictionary

## [1.2.1] - 2025-03-29

### Added
- Added "tree" command to SCP mode to display remote directory structure in a hierarchical view using Rich's tree module
- Added tab completion support for the tree command matching the behavior of the ls command
- Added detailed help documentation for the tree command
- Added documentation for all new commands in user guides and command references

### Fixed
- Optimized tree command to minimize SSH connections for better performance with large directory structures
- Fixed "lcd" command in SCP mode that was present in the code but not working properly
- Added proper help documentation and tab completion for the LCD command in SCP mode

### Changed
- Removed setup.py in favor of using pyproject.toml exclusively for modern Python packaging
- Updated pre-commit checks to verify Python requirements only in pyproject.toml
- Updated documentation to reflect all new commands and features
- Improved SCP mode documentation with more detailed examples and common workflows
- Added troubleshooting information for tree command and large directory visualization
- Updated README with latest feature information and examples

## [1.2.0] - 2025-03-29

### Added
- Added Rich progress bars for file transfers in SCP mode with real-time progress, transfer rate and time estimates
- Restored the `lls` command for listing local directories with size and file count information
- Enhanced file listings using Rich tables with proper formatting and color-coded file types
- Added colorized output for better visual organization of important information

### Changed
- Improved progress tracking in SCP mode showing total bytes and elapsed time for all transfers
- Enhanced date format consistency across file listings
- Updated command help documentation to include all available commands

## [1.1.9] - 2025-03-29

### Added
- Enhanced SSH connection creation with support for additional options:
  - Custom SSH key specification (-ssh-key)
  - Custom shell selection (-shell)
  - Terminal disabling option (-no-term)

### Changed
- Improved UI with colorized confirmation prompts throughout the application
- Modernized code by replacing os.path with pathlib.Path
- Updated package configuration to resolve setuptools warnings

## [1.1.8] - 2025-03-29

### Changed
- Enhanced UI for command help with improved color coding
- Redesigned welcome banner with ASCII art logo
- Implemented dynamic version display in the welcome banner

## [1.1.7] - 2025-03-28

### Added
- Support for specifying socket name for connections

### Fixed
- Bug fixes and performance improvements

## [1.1.6] - 2025-03-28

### Changed
- UI improvements for SCP mode
- Better error handling for failed connections

## [1.1.5] - 2025-03-28

### Added
- Enhanced tab completion for command mode
- Better terminal detection

## [1.1.4] - 2025-03-28

### Fixed
- Fixed issues with directory navigation in SCP mode
- Improved error messages for connection failures

## [1.1.3] - 2025-03-09

### Changed
- Updated dependency requirements
- Code refactoring for better maintainability

## [1.1.2] - 2025-03-09

### Fixed
- Merge branch updates from main repository

## [1.1.1] - 2025-03-09

### Added
- Improved documentation
- Better handling of SSH keys

## [1.0.1] - 2025-03-09

### Fixed
- PyPI packaging fixes
- Documentation updates

## [1.0.0] - 2025-03-09

### Added
- Initial release of LazySSH
- SSH connection management with control sockets
- Tunnel creation and management (forward/reverse)
- Dynamic SOCKS proxy support
- SCP mode for file transfers
- Terminal integration
