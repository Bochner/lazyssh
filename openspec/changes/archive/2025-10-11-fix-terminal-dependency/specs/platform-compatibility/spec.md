# Platform Compatibility - Delta Spec

## MODIFIED Requirements

### Requirement: Platform-Agnostic Dependency Checking

The dependency checking system SHALL differentiate between required and optional dependencies, returning separate classifications for each.

#### Scenario: SSH dependency check returns as required
- **WHEN** checking for SSH client dependency
- **THEN** it SHALL be classified as a required dependency
- **AND** missing SSH SHALL prevent application startup

#### Scenario: Terminator dependency check returns as optional
- **WHEN** checking for Terminator terminal emulator
- **THEN** it SHALL be classified as an optional dependency
- **AND** missing Terminator SHALL NOT prevent application startup
- **AND** a warning message SHALL be displayed about the missing optional dependency

#### Scenario: Application startup with missing required dependencies
- **WHEN** the application starts and required dependencies are missing
- **THEN** the application SHALL display an error message listing the missing required dependencies
- **AND** the application SHALL exit with a non-zero exit code
- **AND** the application SHALL NOT start

#### Scenario: Application startup with missing optional dependencies
- **WHEN** the application starts and only optional dependencies are missing
- **THEN** the application SHALL display a warning message about the missing optional dependencies
- **AND** the application SHALL continue to start normally
- **AND** functionality requiring the optional dependency SHALL degrade gracefully

#### Scenario: Dependency check returns separate lists
- **WHEN** `check_dependencies()` is called
- **THEN** it SHALL return a tuple of `(required_missing, optional_missing)`
- **AND** `required_missing` SHALL contain only required dependencies that are not available
- **AND** `optional_missing` SHALL contain only optional dependencies that are not available
