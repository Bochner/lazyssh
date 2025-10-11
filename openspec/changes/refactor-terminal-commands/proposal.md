# Refactor Terminal Commands

## Why

The current `terminal` command has dual functionality - it both opens terminals for connections AND changes the terminal method configuration. This creates confusion for users and violates the single responsibility principle. Additionally, there's an asymmetry between having a `close` command but no matching `open` command.

## What Changes

- **BREAKING**: Split the `terminal` command into two distinct commands:
  - `terminal <method>` - Only for switching terminal methods (auto, native, terminator)
  - `open <ssh_id>` - For opening terminal sessions (matching the existing `close` command)
- Update command help text and usage messages to reflect the new structure
- Update tab completion to support both commands appropriately
- Ensure terminal method display continues to work in the status table
- Fix any issues with terminal method display if found during implementation

## Impact

- Affected specs: `terminal-integration`
- Affected code:
  - `src/lazyssh/command_mode.py` - Command handler refactoring
  - `src/lazyssh/__main__.py` - Menu mode command handling (if applicable)
  - Documentation files (user guides, command reference)
- Breaking change: Users using `terminal <ssh_id>` will need to switch to `open <ssh_id>`
- Migration path: Clear error messages guiding users to use `open` command instead

