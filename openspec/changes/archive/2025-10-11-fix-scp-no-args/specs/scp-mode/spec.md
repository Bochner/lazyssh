# scp-mode Specification

## ADDED Requirements

### Requirement: SCP Mode Entry Without Arguments

The system SHALL allow users to enter SCP mode without providing a connection argument, prompting them to select from available connections, and SHALL establish the connection before entering the interactive SCP prompt.

#### Scenario: Interactive connection selection

- **WHEN** a user runs the `scp` command without arguments
- **THEN** the system SHALL display a list of active SSH connections
- **AND** the system SHALL prompt the user to select a connection by number
- **AND** after selection, the system SHALL establish the socket connection
- **AND** the system SHALL enter the interactive SCP mode with the selected connection

#### Scenario: Direct connection specification

- **WHEN** a user runs the `scp <connection_name>` command
- **THEN** the system SHALL validate the connection exists
- **AND** the system SHALL establish the socket connection directly
- **AND** the system SHALL enter the interactive SCP mode with that connection

#### Scenario: Connection selection establishes socket path

- **WHEN** a user selects a connection interactively (via `scp` with no args)
- **THEN** the system SHALL set the socket path to `/tmp/{connection_name}`
- **AND** the socket path SHALL be available before calling the connect method
- **AND** the connection SHALL succeed if the socket exists and is valid
