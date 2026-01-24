# Contributing to LazySSH

## Development Setup

```bash
git clone https://github.com/Bochner/lazyssh.git && cd lazyssh
pipx install hatch    # Install Hatch (one-time)
make install          # Setup environment
make run              # Run lazyssh
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Setup Hatch environment |
| `make run` | Run lazyssh |
| `make fmt` | Format code with Ruff |
| `make fix` | Auto-fix issues + format |
| `make lint` | Run linter |
| `make test` | Run tests with coverage |
| `make check` | All quality checks |
| `make build` | Build package |

Use `hatch run <command>` to run any command in the venv without activation.

## Code Style

- **Ruff** for formatting and linting (100 char lines)
- **mypy** for type checking
- Python 3.11+

Auto-fix most issues: `make fix`

## Testing

Tests run with coverage by default:

```bash
make test    # Shows coverage in terminal
```

## Pull Request Process

1. Fork and create a feature branch
2. Make changes following the code style
3. Run `make check` (must pass)
4. Submit PR

## Version Management

Single source of truth: `src/lazyssh/__init__.py`

```bash
hatch version          # Show version
hatch version 1.2.3    # Set version
hatch version patch    # Bump patch
```

## Project Structure

```
src/lazyssh/           # Source code
tests/                 # Tests
pyproject.toml         # Config (Hatch, Ruff, pytest, mypy)
.mise.toml             # Tool versions (Python, Ruff)
Makefile               # Dev commands
```
