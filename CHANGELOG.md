# Changelog

All notable changes to LazySSH will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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