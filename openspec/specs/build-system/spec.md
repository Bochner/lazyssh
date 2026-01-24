# Build System Specification

## Purpose

This spec defines the build tooling, development environment, and quality checks for LazySSH.
## Requirements
### Requirement: Hatch Build System

The project SHALL use Hatch (hatchling) as the build backend for Python package management.

#### Scenario: Package build with Hatch
- **WHEN** developer runs `hatch build`
- **THEN** the system produces both wheel and sdist distributions in `dist/`
- **AND** the wheel contains all source files from `src/lazyssh/`
- **AND** the wheel includes the `plugins/` directory with executable plugins

#### Scenario: Editable install with Hatch
- **WHEN** developer runs `hatch env create` or `pip install -e .`
- **THEN** the package is installed in editable mode
- **AND** code changes are immediately reflected without reinstall

### Requirement: Single Hatch Environment

The project SHALL use a single default Hatch environment for all development workflows.

#### Scenario: Default environment
- **WHEN** developer runs `hatch run <command>`
- **THEN** the command executes in the default environment with all development dependencies
- **AND** the environment includes: ruff, mypy, pytest, pytest-cov, build, twine
- **AND** the developer returns to their normal shell when the command completes

#### Scenario: Run the application
- **WHEN** developer runs `make run` or `hatch run lazyssh`
- **THEN** the lazyssh application starts in the Hatch environment
- **AND** no manual venv activation is required

#### Scenario: Available scripts
- **WHEN** developer runs `hatch run <script>`
- **THEN** the following scripts are available: fmt, lint, fix, test, check, build, verify-pkg

### Requirement: Hatch Version Management

The project SHALL use Hatch's version source configuration to manage package version.

#### Scenario: Version from source
- **WHEN** Hatch reads the project version
- **THEN** version is sourced from `src/lazyssh/__init__.py` `__version__` variable

#### Scenario: Version bump
- **WHEN** developer runs `hatch version <new-version>`
- **THEN** the version in `src/lazyssh/__init__.py` is updated
- **AND** `pyproject.toml` dynamic version reflects the change

### Requirement: Ruff Code Quality

The project SHALL use Ruff as the single tool for linting and formatting.

#### Scenario: Format code
- **WHEN** developer runs `hatch run fmt` or `make fmt`
- **THEN** all Python files in `src/` and `tests/` are formatted with Ruff
- **AND** formatting follows 100 character line length
- **AND** double quotes are used for strings

#### Scenario: Lint code
- **WHEN** developer runs `hatch run lint` or `make lint`
- **THEN** Ruff checks code against enabled rule sets: E, F, I, UP, B, C4, SIM
- **AND** issues are reported with file locations and descriptions

#### Scenario: Auto-fix issues
- **WHEN** developer runs `hatch run fix` or `make fix`
- **THEN** Ruff auto-fixes applicable issues
- **AND** code is formatted after fixes are applied

### Requirement: Test Coverage Display

The project SHALL display test coverage by default when running tests.

#### Scenario: Run tests with coverage
- **WHEN** developer runs `hatch run test` or `make test`
- **THEN** pytest executes all tests in `tests/`
- **AND** coverage report is displayed in terminal with missing lines
- **AND** files with 100% coverage are skipped in report

#### Scenario: Run hatch test with coverage
- **WHEN** developer runs `hatch test`
- **THEN** pytest executes all tests in `tests/`
- **AND** coverage report is displayed in terminal with missing lines
- **AND** coverage HTML report is generated at `artifacts/coverage/`
- **AND** pytest HTML report is generated at `artifacts/unit/`

### Requirement: Quality Check Gate

The project SHALL provide a single command to run all quality checks.

#### Scenario: Run all checks
- **WHEN** developer runs `hatch run check` or `make check`
- **THEN** Ruff format check runs (fails if formatting needed)
- **AND** Ruff lint check runs
- **AND** mypy type checking runs
- **AND** version import verification runs

### Requirement: mise Tool Version Management

The project SHALL provide mise configuration for reproducible tool version management.

#### Scenario: Tool version pinning
- **WHEN** `.mise.toml` exists in project root
- **THEN** it specifies Python 3.11 as the required version
- **AND** it specifies Ruff version for consistent linting

#### Scenario: Automatic version activation
- **WHEN** developer with mise installed enters project directory
- **THEN** the correct Python and Ruff versions are automatically activated

#### Scenario: CI reproducibility
- **WHEN** GitHub Actions uses mise
- **THEN** the same tool versions are used as local development

### Requirement: Makefile Compatibility Layer

The project SHALL maintain Makefile targets that delegate to Hatch commands for backward compatibility.

#### Scenario: Make test
- **WHEN** developer runs `make test`
- **THEN** tests are executed via `hatch run test`

#### Scenario: Make lint
- **WHEN** developer runs `make lint`
- **THEN** linting is executed via `hatch run lint`

#### Scenario: Make check
- **WHEN** developer runs `make check`
- **THEN** all quality checks are executed via `hatch run check`

#### Scenario: Make build
- **WHEN** developer runs `make build`
- **THEN** package is built via `hatch build`
- **AND** package is verified with `hatch run verify-pkg`

#### Scenario: Make clean
- **WHEN** developer runs `make clean`
- **THEN** all build artifacts are removed
- **AND** Hatch environments are removed

#### Scenario: Make version
- **WHEN** developer runs `make version`
- **THEN** current version is displayed via `hatch version`

### Requirement: Hatch Test Command

The project SHALL configure `hatch test` to run pytest with coverage and HTML reports.

#### Scenario: Run hatch test
- **WHEN** developer runs `hatch test`
- **THEN** pytest executes all tests in `tests/`
- **AND** coverage report is displayed in terminal with missing lines
- **AND** coverage HTML report is generated at `artifacts/coverage/index.html`
- **AND** pytest HTML report is generated at `artifacts/unit/report.html`

#### Scenario: Hatch test with specific Python version
- **WHEN** developer runs `hatch test -py 3.11`
- **THEN** tests run against Python 3.11 specifically
- **AND** all reports are generated as normal

### Requirement: pytest-html Integration

The project SHALL include pytest-html for generating HTML test reports.

#### Scenario: HTML test report generation
- **WHEN** tests complete (pass or fail)
- **THEN** `artifacts/unit/report.html` contains all test results
- **AND** the report is self-contained (no external dependencies)
- **AND** the report shows pass/fail status, duration, and error details

### Requirement: Coverage HTML Reports

The project SHALL generate HTML coverage reports alongside CLI output.

#### Scenario: Coverage HTML report generation
- **WHEN** tests complete
- **THEN** `artifacts/coverage/index.html` provides browsable coverage data
- **AND** each source file has a detailed line-by-line coverage view
- **AND** the CLI still displays coverage summary with missing lines

### Requirement: Full Test Coverage

The project SHALL maintain 100% test coverage across all source modules.

#### Scenario: Coverage enforcement
- **WHEN** developer runs `hatch test`
- **THEN** all lines in `src/lazyssh/` are covered by tests
- **AND** untestable lines are explicitly marked with `# pragma: no cover`

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
