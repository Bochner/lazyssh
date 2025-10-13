# LazySSH Development Guide

> **Note**: This guide is for contributors and developers. If you're looking to use LazySSH, see the [User Guide](user-guide.md) instead.

This guide provides information for developers who want to contribute to LazySSH or understand its internal workings.

## Table of Contents

- [Setting Up a Development Environment](#setting-up-a-development-environment)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Building and Packaging](#building-and-packaging)
- [Contributing Guidelines](#contributing-guidelines)

## Setting Up a Development Environment

### Prerequisites

- Python 3.11 or higher
- Git
- Pip
- OpenSSH client
- Terminator terminal emulator (optional but recommended)
- **Platform**: Linux or macOS (Windows users should use WSL)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install in development mode with all development dependencies
make dev-install

# Or manually:
pip install -e ".[dev]"
pip install pyupgrade typing_extensions bandit safety pytest-watch

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

## Project Structure

```
lazyssh/
├── src/                    # Source code
│   └── lazyssh/            # Main package
│       ├── __init__.py     # Package initialization
│       ├── __main__.py     # Entry point for the application
│       ├── ssh.py          # SSH connection management
│       ├── command_mode.py # Command mode interface
│       ├── models.py       # Data models
│       ├── ui.py           # User interface utilities
│       ├── config.py       # Configuration handling
│       └── scp_mode.py     # SCP mode for file transfers
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── .github/                # GitHub workflows and templates
├── pyproject.toml          # Project configuration and packaging
├── requirements.txt        # Dependencies
├── Makefile                # Development tasks
├── pre-commit-check.sh     # Script to run all CI checks locally
├── .pre-commit-config.yaml # Code quality hooks
├── .flake8                 # Flake8 configuration
├── .gitignore              # Git ignore file
├── LICENSE                 # License file
└── README.md               # Project overview
```

## Core Components

### `__main__.py`

- Entry point for the application
- Parses command-line arguments
- Handles top-level menu interface
- Manages main application flow

### `ssh.py`

- `SSHManager` class for managing SSH connections
- Functions for creating and monitoring SSH connections
- Tunnel creation and management
- Terminal session handling

### `command_mode.py`

- `CommandMode` class for handling the command-line interface
- Command parsing and execution
- Tab completion via `LazySSHCompleter`
- Status display

### `scp_mode.py`

- `SCPMode` class for file transfer functionality
- File upload/download commands
- Directory navigation
- Batch file operations

### `models.py`

- Data classes for SSH connections and tunnels
- Connection state management
- Path resolution and directory handling

### `ui.py`

- User interface utilities
- Display formatting functions
- Status table rendering
- Banner and message display

## Development Workflow

### Quick Reference: Makefile Commands

The refactored Makefile provides comprehensive development commands. For full details, run `make help`.

**Common Workflow Commands:**
```bash
make dev-install    # First-time setup with all dev dependencies
make fix            # Auto-fix formatting and code style issues
make check          # Run all quality checks (format, lint, types)
make verify         # PyPI-ready verification: quality + security + tests + build
make test           # Run tests
make coverage       # Run tests with coverage report
make all            # Run all checks and tests
```

**Build & Release Commands:**
```bash
make version        # Display current version
make build          # Build the package
make release        # Interactive release process
make publish-test   # Publish to TestPyPI
make publish        # Publish to PyPI
```

**Utility Commands:**
```bash
make clean          # Clean build artifacts
make deps-check     # Check for outdated dependencies
make security       # Run security scans
make docs           # Verify documentation
```

### Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style guidelines

3. Auto-fix common issues and run quality checks:
   ```bash
   # Quick fix and check
   make fix && make check

   # Or comprehensive verification (recommended before commit)
   make verify

   # Or use the pre-commit script
   ./pre-commit-check.sh
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "feat: add new capability for X"
   ```

5. Push your branch and create a pull request:
   ```bash
   git push -u origin feature/your-feature-name
   ```

### Adding a New Command

1. Add your command function to the appropriate class in `command_mode.py` or `scp_mode.py`:
   ```python
   def cmd_mycommand(self, args: List[str]) -> bool:
       """Handle my new command"""
       # Command implementation
       return True
   ```

2. Add it to the commands dictionary in the class's `__init__` method:
   ```python
   self.commands = {
       # Existing commands...
       "mycommand": self.cmd_mycommand,
   }
   ```

3. Add tab completion support in the respective completer class
4. Update help text and documentation

## Testing

### Running Tests

```bash
# Run all tests (using Make)
make test

# Run with coverage report
make coverage

# Run tests in watch mode (auto-rerun on changes)
make watch

# Or use pytest directly
pytest -xvs tests

# Run specific test file
pytest tests/test_specific.py

# Run with coverage (detailed)
pytest --cov=src/lazyssh --cov-report=html --cov-report=term tests
```

### Writing Tests

- Create test files in the `tests/` directory with the `test_*.py` naming convention
- Use pytest fixtures for common setup
- Mock external dependencies like SSH connections and system commands
- Test both success and failure cases
- Aim for high test coverage of critical functionality
- Include edge cases and error handling scenarios

## Code Style

LazySSH follows these style guidelines:

- **Python 3.11+** - Utilizing modern Python features
- [Black](https://black.readthedocs.io/) for code formatting (line length: 100)
- [isort](https://pycqa.github.io/isort/) for import sorting (Black-compatible profile)
- [flake8](https://flake8.pycqa.org/) for linting (max complexity: 10)
- [mypy](https://mypy.readthedocs.io/) for type checking (strict mode)
- [pyupgrade](https://github.com/asottile/pyupgrade) for Python 3.11+ syntax
- **pathlib** preferred over `os.path` for path operations

### Code Style Enforcement

The refactored Makefile and pre-commit script provide multiple ways to check and fix code style:

```bash
# Auto-fix formatting issues (recommended first step)
make fix              # Runs: pyupgrade → isort → black

# View formatting changes without applying them
make fmt              # Runs: isort → black (shows changes)

# Check code quality without fixes
make check            # Runs: format check → lint → type check (uses your Python env)

# Run comprehensive PyPI-ready verification (recommended before commit/push)
make verify           # Runs pre-commit-check.sh: quality + security + tests + build + cleanup

# Run pre-commit script with auto-fix (default)
./pre-commit-check.sh

# Run pre-commit script in check-only mode
./pre-commit-check.sh --no-fix

# Run pre-commit script in dry-run mode (see what would be fixed)
./pre-commit-check.sh --dry-run

# Skip tests during pre-commit check
./pre-commit-check.sh --skip-tests

# Skip build verification
./pre-commit-check.sh --skip-build

# Verbose output
./pre-commit-check.sh --verbose
```

#### Understanding `make verify` (PyPI-Ready Verification)

The `make verify` command provides the highest level of confidence that your code is ready for deployment to PyPI. It runs the comprehensive `pre-commit-check.sh` script which:

1. **Creates a temporary isolated virtual environment** (`.pre-commit-venv/`)
2. **Installs the package fresh** with all dependencies
3. **Runs all code quality checks** (check-only mode, no auto-fix):
   - Python 3.11+ code optimizations check (pyupgrade)
   - Format check (Black)
   - Import order check (isort)
   - Linting (flake8 - critical errors + full check)
   - Type checking (mypy with strict settings)
   - Pathlib usage check
4. **Runs security analysis**:
   - Bandit security scanner
   - Safety dependency vulnerability checker
5. **Runs all tests** with pytest
6. **Builds the package** with `python -m build`
7. **Verifies the package** with `twine check` (PyPI readiness)
8. **Checks version consistency** across files
9. **Cleans up** everything automatically (venv, build artifacts, cache files)

**Why use `make verify` over `make check`?**
- `make check` runs quick checks in your current environment (fast iteration)
- `make verify` creates a fresh isolated environment, runs tests, builds, and verifies for PyPI
- `make verify` ensures your package is truly ready for production deployment
- Perfect before committing, pushing, or creating a release

**When to use each:**
- Daily development: `make fix && make check` (fast iteration, ~10s)
- Before commit: `make verify` (comprehensive, PyPI-ready, ~60s)
- Before push/release: `make verify` (ensures deployment readiness)

### Pre-Commit Check Script Features

The enhanced `pre-commit-check.sh` script provides:

1. **Auto-Fix Mode (Default)**: Automatically fixes formatting issues
2. **Check-Only Mode**: Reports issues without making changes
3. **Dry-Run Mode**: Shows what would be fixed
4. **Comprehensive Checks**: Runs all CI/CD checks locally
5. **Security Scanning**: Includes Bandit and Safety checks
6. **Detailed Reporting**: Color-coded output with fix/error/warning counts
7. **Smart Cleanup**: Automatically cleans up temporary files

**Example Output:**
```bash
$ ./pre-commit-check.sh
🚀 LazySSH Pre-Commit Checks
=================================
Mode: Auto-fix (will attempt to fix issues)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Auto-Fix Phase
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Running pyupgrade for Python 3.11+ optimizations...
✓ Code already optimized for Python 3.11+
→ Auto-formatting imports with isort...
🔧 Fixed: import ordering
→ Auto-formatting code with Black...
🔧 Fixed: reformatted code with Black

✓ Applied 2 automatic fixes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Code Quality Checks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Black formatting check passed
✓ isort check passed
✓ No critical flake8 errors found
✓ flake8 full check passed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Fixes Applied: 2
✓✓✓ All Checks Passed! ✓✓✓
Repository is clean and ready for commit
```

## Building and Packaging

### Building the Package

```bash
# Using Make (recommended)
make build           # Cleans, builds, and verifies

# Or manually
python -m build      # Build both sdist and wheel
python -m build --wheel   # Build only wheel
python -m build --sdist   # Build only sdist
```

### Testing the Package

```bash
# Verify the package
make build           # Includes verification
twine check dist/*   # Manual verification

# Install the built package locally
pip install --force-reinstall dist/*.whl

# Test in a clean environment
python3 -m venv test_env
source test_env/bin/activate
pip install dist/*.whl
lazyssh --help
deactivate
rm -rf test_env
```

### Publishing Workflow

```bash
# 1. Check current version
make version

# 2. Update version (interactive)
make release         # Updates pyproject.toml and __init__.py

# 3. Review and commit changes
git diff
git commit -am "chore: bump version to X.Y.Z"

# 4. Tag the release
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# 5. Test publish to TestPyPI
make publish-test

# 6. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ lazyssh

# 7. Publish to PyPI (production)
make publish         # Requires confirmation

# 8. Push to GitHub
git push && git push --tags
```

## Contributing Guidelines

### Pull Request Process

1. **Fork and Clone**: Fork the repository and clone your fork
2. **Create a Branch**: Create a feature branch from `main`
3. **Make Changes**: Implement your feature or fix
4. **Auto-Fix Issues**: Run `make fix` to auto-fix formatting issues
5. **Run Checks**: Run `make verify` to ensure all checks pass
6. **Run Tests**: Ensure all tests pass with `make test` or `make coverage`
7. **Update Documentation**: Update relevant docs for new features
8. **Commit**: Use conventional commit format (see below)
9. **Push and PR**: Push to your fork and create a pull request

**Quick Pre-Commit Checklist:**
```bash
make fix      # Auto-fix formatting
make verify   # Run all checks
make coverage # Test with coverage
```

### Required Checks Before PR

All pull requests must pass:
- ✅ Black formatting (auto-fixed by `make fix`)
- ✅ isort import sorting (auto-fixed by `make fix`)
- ✅ flake8 linting
- ✅ mypy type checking
- ✅ All tests passing
- ✅ Package builds successfully
- ✅ No security issues (Bandit scan)
- ✅ Documentation updated (if applicable)

### Commit Message Format

Use conventional commits format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for test-related changes
- `chore:` for changes to the build process or auxiliary tools

### Code Review

Pull requests will be reviewed for:

- Functionality and correctness
- Code style and quality
- Test coverage
- Documentation completeness
- Compatibility with existing code

### Versioning

LazySSH follows [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for new functionality in a backward-compatible manner
- PATCH version for backward-compatible bug fixes

## Makefile Command Reference

The refactored Makefile provides a comprehensive set of commands for development, testing, and release management.

### Setup Commands

| Command | Description |
|---------|-------------|
| `make install` | Install package in development mode |
| `make dev-install` | Install with all development dependencies (recommended) |
| `make deps-check` | Check for outdated dependencies |
| `make deps-update` | Update dependencies to latest versions (interactive) |

### Code Quality Commands

| Command | Description |
|---------|-------------|
| `make fmt` | Format code with Black and isort (shows changes) |
| `make fix` | Auto-fix code issues (pyupgrade + isort + black) |
| `make lint` | Run all linting checks (flake8 + pylint) |
| `make typecheck` | Run mypy type checking |
| `make check` | Run all quality checks (format + lint + type + pathlib) |
| `make verify` | **Full PyPI-ready verification** - quality checks + tests + security + build verification |
| `make pre-commit` | Alias for `verify` |

### Testing Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests with pytest |
| `make coverage` | Run tests with coverage report (HTML + terminal + XML) |
| `make watch` | Run tests in watch mode (auto-rerun on changes) |

### Security Commands

| Command | Description |
|---------|-------------|
| `make security` | Run security checks (Bandit + Safety) |

### Build & Release Commands

| Command | Description |
|---------|-------------|
| `make build` | Clean and build the package |
| `make dist` | Build distribution packages (alias for `build`) |
| `make clean` | Clean up build artifacts and cache files |
| `make version` | Display current version from pyproject.toml and __init__.py |
| `make release` | Interactive version bump process |
| `make publish-test` | Publish to TestPyPI (runs verify + build first) |
| `make publish` | Publish to PyPI (requires confirmation) |

### Documentation Commands

| Command | Description |
|---------|-------------|
| `make docs` | Verify documentation files exist |

### Composite Commands

| Command | Description |
|---------|-------------|
| `make all` | Run all checks and tests (verify + coverage) |
| `make help` | Display help with all available commands |

### Command Dependencies

Understanding command dependencies helps optimize your workflow:

```
make all
├── make verify
│   └── ./pre-commit-check.sh --no-fix
│       ├── Code quality checks
│       │   ├── pyupgrade (Python 3.11+)
│       │   ├── Black check
│       │   ├── isort check
│       │   ├── flake8 (critical + full)
│       │   └── mypy type checking
│       ├── Security analysis
│       │   ├── Bandit security scanner
│       │   └── Safety vulnerability check
│       ├── Testing (pytest)
│       ├── Build verification
│       │   ├── python -m build
│       │   └── twine check
│       └── Cleanup (venv, build, cache)
└── make coverage (pytest with coverage)

make fix
├── pyupgrade (Python 3.11+ optimization)
├── isort (import sorting)
└── black (code formatting)

make publish
├── make verify
├── make build
│   ├── make clean
│   └── python -m build
├── twine check
└── twine upload
```

### Tips and Best Practices

1. **Quick Development Cycle**: Use `make fix && make check` for rapid iteration
2. **Before Committing**: Always run `make verify` for PyPI-ready verification (includes tests + build)
3. **Before Pushing**: Run `make verify` to ensure deployment readiness and package quality
4. **Before Releasing**: Run `make publish-test` first to test on TestPyPI
5. **Clean Build**: `make verify` automatically cleans up; use `make clean` for manual cleanup
6. **Dependency Updates**: Run `make deps-check` periodically

### Common Workflows

**Daily Development:**
```bash
# Make changes to code
make fix          # Auto-fix formatting
make check        # Quick quality check
make test         # Run tests
```

**Before Commit:**
```bash
make verify       # Comprehensive check + tests
# or
./pre-commit-check.sh
```

**Before Release:**
```bash
make version      # Check current version
make all          # Full verification
make release      # Update version
git commit -am "chore: bump version to X.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
make publish-test # Test on TestPyPI
make publish      # Publish to PyPI
git push && git push --tags
```
