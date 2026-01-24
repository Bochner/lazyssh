## 1. Test Infrastructure

- [x] 1.1 Add pytest-html to dev dependencies in pyproject.toml
- [x] 1.2 Configure `hatch test` command in pyproject.toml (using hatch test matrix)
- [x] 1.3 Configure pytest to output HTML report to `artifacts/unit/report.html`
- [x] 1.4 Configure coverage to output HTML report to `artifacts/coverage/`
- [x] 1.5 Update pytest addopts for combined CLI + HTML coverage output
- [x] 1.6 Add `artifacts/` to .gitignore

## 2. Test Stability Fixes

- [x] 2.1 Investigate and fix any hanging tests
- [x] 2.2 Fix OSError spam during test runs (console_instance.py)
- [x] 2.3 Ensure all tests pass without timeouts

## 3. Coverage Completion

- [x] 3.1 Audit current coverage gaps per module
- [x] 3.2 Add missing tests for `__init__.py` (currently 27%)
- [x] 3.3 Add missing tests for `__main__.py` (currently 21%)
- [x] 3.4 Add missing tests for `command_mode.py` (currently 5%)
- [x] 3.5 Add missing tests for `config.py` (currently 11%)
- [x] 3.6 Add missing tests for `console_instance.py` (currently 50%)
- [x] 3.7 Add missing tests for `logging_module.py` (currently 37%)
- [x] 3.8 Add missing tests for `models.py` (currently 50%)
- [x] 3.9 Add missing tests for `plugin_manager.py` (currently 10%)
- [x] 3.10 Add missing tests for `plugins/__init__.py` (currently 0%)
- [x] 3.11 Add missing tests for `plugins/_enumeration_plan.py` (currently 0%)
- [x] 3.12 Add missing tests for `plugins/enumerate.py` (currently 0%)
- [x] 3.13 Add missing tests for `scp_mode.py` (currently 5%)
- [x] 3.14 Add missing tests for `ssh.py` (currently 8%)
- [x] 3.15 Add missing tests for `ui.py` (currently 18%)

## 4. Validation

- [x] 4.1 Run `hatch test` and verify CLI output shows coverage
- [x] 4.2 Verify `artifacts/coverage/index.html` is generated
- [x] 4.3 Verify `artifacts/unit/report.html` is generated
- [x] 4.4 Confirm 100% coverage achieved
- [x] 4.5 Update Makefile `test` target if needed
