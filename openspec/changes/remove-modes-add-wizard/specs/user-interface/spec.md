## ADDED Requirements

### Requirement: Wizard Command

The system SHALL provide a `wizard` command that offers guided, interactive workflows for complex operations, eliminating the need for mode switching while providing step-by-step guidance for common tasks.

#### Scenario: Wizard command with lazyssh workflow
- **WHEN** a user runs `wizard lazyssh`
- **THEN** the system SHALL guide the user through SSH connection creation step-by-step
- **AND** the system SHALL prompt for required parameters (IP, port, username, socket name)
- **AND** the system SHALL prompt for optional parameters (proxy, SSH key, shell, no-term flag)
- **AND** the system SHALL execute the equivalent `lazyssh` command with the provided parameters
- **AND** the workflow SHALL be identical to using the regular `lazyssh` command

#### Scenario: Wizard command with tunnel workflow
- **WHEN** a user runs `wizard tunnel`
- **THEN** the system SHALL guide the user through tunnel creation step-by-step
- **AND** the system SHALL prompt for required parameters (SSH connection, tunnel type, ports, hosts)
- **AND** the system SHALL execute the equivalent `tunc` command with the provided parameters
- **AND** the workflow SHALL be identical to using the regular `tunc` command

#### Scenario: Wizard command with invalid argument
- **WHEN** a user runs `wizard <invalid_argument>`
- **THEN** the system SHALL display an error message
- **AND** the error message SHALL list valid wizard workflows: `lazyssh`, `tunnel`
- **AND** the system SHALL provide usage examples

#### Scenario: Wizard command with no arguments
- **WHEN** a user runs `wizard` without arguments
- **THEN** the system SHALL display available wizard workflows
- **AND** the system SHALL show brief descriptions of each workflow
- **AND** the system SHALL provide usage examples

#### Scenario: Wizard command in help system
- **WHEN** a user runs `help wizard`
- **THEN** the system SHALL display detailed documentation for the wizard command
- **AND** the documentation SHALL explain available workflows
- **AND** the documentation SHALL provide examples for each workflow

## REMOVED Requirements

### Requirement: Dual Mode System
**Reason**: Prompt mode has become obsolete and mode switching adds unnecessary complexity
**Migration**: Users can use the new `wizard` command for guided workflows instead of switching to prompt mode

### Requirement: Mode Switching
**Reason**: Eliminating modes removes the need for mode switching functionality
**Migration**: All functionality is now available in the unified command interface

### Requirement: Prompt Mode Interface
**Reason**: Menu-driven interface is rarely used and adds maintenance overhead
**Migration**: Wizard command provides similar guided experience without mode complexity

### Requirement: Command Line Mode Flag
**Reason**: No longer needed since there is only one interface mode
**Migration**: Application always starts in command mode (now the only mode)
