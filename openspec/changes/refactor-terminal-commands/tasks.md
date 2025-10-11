# Implementation Tasks

## 1. Command Refactoring
- [ ] 1.1 Create new `cmd_open()` method in `CommandMode` class for opening terminals
- [ ] 1.2 Refactor `cmd_terminal()` to only handle terminal method switching
- [ ] 1.3 Update command registration to include the new `open` command
- [ ] 1.4 Add `open` command to `LazySSHCompleter` class in prompt_toolkit
- [ ] 1.5 Ensure `open` command populates established sessions using `_get_connection_completions()`
- [ ] 1.6 Update tab completion for `terminal` command (only method names: auto, native, terminator)

## 2. Help and Error Messages
- [ ] 2.1 Update `terminal` command help text to only show method switching usage
- [ ] 2.2 Create `open` command help text showing terminal opening usage
- [ ] 2.3 Add helpful error message in `terminal` command if user provides SSH connection name (suggest using `open`)
- [ ] 2.4 Add helpful error message in `open` command if user provides method name (suggest using `terminal`)

## 3. Menu Mode Updates
- [ ] 3.1 Check if menu mode (`__main__.py`) needs updates for the new command structure
- [ ] 3.2 Update menu options if they reference the old terminal command usage

## 4. Documentation Updates
- [ ] 4.1 Update command reference documentation (`docs/commands.md`)
- [ ] 4.2 Update user guide with new command examples
- [ ] 4.3 Update README with corrected command examples
- [ ] 4.4 Add migration note to CHANGELOG.md

## 5. Terminal Method Display Investigation
- [ ] 5.1 Verify terminal method is displaying correctly in status table
- [ ] 5.2 Test that method changes are immediately reflected in the display
- [ ] 5.3 Fix any display issues if found

## 6. Testing
- [ ] 6.1 Test `terminal auto/native/terminator` commands
- [ ] 6.2 Test `open <ssh_id>` command
- [ ] 6.3 Test error handling for invalid inputs
- [ ] 6.4 Test tab completion for `open` command shows active SSH connections
- [ ] 6.5 Test tab completion for `terminal` command shows only method names
- [ ] 6.6 Test that `close` and `open` commands work symmetrically
- [ ] 6.7 Verify terminal method display in status table

