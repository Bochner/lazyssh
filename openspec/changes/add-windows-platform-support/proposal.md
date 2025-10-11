# Add Windows Platform Support

## Why

LazySSH currently crashes on Windows immediately after displaying the banner because the dependency check uses the `which` shell command to locate executables, which is not available on Windows. This prevents Windows users from running the application natively.

## What Changes

- Replace subprocess calls to `which` command with Python's built-in `shutil.which()` function
- Update `_check_executable()` function in `src/lazyssh/__init__.py` to use `shutil.which()`
- Update terminator availability check in `src/lazyssh/ssh.py` to use the updated function
- This approach is simpler, more Pythonic, and automatically cross-platform

## Impact

- **Affected specs**: New capability `platform-compatibility`
- **Affected code**: 
  - `src/lazyssh/__init__.py` (lines 69-86: `_check_executable` function)
  - `src/lazyssh/ssh.py` (line 288: terminator path check)
- **Breaking changes**: None
- **Benefits**: Enables LazySSH to run on Windows natively with minimal code changes, following Python best practices

