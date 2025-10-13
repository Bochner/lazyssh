# Implementation Tasks

## 1. Fix Dependency Checking (Critical Bug Fix)
- [x] 1.1 Modify `check_dependencies()` in `__init__.py` to return `(required_missing, optional_missing)` tuple instead of single list
- [x] 1.2 Update SSH dependency check to be classified as required
- [x] 1.3 Update Terminator dependency check to be classified as optional
- [x] 1.4 Modify `main()` in `__main__.py` to only exit (sys.exit(1)) if required dependencies are missing
- [x] 1.5 Display warning messages for optional missing dependencies but allow program to continue
- [x] 1.6 Test that LazySSH starts successfully without Terminator installed

## 2. Add Configuration for Terminal Method
- [x] 2.1 Add `LAZYSSH_TERMINAL_METHOD` environment variable support in `config.py`
- [x] 2.2 Add validation for terminal method values: `auto`, `terminator`, `native`
- [x] 2.3 Set default to `auto` (tries available methods in order)
- [x] 2.4 Add configuration option to connection model if needed

## 3. Implement Native Python Terminal
- [x] 3.1 Create new function `open_terminal_native()` in `ssh.py` using `os.execvp()` approach
- [x] 3.2 Build SSH command with proper TTY allocation (-tt flag)
- [x] 3.3 Handle SSH connection socket path in command
- [x] 3.4 Add shell specification if provided in connection config
- [x] 3.5 Add error handling and logging
- [x] 3.6 Display informative message before launching terminal

## 4. Update Terminal Opening Logic
- [x] 4.1 Refactor `open_terminal()` to detect available terminal methods
- [x] 4.2 Implement terminal method selection logic based on config and availability
- [x] 4.3 Try methods in order: configured preference → Terminator (if available) → native fallback
- [x] 4.4 Update user messages to indicate which terminal method is being used
- [x] 4.5 Ensure backward compatibility - existing Terminator usage should work unchanged
- [x] 4.6 Add proper error handling for each terminal method

## 5. Update Logging and User Feedback
- [x] 5.1 Add log messages for terminal method selection
- [x] 5.2 Update UI messages to show terminal method being used (e.g., "Opening terminal (native)" vs "Opening terminal (terminator)")
- [x] 5.3 Log when falling back from one method to another
- [x] 5.4 Ensure error messages are clear when all terminal methods fail

## 6. Testing
- [x] 6.1 Test application startup without Terminator installed (should start with warning)
- [x] 6.2 Test application startup with Terminator installed (should start normally)
- [x] 6.3 Test native terminal opening functionality
- [x] 6.4 Test Terminator terminal opening when installed
- [x] 6.5 Test terminal method configuration options
- [x] 6.6 Test fallback behavior when preferred method unavailable
- [x] 6.7 Verify SSH connection functionality in native terminal
- [x] 6.8 Test error handling for various failure scenarios

## 7. Documentation
- [x] 7.1 Update README to reflect that Terminator is optional
- [x] 7.2 Document `LAZYSSH_TERMINAL_METHOD` configuration option
- [x] 7.3 Document native terminal mode behavior
- [x] 7.4 Add troubleshooting section for terminal-related issues
- [x] 7.5 Update installation instructions to clarify optional dependencies
