# Implementation Tasks

## 1. Command Refactoring
- [x] 1.1 Create new `cmd_open()` method in `CommandMode` class for opening terminals
- [x] 1.2 Refactor `cmd_terminal()` to only handle terminal method switching
- [x] 1.3 Update command registration to include the new `open` command
- [x] 1.4 Add `open` command to `LazySSHCompleter` class in prompt_toolkit
- [x] 1.5 Ensure `open` command populates established sessions using `_get_connection_completions()`
- [x] 1.6 Update tab completion for `terminal` command (only method names: auto, native, terminator)

## 2. Help and Error Messages
- [x] 2.1 Update `terminal` command help text to only show method switching usage
- [x] 2.2 Create `open` command help text showing terminal opening usage
- [x] 2.3 Add helpful error message in `terminal` command if user provides SSH connection name (suggest using `open`)
- [x] 2.4 Add helpful error message in `open` command if user provides method name (suggest using `terminal`)

## 3. Menu Mode Updates
- [x] 3.1 Check if menu mode (`__main__.py`) needs updates for the new command structure
- [x] 3.2 Update menu options if they reference the old terminal command usage

## 4. Documentation Updates
- [x] 4.1 Update command reference documentation (`docs/commands.md`)
- [x] 4.2 Update user guide with new command examples
- [x] 4.3 Update README with corrected command examples
- [x] 4.4 Add migration note to CHANGELOG.md

## 5. Terminal Method Display Investigation
- [x] 5.1 Verify terminal method is displaying correctly in status table
- [x] 5.2 Test that method changes are immediately reflected in the display
- [x] 5.3 Fix any display issues if found

## 6. Testing
- [x] 6.1 Test `terminal auto/native/terminator` commands
- [x] 6.2 Test `open <ssh_id>` command
- [x] 6.3 Test error handling for invalid inputs
- [x] 6.4 Test tab completion for `open` command shows active SSH connections
- [x] 6.5 Test tab completion for `terminal` command shows only method names
- [x] 6.6 Test that `close` and `open` commands work symmetrically
- [x] 6.7 Verify terminal method display in status table
