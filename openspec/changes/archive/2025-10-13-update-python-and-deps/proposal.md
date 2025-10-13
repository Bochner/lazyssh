## Why
Keep runtime and dependencies current for security, performance and compatibility with modern systems.

## What Changes
- Update target Python runtime to latest stable 3.13.x
- Refresh runtime dependencies to latest compatible releases
- Update dev-tooling (black, isort, mypy, pytest, flake8, pylint, etc.)
- Adjust configs to new versions (e.g., mypy/black targets)

## Impact
- Affected specs: platform-compatibility
- Affected code: `pyproject.toml`, `requirements.txt`, CI/tool configs

## Risks
- Upstream breaking changes in libraries
- Local environment drift

## Mitigations
- Pin minimums compatible with Python 3.13
- Run test suite and adjust if needed

