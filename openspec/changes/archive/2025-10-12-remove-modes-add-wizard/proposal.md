## Why

The current dual-mode system (prompt mode and command mode) has become obsolete over time, with prompt mode being rarely used. The mode-switching concept adds unnecessary complexity to the user experience. Users would benefit from a unified interface with guided workflows for complex operations.

## What Changes

- **BREAKING**: Remove the concept of "modes" entirely from LazySSH
- **BREAKING**: Remove the `--prompt` command-line flag
- **BREAKING**: Remove the `mode` command and mode-switching functionality
- **BREAKING**: Remove prompt mode (menu-driven interface) completely
- **ADDED**: Add a new `wizard` command that provides guided, interactive workflows
- **ADDED**: Support `wizard lazyssh` for guided SSH connection creation
- **ADDED**: Support `wizard tunnel` for guided tunnel creation
- **MODIFIED**: Default to command mode interface (no mode selection needed)
- **MODIFIED**: Remove mode-related UI elements and messaging

## Impact

- Affected specs: user-interface (new capability)
- Affected code:
  - `src/lazyssh/__main__.py` - Remove mode switching logic and --prompt flag
  - `src/lazyssh/command_mode.py` - Remove mode command and mode-related UI
  - `src/lazyssh/ui.py` - Remove prompt mode menu functions
  - All mode-related documentation and help text
