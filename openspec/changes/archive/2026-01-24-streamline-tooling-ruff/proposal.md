## Why

The current tooling setup has significant redundancy:

1. **5 overlapping tools for linting/formatting**: Black, isort, flake8, pylint, pyupgrade
2. **4 separate Hatch environments**: default, test, lint, typing (each with duplicate dependencies)
3. **Duplicate scripts**: Same operations defined in both default and lint environments
4. **182-line pre-commit-check.sh**: Duplicates what `make verify` already does
5. **No default coverage display**: Must explicitly run `make coverage` to see test coverage

**Ruff** is a modern, Rust-based tool that replaces Black, isort, flake8, pylint, and pyupgrade with a single tool that's 10-100x faster.

## What Changes

- **REMOVE**: Black, isort, flake8, pylint, pyupgrade dependencies
- **ADD**: Ruff as the single linting/formatting tool
- **SIMPLIFY**: Consolidate 4 Hatch environments into 1 (default only)
- **SIMPLIFY**: Reduce Makefile targets (remove redundant ones)
- **REMOVE**: pre-commit-check.sh (replaced by `make check`)
- **REMOVE**: .flake8 config file (moved to pyproject.toml under [tool.ruff])
- **ENHANCE**: Make `hatch run test` show coverage percentage by default
- **ENHANCE**: Add Ruff to mise.toml for version pinning

## Impact

- Affected specs: None (tooling-only change)
- Affected files:
  - `pyproject.toml` - Major simplification
  - `Makefile` - Reduced targets
  - `.mise.toml` - Add ruff tool
  - `.flake8` - Remove (config moved to pyproject.toml)
  - `pre-commit-check.sh` - Remove
  - `.github/workflows/*.yml` - Use ruff
  - Documentation (README, CONTRIBUTING, maintainers, CLAUDE.md)
