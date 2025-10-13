# user-interface Delta Specification

## ADDED Requirements

### Requirement: Plugin Command

The system SHALL provide a `plugin` command in command mode that enables users to discover, inspect, and execute plugins through established SSH connections.

#### Scenario: Plugin command without arguments
- **WHEN** a user runs `plugin` without arguments
- **THEN** the system SHALL display a table listing all available plugins
- **AND** the table SHALL include columns for Name, Type (Python/Shell), Description, and Status
- **AND** the display SHALL use consistent Dracula theme styling with Rich table formatting

#### Scenario: Plugin list subcommand
- **WHEN** a user runs `plugin list`
- **THEN** the system SHALL display a formatted table of all discovered plugins
- **AND** each plugin entry SHALL show its name, file type, one-line description, and validation status
- **AND** invalid plugins SHALL be clearly marked with warning indicators

#### Scenario: Plugin run subcommand
- **WHEN** a user runs `plugin run <plugin_name> <socket_name>` with valid parameters
- **THEN** the system SHALL validate that the plugin exists and is executable
- **AND** the system SHALL validate that the socket name refers to an active SSH connection
- **AND** the system SHALL execute the plugin with appropriate environment variables
- **AND** the system SHALL display plugin output in real-time using Rich live display
- **AND** the system SHALL show execution time upon completion

#### Scenario: Plugin info subcommand
- **WHEN** a user runs `plugin info <plugin_name>`
- **THEN** the system SHALL display detailed information about the specified plugin
- **AND** the display SHALL include plugin name, description, version, requirements, and file path
- **AND** the display SHALL use a Rich panel with consistent Dracula theme styling

#### Scenario: Plugin help subcommand
- **WHEN** a user runs `plugin --help` or `help plugin`
- **THEN** the system SHALL display comprehensive usage documentation
- **AND** the documentation SHALL include syntax for all subcommands (list, run, info)
- **AND** the documentation SHALL provide usage examples
- **AND** the display SHALL use Rich markdown rendering with consistent styling

#### Scenario: Tab completion for plugin names
- **WHEN** a user types `plugin run <TAB>` in command mode
- **THEN** the system SHALL suggest available plugin names for completion
- **AND** completion SHALL filter based on partial input

#### Scenario: Tab completion for socket names in plugin command
- **WHEN** a user types `plugin run <plugin_name> <TAB>` in command mode
- **THEN** the system SHALL suggest active socket names for completion
- **AND** completion SHALL only show currently established connections

#### Scenario: Plugin execution with progress indicator
- **WHEN** a plugin is running
- **THEN** the system SHALL display a progress indicator or spinner using Rich styling
- **AND** the indicator SHALL update in real-time
- **AND** the indicator SHALL follow Dracula theme colors

#### Scenario: Plugin execution error handling
- **WHEN** plugin execution fails or exits with non-zero status
- **THEN** the system SHALL display error messages in red using Dracula error color (#ff5555)
- **AND** the system SHALL show the exit code and stderr output
- **AND** the system SHALL suggest troubleshooting steps if applicable

#### Scenario: Plugin not found error
- **WHEN** a user attempts to run a non-existent plugin
- **THEN** the system SHALL display error message "Plugin '<plugin_name>' not found"
- **AND** the system SHALL suggest running `plugin list` to see available plugins
- **AND** error formatting SHALL use consistent display_error styling

#### Scenario: Socket not found error
- **WHEN** a user attempts to run a plugin with non-existent socket name
- **THEN** the system SHALL display error message "Socket '<socket_name>' not found"
- **AND** the system SHALL list currently active socket names
- **AND** error formatting SHALL use consistent display_error styling
