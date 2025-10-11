# Terminal Commands Refactoring - Design

## Context

LazySSH currently uses the `terminal` command for two distinct purposes:
1. Opening terminal sessions on SSH connections (e.g., `terminal ubuntu`)
2. Changing the terminal method configuration (e.g., `terminal native`)

This dual functionality creates confusion and violates the single responsibility principle. Additionally, there's an asymmetry in the command interface - we have a `close` command but no matching `open` command.

**Current State:**
- `terminal <ssh_id>` - Opens a terminal
- `terminal <method>` - Changes terminal method
- `close <ssh_id>` - Closes a connection

**Desired State:**
- `terminal <method>` - Changes terminal method ONLY
- `open <ssh_id>` - Opens a terminal
- `close <ssh_id>` - Closes a connection (unchanged)

## Goals / Non-Goals

**Goals:**
- Create clear command separation for better user experience
- Establish symmetric `open`/`close` commands
- Maintain all existing functionality (just reorganized)
- Provide helpful error messages to guide users through the transition
- Ensure terminal method display works correctly in status table

**Non-Goals:**
- Changing how terminal methods work internally
- Modifying the `close` command behavior
- Changing SSH connection management
- Persisting terminal method preferences to disk

## Decisions

### Decision 1: Split terminal command into two commands
**Rationale:** Single responsibility principle - each command should do one thing well. The current dual functionality creates confusion about what `terminal <arg>` will do.

**Alternatives considered:**
- Keep current behavior (rejected: confusing for users)
- Use subcommands like `terminal open <ssh_id>` and `terminal set <method>` (rejected: more verbose, doesn't address `open`/`close` symmetry)

### Decision 2: Use `open` for the new command name
**Rationale:** Creates perfect symmetry with the existing `close` command. Users will intuitively understand that `open ubuntu` opens a connection and `close ubuntu` closes it.

**Alternatives considered:**
- `connect` (rejected: could be confused with creating new SSH connections)
- `shell` (rejected: less intuitive pairing with `close`)
- `session` (rejected: doesn't pair well with `close`)

### Decision 3: Provide helpful error messages for migration
**Rationale:** This is a breaking change. Users who type `terminal ubuntu` (old syntax) should get a clear message telling them to use `open ubuntu` instead.

**Implementation:**
- `terminal` command checks if argument matches a connection name and suggests `open` command
- `open` command checks if argument matches a method name and suggests `terminal` command

### Decision 4: Maintain backward-compatible tab completion
**Rationale:** Tab completion helps with discoverability. Each command should only suggest relevant completions.

**Implementation:**
- `terminal` tab completion: Only suggests `auto`, `native`, `terminator`
- `open` tab completion: Only suggests active SSH connection names

## Terminal Method Display Investigation

**Current Implementation Analysis:**
- Line 98 in `ui.py`: "Terminal Method" column exists in table definition
- Line 111 in `ui.py`: Column is populated with `terminal_method` parameter
- Line 294 in `command_mode.py`: `get_current_terminal_method()` is passed to display function
- Line 43 in `__main__.py`: Also correctly passes terminal method

**Conclusion:** The code appears correct. The display should be working. During implementation:
1. Test that terminal method displays correctly in status output
2. Verify method changes are immediately reflected
3. If issues are found, investigate runtime behavior

## Risks / Trade-offs

### Risk: Breaking change for existing users
**Impact:** Users accustomed to `terminal <ssh_id>` will get an error

**Mitigation:**
- Clear error message directing to `open` command
- Update all documentation and examples
- Add migration note to CHANGELOG
- Consider adding deprecation warning in a release before breaking change (if version permits)

### Risk: Tab completion needs to be updated in multiple places
**Impact:** Incomplete tab completion updates could confuse users

**Mitigation:**
- Search codebase for all tab completion logic
- Update both command mode and menu mode if applicable
- Test tab completion for both commands

### Risk: Menu mode might reference old command structure
**Impact:** Menu options might still reference old usage

**Mitigation:**
- Review `__main__.py` for menu-related terminal command usage
- Update any menu text or help that references the old structure

## Migration Plan

### Phase 1: Implementation (this proposal)
1. Create `cmd_open()` method
2. Refactor `cmd_terminal()` to only handle methods
3. Update tab completion
4. Add helpful error messages
5. Update documentation

### Phase 2: User Communication
1. Add prominent note in CHANGELOG
2. Update README with new command examples
3. Update all documentation files
4. Consider adding release notes highlighting the change

### Phase 3: Verification
1. Test all command variations
2. Verify error messages are helpful
3. Ensure terminal method display works
4. Confirm tab completion is correct

### Rollback Strategy
If needed, we can:
1. Revert the command split
2. Keep both functionalities in `terminal` command
3. Document the change as experimental

The codebase structure makes rollback straightforward since it's primarily a change in the command handler layer.

## Open Questions

1. **Should we add a deprecation period?**
   - Could add a warning in one release before making it a hard error
   - Decision: Evaluate based on user base size and feedback channels

2. **Should terminal method be persisted to config file?**
   - Current: Only persists for session duration
   - Decision: Out of scope for this change (matches current spec behavior)

3. **Should we add aliases (e.g., `t` for `terminal`, `o` for `open`)?**
   - Could improve user experience for power users
   - Decision: Out of scope for this change, can be added later if requested

