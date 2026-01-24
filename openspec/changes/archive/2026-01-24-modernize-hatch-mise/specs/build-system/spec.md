## ADDED Requirements

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

### Requirement: Hatch Environment Management

The project SHALL define separate Hatch environments for different development workflows.

#### Scenario: Default environment
- **WHEN** developer runs `hatch shell` or `hatch run <command>`
- **THEN** the default environment is activated with runtime dependencies

#### Scenario: Dev environment
- **WHEN** developer runs `hatch run dev:<command>`
- **THEN** the dev environment is used with all development dependencies

#### Scenario: Test environment
- **WHEN** developer runs `hatch run test:pytest`
- **THEN** tests are executed in isolated test environment with pytest and pytest-cov

#### Scenario: Lint environment
- **WHEN** developer runs `hatch run lint:all`
- **THEN** all linting tools (black, isort, flake8, pylint) are executed

#### Scenario: Typing environment
- **WHEN** developer runs `hatch run typing:check`
- **THEN** mypy type checking is executed with project configuration

### Requirement: Hatch Version Management

The project SHALL use Hatch's version source configuration to manage package version.

#### Scenario: Version from source
- **WHEN** Hatch reads the project version
- **THEN** version is sourced from `src/lazyssh/__init__.py` `__version__` variable

#### Scenario: Version bump
- **WHEN** developer runs `hatch version <new-version>`
- **THEN** the version in `src/lazyssh/__init__.py` is updated
- **AND** `pyproject.toml` dynamic version reflects the change

### Requirement: mise Tool Version Management

The project SHALL provide mise configuration for reproducible Python version management.

#### Scenario: Python version pinning
- **WHEN** `.mise.toml` exists in project root
- **THEN** it specifies Python 3.11 as the required version

#### Scenario: Automatic version activation
- **WHEN** developer with mise installed enters project directory
- **THEN** the correct Python version is automatically activated

#### Scenario: CI reproducibility
- **WHEN** GitHub Actions uses mise
- **THEN** the same Python version is used as local development

### Requirement: Makefile Compatibility Layer

The project SHALL maintain Makefile targets that delegate to Hatch commands for backward compatibility.

#### Scenario: Make test
- **WHEN** developer runs `make test`
- **THEN** tests are executed via `hatch run test:pytest`

#### Scenario: Make lint
- **WHEN** developer runs `make lint`
- **THEN** linting is executed via `hatch run lint:all`

#### Scenario: Make build
- **WHEN** developer runs `make build`
- **THEN** package is built via `hatch build`

#### Scenario: Make clean
- **WHEN** developer runs `make clean`
- **THEN** all build artifacts and Hatch environments are removed
