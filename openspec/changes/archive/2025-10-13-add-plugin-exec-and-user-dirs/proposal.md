## Why
Users reported that after installing `lazyssh` via `pipx`, the built-in `enumerate` plugin was discovered but marked invalid because it was not executable. Additionally, there is no first-class mechanism for users to place and load their own custom plugins outside the installed package path.

## What Changes
- Ensure packaged/built-in plugins are installed with the executable bit so they are usable immediately upon install.
- Add support for user plugin directories with documented precedence: package `plugins/`, then user-level directories.
- Provide configuration via environment variable `LAZYSSH_PLUGIN_DIRS` (colon-separated list) and default to `~/.lazyssh/plugins` when not set.
- Update docs and CLI help to explain how to author and place custom plugins.

## Impact
- Affected specs: `plugin-system`
- Affected code: `src/lazyssh/plugin_manager.py`, packaging metadata in `pyproject.toml`, documentation under `docs/Plugin/*`, potential tests under `tests/` for discovery and exec-bit guarantees.
