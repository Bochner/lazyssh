# Design: Native Python Terminal and Dependency Fixing

## Context

LazySSH currently has a critical bug where Terminator is marked as optional but causes program startup failure. Additionally, requiring an external terminal emulator creates an unnecessary barrier for users who just want to use SSH terminal sessions.

Python provides native capabilities for spawning interactive SSH sessions through:
- `os.execvp()` - Replace current process with SSH command (best for direct terminal access)
- `subprocess` with `pty.spawn()` - Spawn SSH in a pseudo-terminal
- Paramiko's built-in terminal capabilities

## Goals / Non-Goals

**Goals:**
- Fix the dependency checking so optional dependencies don't prevent startup
- Implement a native Python terminal that works without external dependencies
- Maintain backward compatibility with Terminator for users who prefer it
- Provide seamless SSH terminal access using standard Python libraries

**Non-Goals:**
- Building a full-featured terminal emulator from scratch
- Replacing all terminal functionality with Python (external emulators remain an option)
- Supporting every possible terminal emulator (focus on native fallback)

## Decisions

### 1. Dependency Classification
- **Decision**: Split `check_dependencies()` to return separate lists for required and optional dependencies
- **Why**: Allows the application to start with warnings for optional deps but hard fail for required deps
- **Implementation**: Return `(required_missing, optional_missing)` tuple from `check_dependencies()`

### 2. Native Terminal Implementation  
- **Decision**: Use `os.execvp()` as the primary native terminal method
- **Why**: 
  - Most direct approach - replaces current process with SSH
  - Preserves all terminal functionality (colors, raw mode, signals)
  - Minimal code (~10 lines)
  - Works identically to running `ssh` directly in terminal
- **Alternatives considered**:
  - `subprocess.Popen()` with `pty.spawn()`: More complex, requires managing PTY master/slave, signal handling
  - Paramiko's channel.invoke_shell(): Requires implementing terminal emulation layer, output rendering
  - Keep Terminator-only: Defeats purpose of removing external dependency

### 3. Terminal Method Selection
- **Decision**: Try methods in order: configured preference → Terminator → native fallback
- **Why**: Respects user preference while ensuring functionality always works
- **Configuration**: Add `LAZYSSH_TERMINAL_METHOD` env var with values: `terminator`, `native`, `auto` (default)

### 4. User Experience
- **Decision**: Clear visual distinction between terminal methods in UI
- **Why**: Users should know which method is being used for debugging/preference
- **Implementation**: Display message like "Opening terminal (native)" vs "Opening terminal (terminator)"

## Risks / Trade-offs

### Risk: os.execvp() replaces the current process
- **Impact**: LazySSH process ends when SSH terminal closes
- **Mitigation**: Only use `execvp()` approach when explicitly opening terminal (user's intent is to enter terminal, not stay in LazySSH). Alternative: spawn new process with pty

### Risk: Native terminal may not handle all edge cases
- **Impact**: Some terminal features might not work perfectly
- **Mitigation**: Terminator remains available as fallback; document any limitations

### Trade-off: Simplicity vs Features
- **Choice**: Simple `execvp()` approach over complex PTY management
- **Rationale**: Users want to drop into SSH terminal; they don't need LazySSH running in background. This matches behavior of running `ssh` directly.

## Implementation Plan

### Phase 1: Fix Dependency Checking (Critical Bug Fix)
1. Modify `check_dependencies()` to return `(required_missing, optional_missing)`  
2. Update `__main__.py` to only exit on required missing dependencies
3. Display warnings for optional missing dependencies
4. Test that application starts without Terminator installed

### Phase 2: Implement Native Terminal
1. Add configuration option for terminal method preference
2. Implement native terminal using `os.execvp()` 
3. Add detection logic for available terminal methods
4. Update `open_terminal()` to try methods in order

### Phase 3: Polish & Documentation
1. Add user-facing messages about terminal method being used
2. Update documentation about terminal options
3. Add tests for both terminal methods

## Migration Plan

**For Users:**
- No action required - application will automatically work without Terminator
- Optional: Set `LAZYSSH_TERMINAL_METHOD=terminator` to force Terminator usage if preferred
- Optional: Install Terminator for external terminal window experience

**Rollback:**
- If native terminal has issues, users can set `LAZYSSH_TERMINAL_METHOD=terminator` and install Terminator
- No data migration required - only code changes

## Open Questions

1. Should native terminal spawn in a new window or replace current process?
   - **Answer**: Replace current process for simplicity and direct SSH experience
2. Should we support other terminal emulators (gnome-terminal, xterm, etc.)?
   - **Answer**: Not in this change - focus on native fallback. Can add in future if requested.

