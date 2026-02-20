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
| `make verify` | Full verification (check + test + build) |
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

### Test Isolation Requirements

All tests must be isolated from external dependencies for CI/CD compatibility:

**Mock blocking operations:**
- `subprocess.run()` / `subprocess.Popen()` - Mock to prevent actual process execution
- `Confirm.ask()` / `Prompt.ask()` / `input()` - Mock to prevent stdin blocking
- SSH connections and network calls - Mock to prevent network dependencies

**Example patterns:**
```python
# Mock subprocess
mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

# Mock interactive prompts
monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *args, **kwargs: True)

# Mock plugin execution
monkeypatch.setattr(cm.plugin_manager, "execute_plugin", lambda *args: (True, "", 0.1))
```

**Timeout protection:** All tests have a 30-second timeout via pytest-timeout. If a test hangs, the timeout will identify the blocking operation.

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
.mise.toml             # Tool versions (Python, Ruff, pre-commit)
Makefile               # Dev commands
```
