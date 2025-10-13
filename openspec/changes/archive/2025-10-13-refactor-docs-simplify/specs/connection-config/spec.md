# connection-config Delta Specification

## MODIFIED Requirements
### Requirement: CLI Configuration Flag
The system SHALL accept a `--config` command-line flag to load a configuration file on startup.

#### Scenario: Launch with explicit default config path
- **WHEN** LazySSH is launched with `--config /tmp/lazyssh/connections.conf`
- **AND** the file exists
- **THEN** the system SHALL load the file
- **AND** SHALL display the configurations table without auto-connecting

#### Scenario: Launch with custom config file path
- **WHEN** LazySSH is launched with `--config /path/to/custom.conf`
- **THEN** the system SHALL load the specified configuration file
- **AND** SHALL display the configurations table

#### Scenario: Launch with non-existent config file
- **WHEN** LazySSH is launched with `--config /path/to/missing.conf`
- **THEN** the system SHALL display a warning "Configuration file not found"
- **AND** SHALL continue normal operation without loaded configurations
