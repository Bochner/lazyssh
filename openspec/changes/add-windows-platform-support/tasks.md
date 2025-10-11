# Implementation Tasks

## 1. Update Executable Checking with shutil.which()

- [x] 1.1 Import `shutil` module in `src/lazyssh/__init__.py` (if not already imported)
- [x] 1.2 Replace subprocess call to `which` command with `shutil.which(name)` in `_check_executable()`
- [x] 1.3 Simplify function logic - `shutil.which()` returns path if found, None otherwise
- [x] 1.4 Keep the file existence and executable permission checks for robustness

## 2. Update Terminator Check

- [x] 2.1 Update terminator availability check in `src/lazyssh/ssh.py` to use `_check_executable()` or `shutil.which()` directly
- [x] 2.2 Remove subprocess call to `which` command

## 3. Testing and Validation

- [x] 3.1 Test on Windows environment to verify executable detection works
- [x] 3.2 Test on Unix/Linux to ensure existing functionality still works
- [x] 3.3 Test on macOS to ensure existing functionality still works
- [x] 3.4 Verify error handling when executable is not found
- [x] 3.5 Add unit tests for cross-platform executable detection

## 4. Documentation

- [x] 4.1 Update project.md to reflect Windows support
- [x] 4.2 Update README.md to indicate Windows compatibility
- [x] 4.3 Add Windows-specific installation notes if needed

