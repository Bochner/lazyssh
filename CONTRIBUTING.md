# Contributing to LazySSH

Thank you for your interest in contributing to LazySSH! This document provides guidelines and information to help you contribute effectively.

## Version Management

LazySSH follows semantic versioning (MAJOR.MINOR.PATCH).

### Version Information

Version information is maintained in **only two places**:

1. `pyproject.toml` - The main version of the package
2. `src/lazyssh/__init__.py` - The `__version__` variable

**Important**: Do not add version information anywhere else in the codebase. This helps avoid confusion and ensures consistency.

### Updating Versions

When preparing a release:

1. Use the `scripts/release.py` script to update versions
2. Example: `python scripts/release.py 1.1.2`

This script will:
- Update version in `pyproject.toml`
- Update `__version__` in `src/lazyssh/__init__.py`
- Create a git tag

## Development Setup

1. Clone the repository
2. Install development dependencies:
   ```
   pip install -e ".[dev]"
   ```
3. Set up pre-commit hooks:
   ```
   pre-commit install
   ```

## Testing

Run tests with pytest:

```
pytest
```

## Code Style

This project follows:
- Black for code formatting
- isort for import sorting
- mypy for type checking

You can run all style checks with:

```
./pre-commit-check.sh
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes following the coding standards
4. Run all tests and linting
5. Submit a pull request

Thank you for contributing to LazySSH! 