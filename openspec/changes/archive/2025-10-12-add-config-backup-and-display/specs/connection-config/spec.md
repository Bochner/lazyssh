# connection-config Specification Delta

## ADDED Requirements

### Requirement: Configuration Backup Command

The system SHALL provide a command to backup the connections configuration file.

#### Scenario: Backup existing configuration file

- **WHEN** the user executes the `backup-config` command
- **AND** the configuration file `/tmp/lazyssh/connections.conf` exists
- **THEN** the system SHALL create a copy at `/tmp/lazyssh/connections.conf.backup`
- **AND** SHALL set file permissions to 600 (owner read/write only)
- **AND** SHALL display "Configuration backed up to /tmp/lazyssh/connections.conf.backup"

#### Scenario: Backup overwrites previous backup

- **WHEN** the user executes `backup-config`
- **AND** a previous backup file exists
- **THEN** the system SHALL overwrite the previous backup file
- **AND** SHALL not prompt for confirmation

#### Scenario: Backup with no configuration file

- **WHEN** the user executes `backup-config`
- **AND** the configuration file does not exist
- **THEN** the system SHALL display "No configuration file to backup"
- **AND** SHALL not create a backup file

#### Scenario: Backup with permission error

- **WHEN** the user executes `backup-config`
- **AND** the system cannot write to the backup file due to permissions
- **THEN** the system SHALL display "Cannot create backup: permission denied"
- **AND** SHALL log the error for debugging

#### Scenario: Backup atomic operation

- **WHEN** creating a backup
- **THEN** the system SHALL use atomic file operations (write to temp, then rename)
- **AND** SHALL ensure the original file is not corrupted if backup fails

### Requirement: Always-Visible Configuration Display

The system SHALL display loaded configurations in the status view whenever saved configurations exist.

#### Scenario: Display loaded configs on startup

- **WHEN** LazySSH starts in command mode
- **AND** saved configurations exist
- **THEN** the system SHALL automatically load and display the configurations table
- **AND** SHALL display above the command prompt

#### Scenario: Display loaded configs after every command

- **WHEN** a command is executed in command mode
- **AND** saved configurations exist
- **THEN** the system SHALL display the configurations table
- **AND** SHALL display before active SSH connections (if any)
- **AND** SHALL maintain consistent ordering: configs → connections → tunnels

#### Scenario: No display when configs are empty

- **WHEN** the configuration file is empty or does not exist
- **THEN** the system SHALL not display a configurations table
- **AND** SHALL only display active connections and tunnels (if any)

#### Scenario: Display format consistency

- **WHEN** displaying loaded configurations in status view
- **THEN** the system SHALL use the same table format as the `config` command
- **AND** SHALL include columns: Name, Host, Username, Port, SSH Key, Shell, Proxy, No-Term
- **AND** SHALL use consistent color coding (cyan for names, magenta for hosts)

#### Scenario: Display in menu mode startup

- **WHEN** LazySSH starts in menu mode
- **AND** saved configurations exist
- **THEN** the system SHALL display the configurations table before the menu
- **AND** SHALL provide visual separation from menu options

### Requirement: Configuration Display Integration

The system SHALL integrate configuration display into the existing status reporting system.

#### Scenario: Status display ordering

- **WHEN** showing status (startup or after commands)
- **AND** multiple status items exist (configs, connections, tunnels)
- **THEN** the system SHALL display in order:
  1. Loaded Configurations (if any)
  2. Active SSH Connections (if any)
  3. Active Tunnels (if any for each connection)

#### Scenario: Configuration changes reflect immediately

- **WHEN** a configuration is saved, updated, or deleted
- **AND** status is displayed
- **THEN** the system SHALL reflect the current state of saved configurations
- **AND** SHALL reload configurations from disk if needed

#### Scenario: Performance consideration

- **WHEN** displaying status
- **THEN** the system SHALL load configurations efficiently
- **AND** SHALL cache loaded configs within a command execution cycle
- **AND** SHALL not cause noticeable delay in command execution

### Requirement: Backup Command Help Integration

The system SHALL include the backup-config command in help and documentation.

#### Scenario: Help command includes backup-config

- **WHEN** the user executes the `help` command
- **THEN** the system SHALL list `backup-config` in available commands
- **AND** SHALL describe it as "Backup the connections configuration file"

#### Scenario: Tab completion for backup-config

- **WHEN** the user types `backup` and presses Tab
- **THEN** the system SHALL suggest `backup-config` as a completion option

#### Scenario: Command without arguments

- **WHEN** the user executes `backup-config` with any arguments
- **THEN** the system SHALL ignore the arguments
- **AND** SHALL proceed with backup operation

