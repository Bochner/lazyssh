# scp-mode Delta Spec

## ADDED Requirements

### Requirement: Directory Listing Cache

The system SHALL cache directory listing results from remote SSH commands to minimize redundant command execution, with automatic expiration and invalidation.

#### Scenario: Cache hit on repeated completion

- **WHEN** a user requests tab completion for a directory that was queried within the cache TTL (30 seconds)
- **THEN** the system SHALL return cached results without executing a new SSH command
- **AND** the system SHALL log cache hit in debug mode

#### Scenario: Cache miss on expired entry

- **WHEN** a user requests tab completion for a directory whose cache entry is older than TTL
- **THEN** the system SHALL execute a new SSH command to fetch fresh results
- **AND** the system SHALL update the cache with the new results
- **AND** the system SHALL log cache miss in debug mode

#### Scenario: Cache invalidation on directory change

- **WHEN** a user changes directories using the `cd` command
- **THEN** the system SHALL clear all cached directory listings
- **AND** subsequent completions SHALL fetch fresh data

#### Scenario: Cache invalidation on file upload

- **WHEN** a user uploads a file using `put` or `mput`
- **THEN** the system SHALL invalidate the cache entry for the target directory
- **AND** subsequent completions for that directory SHALL fetch fresh data

### Requirement: Completion Query Throttling

The system SHALL limit the frequency of SSH command execution during automatic tab completion to reduce unnecessary network traffic during rapid typing.

#### Scenario: Throttle automatic completion during rapid typing

- **WHEN** a user types continuously and triggers automatic completion
- **AND** less than 300ms have elapsed since the last completion query
- **THEN** the system SHALL skip executing a new SSH command
- **AND** the system SHALL return cached results if available or empty results otherwise

#### Scenario: Immediate completion on explicit tab press

- **WHEN** a user explicitly presses the Tab key
- **THEN** the system SHALL execute the completion query immediately without throttling
- **AND** the system SHALL update the cache with results

#### Scenario: No throttle on first completion request

- **WHEN** a user requests the first completion in a session or after a pause
- **THEN** the system SHALL execute the SSH command immediately without delay

### Requirement: Runtime Debug Mode Toggle

The system SHALL provide a command to toggle debug mode on and off during an active SCP session without requiring restart.

#### Scenario: Enable debug mode

- **WHEN** a user enters the `debug` command while debug mode is OFF
- **THEN** the system SHALL enable debug logging
- **AND** the system SHALL display "Debug mode: ON"
- **AND** subsequent operations SHALL show detailed debug information

#### Scenario: Disable debug mode

- **WHEN** a user enters the `debug` command while debug mode is ON
- **THEN** the system SHALL disable debug logging
- **AND** the system SHALL display "Debug mode: OFF"
- **AND** subsequent operations SHALL suppress debug information

#### Scenario: Debug command in help

- **WHEN** a user enters the `help` command
- **THEN** the system SHALL display the `debug` command in the available commands list
- **AND** the help text SHALL indicate it toggles debug mode

### Requirement: Optimized Command Execution

The system SHALL minimize the number of SSH commands executed during normal SCP operations by reusing cached data and batching queries where possible.

#### Scenario: Reduced command count during completion

- **WHEN** a user performs tab completion multiple times in the same directory within the cache TTL
- **THEN** the system SHALL execute at most one SSH command for the initial query
- **AND** subsequent completions SHALL use cached data
- **AND** the total SSH command count SHALL be reduced by at least 80% compared to uncached behavior

#### Scenario: Debug logging shows cache efficiency

- **WHEN** debug mode is enabled
- **AND** a user performs operations that benefit from caching
- **THEN** the system SHALL log cache hit and miss events
- **AND** the logs SHALL include timestamps and cache entry information
