# fix-list-command-display

## Problem

The `list` command in command mode does not display anything when active connections exist. The command handler at `command_mode.py:720-727` checks for connections but then just returns `True` without calling any display functions:

```python
def cmd_list(self, args: list[str]) -> bool:
    """Handle list command for showing connections"""
    if not self.ssh_manager.connections:
        display_info("No active connections")
        return True

    # Connections are already shown by show_status() before each prompt
    return True
```

The comment "Connections are already shown by show_status() before each prompt" is misleading - `show_status()` is called in the main loop, but users expect `list` to explicitly display status on demand.

## Expected Behavior

According to the help text at `command_mode.py:1088`:
> `list` - Show all connections and tunnels

The `list` command should display:
1. Saved configurations (if any exist)
2. Active SSH connections table
3. Tunnels for each connection (if any exist)

This is exactly what `show_status()` already does.

## Solution

Call `self.show_status()` in `cmd_list()` when connections exist. The `show_status()` method at line 402-417 already implements the correct display logic:

1. Displays saved configurations via `display_saved_configs()`
2. Displays SSH connections via `display_ssh_status()`
3. Displays tunnels via `display_tunnels()` for each connection

## Scope

- **Single file change**: `src/lazyssh/command_mode.py`
- **Single line change**: Replace `return True` with `self.show_status(); return True`
- **No new dependencies**
- **No API changes**
- **Existing tests should pass** (behavior becomes correct per documentation)

## Risk Assessment

**Low risk** - This is a simple bug fix that makes the command behave as documented.
