## ADDED Requirements

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

## MODIFIED Requirements

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
