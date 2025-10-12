# Changelog

All notable changes to LazySSH will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]


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
  - Added "Change terminal method" menu option in menu mode (option 8)
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
- Added SCP mode support to prompt mode
- Enhanced SSH connection creation in prompt mode with support for additional options:
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