# Proposal: Add Config Backup Command and Always-Visible Config Display

## Why

Users need a way to backup their connection configurations before making changes, preventing accidental data loss. Additionally, loaded configurations should be visible at all times (like active SSH connections) to provide better awareness of available saved connections.

## What Changes

- Add a `backup-config` command that creates a backup of the current connections.conf file
- Modify the status display to always show loaded configurations table (when configs exist)
- Display loaded configs on startup and after every command execution (matching active connections behavior)

## Impact

- Affected specs: `connection-config`
- Affected code:
  - `src/lazyssh/config.py` - Add backup functionality
  - `src/lazyssh/command_mode.py` - Add backup-config command, modify show_status() to include configs
  - `src/lazyssh/ui.py` - May need adjustment if display logic changes
