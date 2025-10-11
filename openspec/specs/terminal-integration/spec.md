# terminal-integration Specification

## Purpose
TBD - created by archiving change fix-terminal-dependency. Update Purpose after archive.
## Requirements
### Requirement: Native Python Terminal Support

The system SHALL provide a native Python-based terminal method that allows users to open SSH terminal sessions without requiring external terminal emulator dependencies.

#### Scenario: Opening terminal with native method
- **WHEN** a user requests to open a terminal session
- **AND** native terminal method is selected or is the fallback
- **THEN** the system SHALL launch an SSH session using Python's native capabilities
- **AND** the SSH session SHALL have full TTY allocation for interactive use
- **AND** the terminal SHALL support all standard SSH features (colors, raw mode, signals)

#### Scenario: Native terminal uses os.execvp for direct execution
- **WHEN** the native terminal method is invoked
- **THEN** the system SHALL use `os.execvp()` to replace the current process with the SSH command
- **AND** the SSH command SHALL include the `-tt` flag for TTY allocation
- **AND** the SSH command SHALL use the control socket path from the connection
- **AND** the SSH command SHALL include any custom shell specified in the connection

#### Scenario: Terminal session inherits current terminal
- **WHEN** native terminal method launches an SSH session
- **THEN** the SSH session SHALL run in the current terminal window
- **AND** the user SHALL be dropped directly into the SSH session
- **AND** closing the SSH session SHALL end the LazySSH process (as process was replaced)

### Requirement: Terminal Method Selection

The system SHALL support multiple terminal methods and automatically select an appropriate method based on availability and configuration.

#### Scenario: Terminal method configuration via environment variable
- **WHEN** the `LAZYSSH_TERMINAL_METHOD` environment variable is set
- **THEN** the system SHALL respect the configured terminal method preference
- **AND** valid values SHALL be: `auto`, `terminator`, `native`
- **AND** `auto` SHALL be the default if not specified
- **AND** invalid values SHALL be rejected with a clear error message

#### Scenario: Auto terminal method selection
- **WHEN** terminal method is set to `auto` (default)
- **THEN** the system SHALL try terminal methods in order of preference:
  1. Terminator (if installed)
  2. Native Python method (always available)
- **AND** the system SHALL use the first available method
- **AND** the system SHALL log which method was selected

#### Scenario: Forced terminal method selection
- **WHEN** terminal method is explicitly set to `terminator` or `native`
- **THEN** the system SHALL only attempt to use the specified method
- **AND** if the specified method is unavailable, the system SHALL display an error
- **AND** the system SHALL NOT automatically fall back to another method

#### Scenario: Terminator not available with auto method
- **WHEN** terminal method is `auto`
- **AND** Terminator is not installed or not found in PATH
- **THEN** the system SHALL automatically use the native terminal method
- **AND** the system SHALL display a message indicating native method is being used
- **AND** the SSH terminal session SHALL open successfully

### Requirement: Terminal Method User Feedback

The system SHALL provide clear feedback to users about which terminal method is being used and why.

#### Scenario: Display terminal method in use
- **WHEN** opening a terminal session
- **THEN** the system SHALL display a message indicating the terminal method being used
- **AND** the message format SHALL be "Opening terminal (terminator)" or "Opening terminal (native)"
- **AND** the SSH command being executed SHALL be displayed

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

### Requirement: Backward Compatibility for External Terminal Emulators

The system SHALL maintain backward compatibility with existing Terminator terminal emulator usage while adding native terminal support.

#### Scenario: Terminator usage when installed
- **WHEN** Terminator is installed and available
- **AND** terminal method is `auto` or `terminator`
- **THEN** the system SHALL use Terminator to open terminal sessions
- **AND** the behavior SHALL be identical to previous versions
- **AND** terminal sessions SHALL open in a new Terminator window

#### Scenario: Existing connection configurations work unchanged
- **WHEN** opening a terminal for an existing SSH connection
- **THEN** all existing connection configurations SHALL continue to work
- **AND** SSH socket paths SHALL be honored
- **AND** custom shell specifications SHALL be preserved
- **AND** SSH connection options SHALL be passed correctly

