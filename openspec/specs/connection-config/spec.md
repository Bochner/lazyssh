# connection-config Specification

## Purpose
TBD - created by archiving change add-connection-config-management. Update Purpose after archive.
## Requirements
### Requirement: Configuration File Storage

The system SHALL persist SSH connection configurations in a TOML-formatted file located at `/tmp/lazyssh/connections.conf`.

#### Scenario: Configuration file creation

- **WHEN** a user saves their first connection configuration
- **THEN** the system SHALL create `/tmp/lazyssh/connections.conf` with file permissions 600 (owner read/write only)
- **AND** the directory `/tmp/lazyssh/` SHALL be created if it does not exist

#### Scenario: Configuration file format

- **WHEN** a connection configuration is saved
- **THEN** the system SHALL store it as a TOML table with the connection name as the table header
- **AND** SHALL include all connection parameters: host, port, username, socket_name, ssh_key (optional), shell (optional), no_term (optional), proxy_port (optional)

#### Scenario: Multiple configurations in one file

- **WHEN** multiple configurations are saved
- **THEN** each configuration SHALL be stored as a separate TOML table in the same file
- **AND** table names SHALL be unique within the file

#### Scenario: Configuration file validation

- **WHEN** loading a configuration file
- **THEN** the system SHALL validate TOML syntax
- **AND** SHALL display specific error messages including line numbers for parsing errors
- **AND** SHALL continue operation with an empty config if the file is invalid

### Requirement: Configuration Display

The system SHALL display saved configurations in a formatted table using the Rich library.

#### Scenario: Display saved configurations table

- **WHEN** the user executes the `config` or `configs` command
- **THEN** the system SHALL display a table with columns: Name, Host, Username, Port, SSH Key, Shell, Proxy, No-Term
- **AND** SHALL use color coding consistent with existing status tables (cyan for names, magenta for hosts)
- **AND** SHALL display above the command prompt in command mode

#### Scenario: No saved configurations

- **WHEN** the configuration file does not exist or is empty
- **AND** the user executes the `config` command
- **THEN** the system SHALL display "No saved configurations" message
- **AND** SHALL not display an error

#### Scenario: Configuration display on startup with flag

- **WHEN** LazySSH is started with the `--config` flag
- **THEN** the system SHALL load and display the configuration table
- **AND** SHALL not automatically establish any connections
- **AND** SHALL allow the user to use the `connect` command to select a configuration

### Requirement: Save Configuration Prompt

The system SHALL prompt users to save connection configurations after successful connection establishment.

#### Scenario: Save prompt after successful connection

- **WHEN** a new SSH connection is successfully established
- **THEN** the system SHALL display the prompt "Save this connection configuration? (y/N)"
- **AND** default to 'No' if the user presses Enter without input

#### Scenario: User accepts save prompt

- **WHEN** the user answers 'y' or 'yes' to the save prompt
- **THEN** the system SHALL prompt for a configuration name
- **AND** SHALL suggest the socket name as the default
- **AND** SHALL save the connection parameters to the configuration file

#### Scenario: Configuration name conflict

- **WHEN** the user provides a configuration name that already exists
- **THEN** the system SHALL prompt "Configuration 'name' already exists. Overwrite? (y/N)"
- **AND** SHALL only overwrite if the user confirms with 'y' or 'yes'

#### Scenario: User declines save prompt

- **WHEN** the user answers 'n', 'no', or presses Enter at the save prompt
- **THEN** the system SHALL not save the configuration
- **AND** SHALL continue normal operation

### Requirement: Connect Command

The system SHALL provide a `connect` command to establish connections using saved configurations.

#### Scenario: Connect using saved configuration

- **WHEN** the user executes `connect <config-name>`
- **AND** the configuration exists in the file
- **THEN** the system SHALL load the connection parameters from the configuration
- **AND** SHALL create an SSH connection using those parameters
- **AND** SHALL display the SSH command that will be executed
- **AND** SHALL prompt for confirmation before connecting

#### Scenario: Connect with non-existent configuration

- **WHEN** the user executes `connect <config-name>`
- **AND** the configuration does not exist
- **THEN** the system SHALL display "Configuration 'config-name' not found"
- **AND** SHALL suggest available configuration names

#### Scenario: Connect command tab completion

- **WHEN** the user types `connect ` and presses Tab
- **THEN** the system SHALL display available configuration names as completion suggestions
- **AND** SHALL filter suggestions based on partially typed names

#### Scenario: Connect command without arguments

- **WHEN** the user executes `connect` without a configuration name
- **THEN** the system SHALL display "Usage: connect <config-name>"
- **AND** SHALL list available configuration names

### Requirement: Manual Configuration Management Commands

The system SHALL provide commands to manually save and delete configurations.

#### Scenario: Save configuration command

- **WHEN** the user executes `save-config <config-name>`
- **AND** a connection context is available (recent or current connection)
- **THEN** the system SHALL save the connection parameters with the specified name
- **AND** SHALL display "Configuration 'config-name' saved"

#### Scenario: Save configuration without name

- **WHEN** the user executes `save-config` without a name argument
- **THEN** the system SHALL display "Usage: save-config <config-name>"

#### Scenario: Delete configuration command

