## ADDED Requirements

### Requirement: Test Isolation for CI/CD

Tests SHALL be fully isolated from external dependencies to ensure reliable execution in headless CI/CD environments.

#### Scenario: Subprocess operations must be mocked
- **WHEN** a test calls code that invokes `subprocess.run()` or `subprocess.Popen()`
- **THEN** the subprocess call MUST be mocked to prevent actual process execution
- **AND** the mock SHALL return appropriate CompletedProcess or Popen objects

#### Scenario: Interactive prompts must be mocked
- **WHEN** a test calls code that invokes `Confirm.ask()`, `Prompt.ask()`, or `input()`
- **THEN** the prompt call MUST be mocked to prevent blocking on stdin
- **AND** the mock SHALL return predetermined values for the test scenario

#### Scenario: Network operations must be mocked
- **WHEN** a test calls code that creates SSH connections or network sockets
- **THEN** the network operation MUST be mocked to prevent actual network calls
- **AND** tests SHALL NOT depend on network availability

#### Scenario: SCPMode tests with connections
- **WHEN** a test creates an SCPMode instance with active connections
- **THEN** the `subprocess.run()` call in `connect()` MUST be mocked
- **AND** the `SCPMode.run()` interactive loop MUST be mocked if called

#### Scenario: Plugin execution tests
- **WHEN** a test executes plugins via `execute_plugin()` or `cmd_plugin(["run", ...])`
- **THEN** either the plugin execution MUST be mocked
- **OR** the test MUST use small, controlled test plugins that complete quickly

### Requirement: Test Timeout Protection

Tests SHALL have timeout protection to prevent indefinite hangs in CI/CD.

#### Scenario: pytest-timeout dependency
- **WHEN** the test suite is executed
- **THEN** pytest-timeout MUST be installed as a test dependency
- **AND** a default timeout of 30 seconds MUST be configured per test

#### Scenario: Timeout configuration
- **WHEN** pyproject.toml defines pytest configuration
- **THEN** `timeout = 30` MUST be set in `[tool.pytest.ini_options]`
- **AND** `timeout_method = "thread"` MUST be set for cross-platform compatibility

#### Scenario: Timeout failure identification
- **WHEN** a test exceeds the timeout limit
- **THEN** pytest-timeout SHALL terminate the test and report which test hung
- **AND** the stack trace SHALL be captured to identify the blocking operation

### Requirement: CI Environment Configuration

The CI/CD pipeline SHALL configure environment variables for headless test execution.

#### Scenario: Plain text mode in CI
- **WHEN** tests run in GitHub Actions
- **THEN** `LAZYSSH_PLAIN_TEXT=1` SHOULD be set to disable rich animations
- **AND** `LAZYSSH_NO_ANIMATIONS=1` SHOULD be set to prevent spinner hangs

#### Scenario: No TTY available
- **WHEN** tests run in a headless CI environment without TTY
- **THEN** all tests MUST pass without requiring terminal interaction
- **AND** tests SHALL NOT fail due to missing TTY
