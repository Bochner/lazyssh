# Implementation Tasks

## 1. Core Terminal Session Management

- [x] 1.1 Modify `open_terminal_native()` in `src/lazyssh/ssh.py` to use `subprocess.run()` instead of `os.execvp()`
- [x] 1.2 Change return type of `open_terminal_native()` from `None` to `bool`
- [x] 1.3 Add success/failure handling and return appropriate boolean value
- [x] 1.4 Test that native terminal sessions run as subprocess and LazySSH continues running
- [x] 1.5 Test that users can exit SSH session with `exit` or `Ctrl+D` and return to LazySSH
- [x] 1.6 Verify all SSH features work correctly (colors, raw mode, vim, tmux, etc.)

## 2. Terminal Method State Management

- [x] 2.1 Add `terminal_method` attribute to `SSHManager` class in `src/lazyssh/ssh.py`
- [x] 2.2 Initialize `terminal_method` from `get_terminal_method()` in `SSHManager.__init__()`
- [x] 2.3 Add `set_terminal_method()` method to `SSHManager` class
- [x] 2.4 Add `get_current_terminal_method()` method to `SSHManager` class
- [x] 2.5 Update `open_terminal()` to use `self.terminal_method` instead of calling `get_terminal_method()`

## 3. UI Enhancements

- [x] 3.1 Add "Terminal Method" column to `display_ssh_status()` in `src/lazyssh/ui.py`
- [x] 3.2 Update column to show current terminal method (auto/native/terminator)
- [x] 3.3 Ensure column formatting is consistent with existing columns
- [x] 3.4 Test that terminal method displays correctly for all three modes

## 4. Command Mode Integration

- [x] 4.1 Add `terminal` command handler in `CommandMode` class in `src/lazyssh/command_mode.py`
- [x] 4.2 Implement validation for terminal method values (auto, native, terminator)
- [x] 4.3 Add success/error messages for terminal command
- [x] 4.4 Add `terminal` command to help text and completions
- [x] 4.5 Test command with valid and invalid inputs

## 5. Menu Mode Integration

- [x] 5.1 Add "Change terminal method" menu option to main menu in `src/lazyssh/__main__.py`
- [x] 5.2 Implement `change_terminal_method_menu()` function with method selection
- [x] 5.3 Add confirmation message after terminal method change
- [x] 5.4 Update menu option numbering (shift existing options)
- [x] 5.5 Test menu option with all three terminal methods

## 6. Documentation Updates

- [x] 6.1 Update `README.md` to document new terminal behavior
- [x] 6.2 Update `docs/user-guide.md` with terminal method commands
- [x] 6.3 Update `docs/troubleshooting.md` with terminal session guidance
- [x] 6.4 Add CHANGELOG entry for this breaking behavior change
- [x] 6.5 Document that native mode no longer exits LazySSH

## 7. Testing

- [x] 7.1 Test native terminal with various SSH commands (ls, vim, top, etc.)
- [x] 7.2 Test terminal method switching (auto → native → terminator)
- [x] 7.3 Test multiple sequential terminal sessions with same connection
- [x] 7.4 Test terminal sessions with multiple active connections
- [x] 7.5 Test that closing SSH session returns to LazySSH correctly
- [x] 7.6 Test that other connections remain active after closing one terminal session
- [x] 7.7 Test Terminator behavior remains unchanged
- [x] 7.8 Test with `LAZYSSH_TERMINAL_METHOD` environment variable
- [x] 7.9 Add unit tests for new methods in SSHManager
- [x] 7.10 Add integration tests for terminal command

## 8. Error Handling

- [x] 8.1 Handle subprocess failures gracefully in `open_terminal_native()`
- [x] 8.2 Add error message if SSH process fails to start
- [x] 8.3 Handle invalid terminal method gracefully
- [x] 8.4 Test error scenarios and verify error messages are clear