- **WHEN** the user executes `delete-config <config-name>`
- **AND** the configuration exists
- **THEN** the system SHALL prompt for confirmation "Delete configuration 'config-name'? (y/N)"
- **AND** SHALL remove the configuration only if confirmed

#### Scenario: Delete non-existent configuration

- **WHEN** the user executes `delete-config <config-name>`
- **AND** the configuration does not exist
- **THEN** the system SHALL display "Configuration 'config-name' not found"

#### Scenario: Delete configuration tab completion

- **WHEN** the user types `delete-config ` and presses Tab
- **THEN** the system SHALL display available configuration names as completion suggestions

### Requirement: CLI Configuration Flag

The system SHALL accept a `--config` command-line flag to load a configuration file on startup.

#### Scenario: Launch with default config file

- **WHEN** LazySSH is launched with `--config` flag and no path argument
- **THEN** the system SHALL load `/tmp/lazyssh/connections.conf`
- **AND** SHALL display the configurations table
- **AND** SHALL not automatically connect

#### Scenario: Launch with custom config file path

- **WHEN** LazySSH is launched with `--config /path/to/custom.conf`
- **THEN** the system SHALL load the specified configuration file
- **AND** SHALL display the configurations table

#### Scenario: Launch with non-existent config file

- **WHEN** LazySSH is launched with `--config` flag
- **AND** the specified file does not exist
- **THEN** the system SHALL display a warning "Configuration file not found"
- **AND** SHALL continue normal operation without loaded configurations

### Requirement: Configuration Parameter Support

The system SHALL support saving and loading all connection parameters.

#### Scenario: Save all connection parameters

- **WHEN** a configuration is saved
- **THEN** the system SHALL store host, port, username, socket_name as required fields
- **AND** SHALL store ssh_key, shell, no_term, proxy_port as optional fields
- **AND** SHALL preserve SSH key file paths as-is (expanding ~ to home directory on load)

#### Scenario: Load configuration with optional parameters

- **WHEN** a configuration is loaded
- **AND** optional parameters are missing from the TOML file
- **THEN** the system SHALL use default values (None for ssh_key, shell; False for no_term; None for proxy_port)

#### Scenario: SSH key path validation on save

- **WHEN** a configuration with an ssh_key path is saved
- **AND** the SSH key file does not exist
- **THEN** the system SHALL display a warning "SSH key file not found: <path>"
- **AND** SHALL still save the configuration

### Requirement: Menu Mode Integration

The system SHALL integrate configuration management into menu mode.

#### Scenario: View configurations from menu

- **WHEN** the user selects the "View saved configurations" menu option
- **THEN** the system SHALL display the configurations table
- **AND** SHALL return to the main menu

#### Scenario: Connect from menu

- **WHEN** the user selects "Connect from saved config" menu option
- **THEN** the system SHALL display a numbered list of saved configurations
- **AND** SHALL prompt the user to select a number
- **AND** SHALL establish a connection with the selected configuration

#### Scenario: Save from menu

- **WHEN** the user selects "Save current connection" after establishing a connection
- **THEN** the system SHALL prompt for a configuration name
- **AND** SHALL save the connection parameters

#### Scenario: Delete from menu

- **WHEN** the user selects "Delete saved config" menu option
- **THEN** the system SHALL display a numbered list of saved configurations
- **AND** SHALL prompt the user to select a number
- **AND** SHALL prompt for confirmation before deletion

### Requirement: Error Handling and Validation

The system SHALL handle configuration errors gracefully with informative messages.

#### Scenario: TOML parsing error

- **WHEN** the configuration file contains invalid TOML syntax
- **THEN** the system SHALL display an error message with the line number and specific error
- **AND** SHALL operate as if no configurations exist

#### Scenario: Invalid configuration name

- **WHEN** the user attempts to save a configuration with invalid characters
- **THEN** the system SHALL display "Invalid configuration name. Use alphanumeric characters, dashes, and underscores only"
- **AND** SHALL not save the configuration

#### Scenario: File permission error

- **WHEN** the system cannot write to the configuration file due to permissions
- **THEN** the system SHALL display "Cannot write to configuration file: permission denied"
- **AND** SHALL log the error for debugging

#### Scenario: Missing required fields in config

- **WHEN** a configuration is loaded
- **AND** required fields (host, port, username, socket_name) are missing
- **THEN** the system SHALL display "Invalid configuration 'config-name': missing required field '<field>'"
- **AND** SHALL not attempt to establish the connection

### Requirement: Configuration Operation Logging

The system SHALL log all configuration management operations for debugging and audit purposes.

#### Scenario: Log configuration save

- **WHEN** a configuration is saved
- **THEN** the system SHALL log "Configuration 'config-name' saved to <path>"

#### Scenario: Log configuration load

- **WHEN** configurations are loaded
- **THEN** the system SHALL log "Loaded <count> configuration(s) from <path>"

#### Scenario: Log configuration deletion

- **WHEN** a configuration is deleted
- **THEN** the system SHALL log "Configuration 'config-name' deleted from <path>"

#### Scenario: Log configuration errors

- **WHEN** a configuration operation fails
- **THEN** the system SHALL log the error with full details including stack trace for debugging

