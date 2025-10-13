# Change Proposal: Persistent Terminal Sessions

## Why

Currently, native Python terminal mode uses `os.execvp()` to replace the LazySSH process with the SSH command, which prevents users from returning to LazySSH after opening a terminal session. This creates an inconsistent user experience where:
- Users cannot easily switch between multiple SSH connections
- The LazySSH interface is lost after opening a native terminal
- There's no way to change terminal method preferences while LazySSH is running
- Users cannot see which terminal method is being used for each connection

Users need the ability to enter and exit SSH sessions at will while keeping LazySSH running, similar to how a traditional SSH connection manager would work.

## What Changes

- **Modify native terminal implementation** to use subprocess instead of `os.execvp()`, allowing LazySSH to remain running
- **Add terminal method display** to the SSH connections status table showing whether each connection uses native or terminator mode
- **Add command to change terminal method** from within LazySSH without restarting
- **Store terminal method preference** per user session (not per connection, but globally configurable at runtime)
- **Maintain backward compatibility** with existing Terminator behavior

## Impact

- **Affected specs:** `terminal-integration`
- **Affected code:**
  - `src/lazyssh/ssh.py` - Modify `open_terminal_native()` to use subprocess instead of execvp
  - `src/lazyssh/ui.py` - Add terminal method column to SSH status display
  - `src/lazyssh/command_mode.py` - Add `terminal` or `set-terminal` command
  - `src/lazyssh/config.py` - Add runtime terminal method configuration
  - `src/lazyssh/__main__.py` - Add menu option to change terminal method
