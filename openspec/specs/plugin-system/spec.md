# plugin-system Specification

## Purpose
Document LazySSH's plugin discovery, metadata handling, execution workflow, and safety requirements for built-in and user-provided plugins.
## Requirements
### Requirement: Plugin Discovery
The system SHALL automatically discover plugins from the following locations in order of precedence (first match wins):

1. Directories provided via `LAZYSSH_PLUGIN_DIRS` (left to right)
2. Default user directory: `~/.lazyssh/plugins`
3. Runtime directory: `/tmp/lazyssh/plugins`
4. Packaged built-in directory: `lazyssh/plugins/` (installed with the package)

#### Scenario: Runtime directory included
- **WHEN** plugin discovery runs
- **THEN** the `/tmp/lazyssh/plugins` directory SHALL be included in the search order as specified
- **AND** non-existent directories SHALL be ignored without error

### Requirement: Plugin Directory Creation
The system SHALL ensure the existence of `/tmp/lazyssh/plugins` at program startup.

#### Scenario: Create runtime plugin directory
- **WHEN** the program starts
- **THEN** the directory `/tmp/lazyssh/plugins` SHALL be created if it does not exist
- **AND** permissions SHALL be set to `0700`
- **AND** failures SHALL be logged without crashing the application

### Requirement: Plugin Metadata Extraction
The system SHALL extract metadata from plugin files using structured comments at the beginning of the file.

#### Scenario: Parse plugin metadata
- **WHEN** plugin file contains metadata comments (PLUGIN_NAME, PLUGIN_DESCRIPTION, PLUGIN_REQUIREMENTS, PLUGIN_VERSION)
- **THEN** system extracts and stores metadata for display in plugin info

#### Scenario: Missing metadata
- **WHEN** plugin file lacks metadata comments
- **THEN** system uses filename as name and displays "No description available"

### Requirement: Plugin Execution
The system SHALL execute plugins as subprocesses with connection information passed via environment variables.

#### Scenario: Execute plugin successfully
- **WHEN** user runs `plugin run <plugin_name> <socket_name>` with valid plugin and active connection
- **THEN** system sets environment variables (LAZYSSH_SOCKET, LAZYSSH_HOST, LAZYSSH_PORT, LAZYSSH_USER, LAZYSSH_SOCKET_PATH) and executes plugin
- **AND** plugin output streams to user in real-time
- **AND** execution time is displayed upon completion

#### Scenario: Execute with invalid socket
- **WHEN** user runs plugin with socket name that doesn't exist
- **THEN** system displays error "Socket '<socket_name>' not found" and lists active sockets

#### Scenario: Execute with invalid plugin
- **WHEN** user attempts to run non-existent or invalid plugin
- **THEN** system displays error "Plugin '<plugin_name>' not found" and suggests available plugins

#### Scenario: Plugin execution failure
- **WHEN** plugin exits with non-zero exit code
- **THEN** system displays error message with exit code and stderr output

### Requirement: Plugin Environment Variables
The system SHALL provide plugins with connection context through standardized environment variables.

#### Scenario: Environment variables available to plugin
- **WHEN** plugin is executed
- **THEN** following environment variables are set:
  - `LAZYSSH_SOCKET` - Control socket name
  - `LAZYSSH_HOST` - Remote host address
  - `LAZYSSH_PORT` - SSH port number
  - `LAZYSSH_USER` - SSH username
  - `LAZYSSH_SOCKET_PATH` - Full path to control socket file
  - `LAZYSSH_SSH_KEY` - Path to SSH key (if key-based auth used)
  - `LAZYSSH_PLUGIN_API_VERSION` - Plugin API version (initially "1")

### Requirement: Plugin Command Interface
The system SHALL provide a `plugin` command in command mode with subcommands for plugin management.

#### Scenario: Plugin list subcommand
- **WHEN** user runs `plugin list` or `plugin`
- **THEN** system displays table of available plugins with columns: Name, Type, Description, Status

#### Scenario: Plugin run subcommand
- **WHEN** user runs `plugin run <plugin_name> <socket_name>`
- **THEN** system executes the specified plugin with the specified SSH connection

#### Scenario: Plugin info subcommand
- **WHEN** user runs `plugin info <plugin_name>`
- **THEN** system displays detailed information including name, description, version, requirements, and file path

#### Scenario: Plugin help
- **WHEN** user runs `plugin --help` or `help plugin`
- **THEN** system displays usage information and examples for plugin command

### Requirement: Tab Completion for Plugins
The system SHALL provide tab completion for plugin names and socket names in plugin commands.

