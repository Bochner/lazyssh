# Design Document: Persistent Terminal Sessions

## Context

LazySSH currently supports two terminal methods:
1. **Terminator** - Spawns a new terminal emulator window (subprocess)
2. **Native** - Replaces the LazySSH process with SSH using `os.execvp()`

The native method's use of `os.execvp()` creates a poor user experience because:
- The LazySSH process is replaced and cannot be returned to
- Users lose access to manage other connections
- The only way to return to LazySSH is to restart it

Users want to be able to open terminal sessions, work in them, close them, and return to LazySSH to manage other connections or open new sessions.

## Goals / Non-Goals

### Goals
- Allow native terminal sessions to be opened and closed without exiting LazySSH
- Display which terminal method is active for visibility
- Allow users to change terminal method preference at runtime
- Maintain existing behavior for Terminator mode
- Keep the implementation simple and maintainable

### Non-Goals
- Per-connection terminal method preferences (global setting is sufficient)
- Complex session management (no session history, reconnection, etc.)
- Terminal multiplexing features (tmux/screen integration)
- Automatic reconnection or session persistence across LazySSH restarts

## Decisions

### Decision 1: Use subprocess.run() with interactive mode for native terminals

**Choice:** Replace `os.execvp()` with `subprocess.run()` in interactive mode.

**Rationale:**
- `subprocess.run()` allows the parent LazySSH process to continue running
- The SSH session runs as a child process
- User can exit the SSH session with `exit` or `Ctrl+D` and return to LazySSH
- Still provides full TTY allocation with `-tt` flag
- No loss of functionality (colors, raw mode, signals all work)

**Implementation:**
```python
def open_terminal_native(self, socket_path: str) -> bool:
    # Build SSH command
    ssh_args = ["ssh", "-tt", "-S", socket_path, f"{username}@{host}"]
    
    # Run SSH as subprocess and wait for it to complete
    result = subprocess.run(ssh_args)
    
    return result.returncode == 0
```

**Alternatives considered:**
- `os.system()` - Less control over process, harder to capture errors
- `pexpect` - Overkill for this use case, adds complexity
- Keep `os.execvp()` - Doesn't meet user requirements

### Decision 2: Add terminal method column to status display

**Choice:** Add a "Terminal Method" column to the existing SSH connections table.

**Rationale:**
- Users can see at a glance which method is being used
- Minimal UI change, fits naturally in existing table
- No separate status line needed
- Consistent with how other connection properties are displayed

**Alternatives considered:**
- Global status line above table - Redundant if all connections use same method
- Only show when different from default - Users want to always see it
- Per-connection setting - Adds unnecessary complexity

### Decision 3: Add runtime configuration command

**Choice:** Add a `terminal <method>` command to both command mode and menu mode.

**Command mode:**
```
lazyssh> terminal native
Terminal method set to: native

lazyssh> terminal auto
Terminal method set to: auto (will use terminator if available, otherwise native)
```

**Menu mode:**
Add option "9. Change terminal method" that prompts for selection.

**Rationale:**
- Matches existing command patterns in LazySSH
- No need to restart application or edit environment variables
- Simple to implement and test
- Works in both interaction modes

**Alternatives considered:**
- `set terminal <method>` - More verbose, not needed
- Only environment variable - Can't change at runtime
- Per-connection setting - Unnecessary complexity

### Decision 4: Store terminal method in SSHManager state

**Choice:** Add `terminal_method` attribute to `SSHManager` class, initialized from `get_terminal_method()`.

**Rationale:**
- Centralized state management
- Easy to query current setting
- Can be changed at runtime without environment variable changes
- Doesn't require changes to SSHConnection model

**Implementation:**
```python
class SSHManager:
    def __init__(self):
        self.connections = {}
        self.terminal_method = get_terminal_method()  # Initialize from env/config
    
    def set_terminal_method(self, method: TerminalMethod):
        """Change terminal method at runtime"""
        self.terminal_method = method
```

### Decision 5: Native terminal returns boolean, not exits process

**Choice:** Change `open_terminal_native()` return type from `None` to `bool` and remove `os.execvp()`.

**Rationale:**
- Consistent with `open_terminal_terminator()` which returns bool
- Allows error handling and status reporting
- No breaking changes to callers (they already check return values)
- Makes testing easier

**Breaking change note:** This changes the behavior of native mode, but the old behavior was problematic and is the reason for this change.

## Risks / Trade-offs

### Risk 1: Native terminal subprocess might not handle all terminal features correctly
**Mitigation:** 
- Use `-tt` flag for forced TTY allocation
- Test with common use cases (vim, tmux, color output, etc.)
- Document any known limitations
- Users can still use Terminator if issues arise

### Risk 2: Users might expect per-connection terminal preferences
**Mitigation:**
- Document that terminal method is global
- Keep implementation simple for first iteration
- Can add per-connection preferences in future if there's demand

### Risk 3: Changing from execvp to subprocess might have subtle differences
**Mitigation:**
- Thoroughly test common terminal operations
- Update documentation to reflect new behavior
- Consider this a breaking change in behavior (but an improvement)

## Migration Plan

### For Users:
- **No action required** - Change is backward compatible
- Users who relied on native mode exiting will now return to LazySSH
- Document new behavior in CHANGELOG and user guide
- Recommend testing terminal-heavy workflows after upgrade

### For Developers:
1. Update `open_terminal_native()` implementation
2. Add terminal method column to UI display
3. Add runtime configuration command
4. Update tests for new behavior
5. Update documentation

### Rollback:
If issues arise, users can:
1. Use Terminator mode instead (`LAZYSSH_TERMINAL_METHOD=terminator`)
2. Revert to previous version

## Open Questions

1. **Should we add a confirmation prompt when opening native terminal?**
   - Probably not - adds friction for common operation
   - Users can exit anytime with `Ctrl+D` or `exit`

2. **Should terminal method be persisted to config file?**
   - Not in this change - keep it simple
   - Environment variable or runtime command is sufficient
   - Can add config file persistence later if needed

3. **Should we show terminal method in banner or startup message?**
   - Yes, but as low-priority enhancement
   - Add to status display first, banner can come later

