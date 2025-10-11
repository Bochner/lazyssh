# Implementation Tasks

## 1. Fix Dependency Checking (Critical Bug Fix)
- [ ] 1.1 Modify `check_dependencies()` in `__init__.py` to return `(required_missing, optional_missing)` tuple instead of single list
- [ ] 1.2 Update SSH dependency check to be classified as required
- [ ] 1.3 Update Terminator dependency check to be classified as optional
- [ ] 1.4 Modify `main()` in `__main__.py` to only exit (sys.exit(1)) if required dependencies are missing
- [ ] 1.5 Display warning messages for optional missing dependencies but allow program to continue
- [ ] 1.6 Test that LazySSH starts successfully without Terminator installed

## 2. Add Configuration for Terminal Method
- [ ] 2.1 Add `LAZYSSH_TERMINAL_METHOD` environment variable support in `config.py`
- [ ] 2.2 Add validation for terminal method values: `auto`, `terminator`, `native`
- [ ] 2.3 Set default to `auto` (tries available methods in order)
- [ ] 2.4 Add configuration option to connection model if needed

## 3. Implement Native Python Terminal
- [ ] 3.1 Create new function `open_terminal_native()` in `ssh.py` using `os.execvp()` approach
- [ ] 3.2 Build SSH command with proper TTY allocation (-tt flag)
- [ ] 3.3 Handle SSH connection socket path in command
- [ ] 3.4 Add shell specification if provided in connection config
- [ ] 3.5 Add error handling and logging
- [ ] 3.6 Display informative message before launching terminal

## 4. Update Terminal Opening Logic
- [ ] 4.1 Refactor `open_terminal()` to detect available terminal methods
- [ ] 4.2 Implement terminal method selection logic based on config and availability
- [ ] 4.3 Try methods in order: configured preference → Terminator (if available) → native fallback
- [ ] 4.4 Update user messages to indicate which terminal method is being used
- [ ] 4.5 Ensure backward compatibility - existing Terminator usage should work unchanged
- [ ] 4.6 Add proper error handling for each terminal method

## 5. Update Logging and User Feedback
- [ ] 5.1 Add log messages for terminal method selection
- [ ] 5.2 Update UI messages to show terminal method being used (e.g., "Opening terminal (native)" vs "Opening terminal (terminator)")
- [ ] 5.3 Log when falling back from one method to another
- [ ] 5.4 Ensure error messages are clear when all terminal methods fail

## 6. Testing
- [ ] 6.1 Test application startup without Terminator installed (should start with warning)
- [ ] 6.2 Test application startup with Terminator installed (should start normally)
- [ ] 6.3 Test native terminal opening functionality
- [ ] 6.4 Test Terminator terminal opening when installed
- [ ] 6.5 Test terminal method configuration options
- [ ] 6.6 Test fallback behavior when preferred method unavailable
- [ ] 6.7 Verify SSH connection functionality in native terminal
- [ ] 6.8 Test error handling for various failure scenarios

## 7. Documentation
- [ ] 7.1 Update README to reflect that Terminator is optional
- [ ] 7.2 Document `LAZYSSH_TERMINAL_METHOD` configuration option
- [ ] 7.3 Document native terminal mode behavior
- [ ] 7.4 Add troubleshooting section for terminal-related issues
- [ ] 7.5 Update installation instructions to clarify optional dependencies

