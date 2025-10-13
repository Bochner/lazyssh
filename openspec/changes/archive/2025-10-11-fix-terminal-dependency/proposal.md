# Fix Terminal Dependency and Add Native Python Terminal

## Why

Terminator is currently marked as optional in the code but causes the program to fail on startup with "missing required dependencies" error, preventing LazySSH from running. Additionally, users need an external terminal emulator (Terminator) to access SSH terminals, creating an unnecessary external dependency for core SSH terminal functionality.

## What Changes

- **Fix dependency checking**: Separate required dependencies from optional dependencies so the application only exits if required dependencies are missing
- **Native Python terminal fallback**: Implement a native Python-based SSH terminal that works without any external terminal emulator using Python's `os.execvp()` or subprocess with PTY allocation
- **Terminal method selection**: Automatically detect and use available terminal methods (external emulator or native fallback)
- **User notifications**: Inform users about optional dependencies without preventing startup

## Impact

- Affected specs:
  - `platform-compatibility` (existing) - Modified dependency checking behavior
  - `terminal-integration` (new) - New native terminal capability
- Affected code:
  - `src/lazyssh/__init__.py` - Dependency checking logic
  - `src/lazyssh/__main__.py` - Startup dependency validation
  - `src/lazyssh/ssh.py` - Terminal opening logic
  - `src/lazyssh/config.py` - Terminal configuration options
