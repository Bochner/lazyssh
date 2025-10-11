# Fix SCP Mode Connection When No Arguments Provided

## Why

When users run `scp` without arguments in command mode, they are prompted to select a connection, but after selection, SCP mode immediately exits without connecting. This breaks the expected workflow where users should be able to enter SCP mode and select a connection interactively.

The bug occurs because `self.socket_path` is never set when no connection argument is provided, causing `connect()` to fail silently and return early.

## What Changes

- Fix `SCPMode.run()` to set `socket_path` after interactive connection selection
- Ensure socket path is derived from the selected connection name before calling `connect()`
- Maintain existing behavior when connection name is provided as argument

## Impact

- Affected specs: None (no existing SCP spec, only terminal-integration exists)
- Affected code: `src/lazyssh/scp_mode.py` (SCPMode.run method)
- This is a bug fix restoring intended functionality

