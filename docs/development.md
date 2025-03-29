# LazySSH Development Guide

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

- Python 3.7 or higher
- Git
- Pip
- OpenSSH client
- Terminator terminal emulator

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/Bochner/lazyssh.git
cd lazyssh

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
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

### Making Changes

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style guidelines

3. Run tests and linting to ensure quality:
   ```bash
   ./pre-commit-check.sh
   ```

4. Commit your changes with a descriptive message:
   ```bash
   git commit -m "feature: add new capability for X"
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
# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=src/lazyssh
```

### Writing Tests

- Create test files in the `tests/` directory
- Use pytest fixtures for common setup
- Mock external dependencies like SSH connections
- Test both success and failure cases

## Code Style

LazySSH follows these style guidelines:

- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [flake8](https://flake8.pycqa.org/) for linting
- [mypy](https://mypy.readthedocs.io/) for type checking

### Code Style Enforcement

The pre-commit hooks will automatically check and fix some style issues. You can also run:

```bash
# Format code
make fmt

# Lint code
make lint
```

## Building and Packaging

### Building the Package

```bash
# Build both sdist and wheel
python -m build

# Build only wheel
python -m build --wheel

# Build only sdist
python -m build --sdist
```

### Testing the Package

```bash
# Verify the package
twine check dist/*

# Install the built package
pip install --force-reinstall dist/*.whl
```

## Contributing Guidelines

### Pull Request Process

1. Ensure your code passes all tests and style checks
2. Update documentation if needed
3. Include tests for new functionality
4. Keep pull requests focused on a single change
5. Reference any relevant issues in your PR description

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