#### Scenario: Tab complete plugin names
- **WHEN** user types `plugin run <TAB>`
- **THEN** system suggests available plugin names

#### Scenario: Tab complete socket names
- **WHEN** user types `plugin run enumerate <TAB>`
- **THEN** system suggests active socket names

### Requirement: Plugin Output Handling
The system SHALL capture and display plugin output with proper formatting and error handling.

#### Scenario: Stream stdout in real-time
- **WHEN** plugin writes to stdout
- **THEN** output is displayed immediately to user without buffering

#### Scenario: Display stderr separately
- **WHEN** plugin writes to stderr
- **THEN** stderr output is displayed in red/error color to distinguish from stdout

#### Scenario: Show execution progress
- **WHEN** plugin is running
- **THEN** system displays progress indicator or spinner

#### Scenario: Display execution time
- **WHEN** plugin completes (success or failure)
- **THEN** system displays total execution time in seconds

### Requirement: Enumeration Plugin
The system SHALL include a built-in `enumerate.py` plugin that performs comprehensive system enumeration on remote machines.

#### Scenario: Execute enumeration with default output
- **WHEN** user runs `plugin run enumerate <socket_name>`
- **THEN** plugin executes remote commands to gather system information
- **AND** output is displayed in human-readable format with sections for each category

#### Scenario: JSON output format
- **WHEN** plugin supports format flag and user requests JSON output
- **THEN** enumeration data is returned as structured JSON

#### Scenario: Enumeration categories
- **WHEN** enumerate plugin runs successfully
- **THEN** following information categories are collected:
  - Operating system and kernel information
  - User accounts and groups
  - Network configuration (interfaces, IPs, routes, listening ports)
  - Running processes and services
  - Installed software packages (apt/yum/pacman)
  - Filesystem mounts and disk usage
  - Environment variables
  - Scheduled tasks (cron, systemd timers)
  - Security configurations (firewall, SELinux/AppArmor)
  - Recent system and auth logs
  - Hardware information

#### Scenario: Graceful degradation
- **WHEN** enumeration command is not available or fails
- **THEN** plugin logs warning and continues with other checks
- **AND** missing data sections are marked as "N/A" or "Permission Denied"

#### Scenario: Remote OS detection
- **WHEN** enumerate plugin detects different Linux distributions
- **THEN** plugin adapts commands appropriately (apt vs yum vs pacman)

### Requirement: Plugin Development Documentation
The system SHALL provide documentation for users to develop their own plugins.

#### Scenario: Plugin template available
- **WHEN** user wants to create new plugin
- **THEN** template file with example structure is available in plugins directory

#### Scenario: Development guide
- **WHEN** user reads plugin README.md
- **THEN** documentation explains:
  - Plugin file structure and metadata format
  - Available environment variables
  - How to execute SSH commands using control socket
  - Best practices for error handling
  - Security considerations
  - Example plugins (Python and Shell)

### Requirement: Plugin Safety Warnings
The system SHALL warn users about plugin execution risks.

#### Scenario: First-time plugin execution warning
- **WHEN** user runs any non-built-in plugin for first time
- **THEN** system displays warning about reviewing plugin code before execution
- **AND** requires user confirmation to proceed

#### Scenario: Built-in plugin trust
- **WHEN** user runs built-in plugin (enumerate.py)
- **THEN** no warning is displayed as built-in plugins are trusted

### Requirement: Discovery Safety
Discovery SHALL avoid following symlinks outside declared plugin directories and SHALL handle broken symlinks gracefully without crashing. The search MUST be restricted to configured directories and only consider top-level files by default.

#### Scenario: Symlink outside base is ignored
- **WHEN** a symlink points outside a configured plugin directory
- **THEN** it SHALL be skipped and not loaded

### Requirement: Python Plugin Permission Resilience
Python plugins SHALL remain runnable even when installation strips executable permissions or prevents file access during validation, with best-effort remediation and clear user feedback.
#### Scenario: Python plugin shebang check failure
- **WHEN** a Python plugin file cannot be opened for shebang validation
- **THEN** validation SHALL mark it as valid with a warning instead of invalid
- **AND** execution SHALL proceed via the Python interpreter regardless of shebang presence.

#### Scenario: Built-in plugin validation robustness
- **WHEN** LazySSH discovers built-in Python plugins
- **THEN** file access failures during validation SHALL not prevent plugin discovery or execution
- **AND** plugins SHALL execute successfully via interpreter even without executable permissions or readable shebangs.

