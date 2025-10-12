# User Interface Specification

## Purpose
Define the user interface capabilities for lazySSH, including command-line operations, help system, and guided workflows.
## Requirements
### Requirement: Command Line Interface
The system SHALL provide a command-line interface for all operations.

#### Scenario: Basic command execution
- **WHEN** a user runs a command
- **THEN** the system SHALL execute the command and return results
- **AND** the system SHALL display appropriate output or error messages

### Requirement: Help System
The system SHALL provide comprehensive help documentation accessible via the `help` command.

#### Scenario: Help command usage
- **WHEN** a user runs `help` or `help <command>`
- **THEN** the system SHALL display relevant documentation
- **AND** the documentation SHALL include usage examples and parameter descriptions

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

### Requirement: Unified Command Interface

The system SHALL operate in a single unified command mode, eliminating the complexity of mode switching while maintaining all functionality through direct commands and wizard workflows.

#### Scenario: Single mode operation
- **WHEN** the application starts
- **THEN** it SHALL operate in command mode only
- **AND** mode switching functionality SHALL not be available
- **AND** all operations SHALL be accessible through direct commands or wizard workflows

