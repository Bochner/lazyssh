# user-interface Specification Delta

## ADDED Requirements

### Requirement: List Command Status Display

The system SHALL provide a `list` command that displays the current status of configurations, connections, and tunnels on demand.

#### Scenario: List command with active connections
- **WHEN** a user runs the `list` command
- **AND** there are active SSH connections
- **THEN** the system SHALL display saved configurations table (if any exist)
- **AND** the system SHALL display the active SSH connections table
- **AND** the system SHALL display tunnels for each connection (if any exist)
- **AND** the display SHALL match the status shown at startup and after commands

#### Scenario: List command with no connections
- **WHEN** a user runs the `list` command
- **AND** there are no active SSH connections
- **THEN** the system SHALL display "No active connections" message
- **AND** the message SHALL use consistent informational formatting
