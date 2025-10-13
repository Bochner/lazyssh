## Why

The current implementation in `src/lazyssh/logging_module.py` around lines 78-81 uses a local import of `display_error` to avoid circular imports. This is a code-smell that indicates architectural issues with module dependencies and makes the code harder to maintain and test.

## What Changes

- **BREAKING**: Introduce a new shared module `src/lazyssh/console_instance.py` that centralizes Rich Console management
- **BREAKING**: Move `display_error` and related display functions to the shared console module
- **BREAKING**: Update all modules to import console and display functions from the shared module instead of `ui.py`
- Remove the local import workaround in `logging_module.py`
- Update `ui.py` to use the shared console instance instead of creating its own

## Impact

- Affected specs: user-interface
- Affected code: 
  - `src/lazyssh/console_instance.py` (new file)
  - `src/lazyssh/logging_module.py` (remove local import)
  - `src/lazyssh/ui.py` (use shared console)
  - `src/lazyssh/command_mode.py` (update imports)
  - `src/lazyssh/scp_mode.py` (update imports)
  - `src/lazyssh/ssh.py` (update imports)
  - `src/lazyssh/__main__.py` (update imports)
