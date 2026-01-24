## Why

The project currently has ~10% test coverage across all modules and lacks integrated HTML test/coverage reporting. Running `hatch test` produces no output. Comprehensive test coverage ensures code reliability and the reporting infrastructure enables efficient debugging and CI integration.

## What Changes

- Configure `hatch test` to run pytest with coverage and HTML reports
- Add pytest-html dependency for test result HTML reports
- Output coverage HTML report to `artifacts/coverage/`
- Output pytest HTML report to `artifacts/unit/`
- Display coverage summary to CLI by default
- Ensure 100% test coverage across all source modules
- Fix any hanging or slow tests blocking test execution

## Impact

- Affected specs: `build-system`
- Affected code: `pyproject.toml`, `tests/`
