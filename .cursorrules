# Cursor Rules for LazySSH

## Code Style
- Line length: 100 characters
- Python 3.11+ with modern type hints (`list[str]` not `List[str]`)
- Ruff for linting and formatting
- mypy for type checking

## Quality Gate
Run `make check` before committing. All quality checks must pass.

## Test Isolation Requirements (CRITICAL)

All tests MUST be isolated from external dependencies for CI/CD compatibility.
Tests that make real subprocess calls or network connections will timeout and fail in CI.

### Always Mock These in Tests

1. **Subprocess operations** - `subprocess.run()`, `subprocess.Popen()`
   ```python
   mock_result = mock.MagicMock()
   mock_result.returncode = 0
   mock_result.stdout = "/home/user"
   monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)
   ```

2. **Interactive prompts** - `Confirm.ask()`, `Prompt.ask()`, `input()`
   ```python
   monkeypatch.setattr("rich.prompt.Confirm.ask", lambda *a, **kw: True)
   ```

3. **Plugin execution** - `execute_plugin()`
   ```python
   monkeypatch.setattr(cm.plugin_manager, "execute_plugin", lambda *a: (True, "", 0.1))
   ```

4. **SCPMode with selected_connection** - MUST mock subprocess.run before instantiation
   ```python
   def test_with_connection(self, ssh_manager: SSHManager, monkeypatch: pytest.MonkeyPatch) -> None:
       mock_result = mock.MagicMock()
       mock_result.returncode = 0
       mock_result.stdout = "/home/user"
       monkeypatch.setattr("subprocess.run", lambda *a, **kw: mock_result)

       mode = SCPMode(ssh_manager, selected_connection="myconn")
   ```

### Timeout Protection
- pytest-timeout enforces 30-second per-test timeout
- Hanging tests indicate missing mocks
- Stack traces identify blocking operations

## Architecture Overview

LazySSH is an SSH automation toolkit with:
- `command_mode.py` - Main prompt_toolkit shell
- `ssh.py` - SSH connection management
- `scp_mode.py` - File transfer interface
- `plugin_manager.py` - Plugin discovery/execution
- `config.py` - TOML persistence

## Cross-References

- See CLAUDE.md for full guidance
- See CONTRIBUTING.md for PR process
- See openspec/project.md for detailed conventions
