## Why

Tests were hanging in CI/CD due to unmocked blocking operations (subprocess calls, interactive prompts) that work locally but fail in headless CI environments. Three tests were identified and fixed:
- `test_scp_with_connection` - unmocked SSH subprocess in SCPMode.connect()
- `test_wizard_lazyssh_existing_connection` - unmocked create_connection() with Confirm.ask()
- `test_plugin_run_executes` - unmocked execute_plugin() with subprocess.Popen

This proposal formalizes test isolation requirements to prevent similar issues in the future.

## What Changes

- Add test isolation requirements to the build-system spec
- Add pytest-timeout as a dependency for CI safety
- Document mocking requirements for blocking operations
- Add CI environment configuration guidance

## Impact

- Affected specs: `build-system`
- Affected code: `pyproject.toml` (already updated with pytest-timeout)
- Affected docs: `CONTRIBUTING.md`, `openspec/project.md`
