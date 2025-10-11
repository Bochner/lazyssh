# terminal-integration Specification Deltas

## MODIFIED Requirements

### Requirement: Terminal Method User Feedback

The system SHALL provide clear feedback to users about which terminal method is being used, display the terminal method in the connections status table, and allow users to change the terminal method at runtime using a dedicated command.

#### Scenario: Display terminal method in use
- **WHEN** opening a terminal session
- **THEN** the system SHALL display a message indicating the terminal method being used
- **AND** the message format SHALL be "Opening terminal (terminator)" or "Opening terminal (native)"
- **AND** the SSH command being executed SHALL be displayed

#### Scenario: Display terminal method in SSH status table
- **WHEN** displaying the SSH connections status table
- **THEN** the table SHALL include a "Terminal Method" column
- **AND** the column SHALL display the currently configured terminal method (e.g., "native", "terminator", "auto")
- **AND** the display SHALL reflect the current runtime setting, not necessarily the environment variable

#### Scenario: Change terminal method at runtime via dedicated command
- **WHEN** a user issues the `terminal <method>` command in command mode
- **AND** `<method>` is one of: `auto`, `terminator`, or `native`
- **THEN** the system SHALL update the terminal method preference for the current session
- **AND** the system SHALL display a confirmation message: "Terminal method set to: <method>"
- **AND** subsequent terminal sessions SHALL use the new method
- **AND** existing SSH connections SHALL not be affected

#### Scenario: Change terminal method at runtime via menu
- **WHEN** a user selects the "Change terminal method" option in menu mode
- **THEN** the system SHALL display available terminal methods
- **AND** the system SHALL prompt the user to select a method
- **AND** upon selection, the system SHALL update the terminal method preference
- **AND** the system SHALL display a confirmation message

#### Scenario: Invalid terminal method command
- **WHEN** a user issues the `terminal <method>` command with an invalid method
- **THEN** the system SHALL display an error message
- **AND** the error message SHALL list valid options: `auto`, `terminator`, `native`
- **AND** the current terminal method SHALL remain unchanged

#### Scenario: Warning for missing optional terminal emulator
- **WHEN** the application starts
- **AND** Terminator is not installed
- **THEN** the system SHALL display a warning: "Terminator terminal emulator not found (optional)"
- **AND** the system SHALL indicate that native terminal method will be used as fallback
- **AND** the application SHALL continue to start normally

#### Scenario: Error feedback for terminal method failures
- **WHEN** a terminal method fails to open a session
- **THEN** the system SHALL display a clear error message indicating which method failed
- **AND** the system SHALL log the error details
- **AND** if using auto method, the system SHALL attempt the next available method

## ADDED Requirements

### Requirement: Terminal Opening Command

The system SHALL provide a dedicated `open` command for opening terminal sessions on SSH connections, creating symmetry with the existing `close` command and separating terminal session management from terminal method configuration.

#### Scenario: Open terminal session with open command
- **WHEN** a user issues the `open <ssh_id>` command in command mode
- **AND** `<ssh_id>` refers to an active SSH connection
- **THEN** the system SHALL open a terminal session for that connection
- **AND** the system SHALL use the currently configured terminal method
- **AND** the system SHALL display feedback about which terminal method is being used

#### Scenario: Open command with non-existent connection
- **WHEN** a user issues the `open <ssh_id>` command
- **AND** `<ssh_id>` does not refer to any active connection
- **THEN** the system SHALL display an error: "SSH connection '<ssh_id>' not found"
- **AND** no terminal session SHALL be opened

#### Scenario: Open command with no arguments
- **WHEN** a user issues the `open` command without arguments
- **THEN** the system SHALL display usage help: "Usage: open <ssh_id>"
- **AND** the system SHALL provide an example: "Example: open ubuntu"

#### Scenario: Open command tab completion
- **WHEN** a user types `open ` and requests tab completion
- **THEN** the system SHALL suggest all active SSH connection names
- **AND** the suggestions SHALL match the connection names shown in the status table

#### Scenario: Symmetric open and close commands
- **WHEN** a user opens a terminal with `open <ssh_id>`
- **AND** later closes the connection with `close <ssh_id>`
- **THEN** the commands SHALL use the same connection identifier format
- **AND** the connection SHALL close successfully
- **AND** the user experience SHALL be consistent and intuitive

## MODIFIED Requirements

### Requirement: Runtime Terminal Method Management

The system SHALL allow users to query and modify the terminal method preference during runtime without requiring application restart or environment variable changes. The `terminal` command SHALL be dedicated exclusively to terminal method management and SHALL NOT open terminal sessions.

#### Scenario: Query current terminal method
- **WHEN** a user views the SSH status display
- **THEN** the current terminal method SHALL be visible in the status table
- **AND** the method SHALL reflect the active runtime setting

#### Scenario: Terminal method persists for session duration
- **WHEN** a user changes the terminal method at runtime using the `terminal` command
- **THEN** the new method SHALL be used for all subsequent terminal operations
- **AND** the setting SHALL persist until LazySSH is closed
- **AND** the setting SHALL NOT be saved to disk or persist across LazySSH restarts

#### Scenario: Terminal method does not affect existing sessions
- **WHEN** a user has active terminal sessions open
- **AND** the user changes the terminal method setting
- **THEN** existing terminal sessions SHALL continue using their original method
- **AND** only new terminal sessions SHALL use the updated method

#### Scenario: Terminal command only accepts method names
- **WHEN** a user issues the `terminal <arg>` command
- **AND** `<arg>` is not one of: `auto`, `terminator`, or `native`
- **THEN** the system SHALL check if `<arg>` matches an SSH connection name
- **AND** if it matches a connection name, the system SHALL display a helpful error: "To open a terminal, use: open <ssh_id>"
- **AND** if it does not match a connection name, the system SHALL display: "Invalid terminal method. Valid options: auto, native, terminator"
- **AND** the terminal method SHALL remain unchanged

#### Scenario: Open command only accepts connection names
- **WHEN** a user issues the `open <arg>` command
- **AND** `<arg>` is one of: `auto`, `terminator`, or `native`
- **THEN** the system SHALL display a helpful error: "To change terminal method, use: terminal <method>"
- **AND** no terminal session SHALL be opened

