# Terminal Integration Spec Deltas

## MODIFIED Requirements

### Requirement: Native Python Terminal Support

The system SHALL provide a native Python-based terminal method that allows users to open SSH terminal sessions without requiring external terminal emulator dependencies, and SHALL allow users to return to LazySSH after closing the terminal session.

#### Scenario: Opening terminal with native method as subprocess
- **WHEN** a user requests to open a terminal session with native method
- **THEN** the system SHALL launch an SSH session using Python's subprocess capabilities
- **AND** the SSH session SHALL run as a child process, not replacing the LazySSH process
- **AND** the SSH session SHALL have full TTY allocation for interactive use (`-tt` flag)
- **AND** the terminal SHALL support all standard SSH features (colors, raw mode, signals)

#### Scenario: Native terminal session runs in current terminal
- **WHEN** the native terminal method launches an SSH session
- **THEN** the SSH session SHALL run in the current terminal window
- **AND** the user SHALL be dropped into the SSH session
- **AND** the LazySSH process SHALL continue running in the background

#### Scenario: Returning to LazySSH after native terminal session
- **WHEN** a user closes an SSH session opened with native method (via `exit` command or Ctrl+D)
- **THEN** the SSH session process SHALL terminate
- **AND** control SHALL return to the LazySSH interface
- **AND** all SSH connections SHALL remain active
- **AND** the user SHALL be able to open additional terminal sessions or perform other LazySSH operations

#### Scenario: Native terminal uses subprocess for execution
- **WHEN** the native terminal method is invoked
- **THEN** the system SHALL use `subprocess.run()` to execute the SSH command as a child process
- **AND** the SSH command SHALL include the `-tt` flag for TTY allocation
- **AND** the SSH command SHALL use the control socket path from the connection
- **AND** the SSH command SHALL include any custom shell specified in the connection
- **AND** the subprocess SHALL run in the foreground until the user exits the SSH session

### Requirement: Terminal Method Selection

The system SHALL support multiple terminal methods, automatically select an appropriate method based on availability and configuration, and allow users to change the terminal method at runtime.

#### Scenario: Terminal method configuration via environment variable
- **WHEN** the `LAZYSSH_TERMINAL_METHOD` environment variable is set
- **THEN** the system SHALL use the configured terminal method as the initial preference
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

The system SHALL provide clear feedback to users about which terminal method is being used, display the terminal method in the connections status table, and allow users to change the terminal method at runtime.

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

#### Scenario: Change terminal method at runtime via command
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

### Requirement: Backward Compatibility for External Terminal Emulators

The system SHALL maintain backward compatibility with existing Terminator terminal emulator usage while enhancing native terminal support.

#### Scenario: Terminator usage when installed
- **WHEN** Terminator is installed and available
- **AND** terminal method is `auto` or `terminator`
- **THEN** the system SHALL use Terminator to open terminal sessions
- **AND** the behavior SHALL be identical to previous versions (spawns new window)
- **AND** terminal sessions SHALL open in a new Terminator window
- **AND** the Terminator window SHALL remain independent of the LazySSH process

#### Scenario: Existing connection configurations work unchanged
- **WHEN** opening a terminal for an existing SSH connection
- **THEN** all existing connection configurations SHALL continue to work
- **AND** SSH socket paths SHALL be honored
- **AND** custom shell specifications SHALL be preserved
- **AND** SSH connection options SHALL be passed correctly

## ADDED Requirements

### Requirement: Runtime Terminal Method Management

The system SHALL allow users to query and modify the terminal method preference during runtime without requiring application restart or environment variable changes.

#### Scenario: Query current terminal method
- **WHEN** a user views the SSH status display
- **THEN** the current terminal method SHALL be visible in the status table
- **AND** the method SHALL reflect the active runtime setting

#### Scenario: Terminal method persists for session duration
- **WHEN** a user changes the terminal method at runtime
- **THEN** the new method SHALL be used for all subsequent terminal operations
- **AND** the setting SHALL persist until LazySSH is closed
- **AND** the setting SHALL NOT be saved to disk or persist across LazySSH restarts

#### Scenario: Terminal method does not affect existing sessions
- **WHEN** a user has active terminal sessions open
- **AND** the user changes the terminal method setting
- **THEN** existing terminal sessions SHALL continue using their original method
- **AND** only new terminal sessions SHALL use the updated method
