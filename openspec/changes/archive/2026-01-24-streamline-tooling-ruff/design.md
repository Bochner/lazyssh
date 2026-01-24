## Spec Delta Status

**This is a tooling-only change** - it affects build configuration, CI, and developer experience but has no impact on runtime behavior or user-facing features. There are no spec deltas because:

1. Build tooling (Hatch, Ruff, pytest) is infrastructure, not product features
2. No existing specs cover development tooling
3. The application behavior remains unchanged

This change will be archived with `--skip-specs` since it's equivalent to the `modernize-hatch-mise` change.

---

## Context

After modernizing to Hatch and mise, the project still carries legacy tool sprawl from the setuptools era. The current setup uses 5 separate tools for code quality that Ruff can replace.

### Current State (Redundant)

| Function | Current Tools | Ruff Equivalent |
|----------|---------------|-----------------|
| Formatting | Black | `ruff format` |
| Import sorting | isort | `ruff check --select I` |
| Linting | flake8 + pylint | `ruff check` |
| Syntax upgrade | pyupgrade | `ruff check --select UP` |
| Type checking | mypy | mypy (keep - Ruff doesn't do types) |

**4 Hatch environments with duplicate deps:**
- `default`: black, isort, flake8, pylint, pytest, pytest-cov, mypy, pre-commit, build, twine, pyupgrade, pytest-watch
- `test`: pytest, pytest-cov
- `lint`: black, isort, flake8, pylint, pyupgrade
- `typing`: mypy

## Goals / Non-Goals

**Goals:**
- Replace 5 tools with Ruff (single tool, single config)
- Consolidate to single Hatch environment
- Reduce Makefile complexity
- Show test coverage by default
- Faster CI and local checks

**Non-Goals:**
- Changing test framework (keep pytest)
- Changing type checker (keep mypy - Ruff doesn't do type checking)
- Changing build system (keep Hatch)

## Decisions

### Decision 1: Replace formatting/linting tools with Ruff

**What**: Remove black, isort, flake8, pylint, pyupgrade. Add ruff.

**Why**:
- Ruff is 10-100x faster
- Single configuration in pyproject.toml
- Actively maintained, gaining industry adoption
- Compatible with existing Black/isort formatting

**Configuration approach**:
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM"]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.format]
quote-style = "double"
```

### Decision 2: Single Hatch environment

**What**: Remove test, lint, typing environments. Use default for everything.

**Why**:
- All tools needed for dev are in one env
- No confusion about which env to use
- Faster setup (one env instead of four)
- Hatch scripts still provide organization

**Scripts**:
```toml
[tool.hatch.envs.default.scripts]
fmt = "ruff format src tests"
lint = "ruff check src tests"
fix = "ruff check --fix src tests && ruff format src tests"
test = "pytest -xvs tests"
cov = "pytest --cov=src --cov-report=term-missing tests"
check = ["ruff check src tests", "ruff format --check src tests", "mypy src"]
```

### Decision 3: Simplified Makefile

**Current (22 targets)**: help, clean, install, dev-install, test, coverage, fmt, fix, lint, check, verify, build, dist, release, publish, publish-test, pre-commit, watch, version, deps-check, all, env-info, typecheck

**Proposed (12 targets)**:
| Target | Purpose |
|--------|---------|
| `help` | Show available commands |
| `install` | Create Hatch environment |
| `fmt` | Format code |
| `fix` | Auto-fix and format |
| `lint` | Run linting |
| `test` | Run tests with coverage |
| `check` | All quality checks |
| `build` | Build package |
| `clean` | Clean artifacts |
| `version` | Show version |
| `release` | Version bump workflow |
| `publish` | Publish to PyPI |

**Removed**:
- `dev-install` (same as install)
- `coverage` (merged into test)
- `verify` (same as check + test)
- `pre-commit` (same as check)
- `dist` (same as build)
- `publish-test` (rarely used, use hatch directly)
- `watch` (use hatch run watch directly)
- `deps-check` / `env-info` (use hatch commands directly)
- `typecheck` (included in check)
- `all` (removed, use check)

### Decision 4: Default coverage display

**What**: `make test` (and `hatch run test`) shows coverage percentage by default

**Why**:
- No need to remember separate coverage command
- Immediate feedback on test coverage
- Still generates HTML report for detailed view

**Configuration**:
```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing:skip-covered --cov-fail-under=0"
```

### Decision 5: Remove pre-commit-check.sh

**What**: Delete the 182-line shell script

**Why**:
- `make check` does the same thing
- Hatch scripts are more maintainable
- Less code to maintain

### Decision 6: Add Ruff to mise.toml

**What**: Pin Ruff version in mise for reproducibility

**Configuration**:
```toml
[tools]
python = "3.11"
ruff = "0.8"
```

## Migration Path

1. Add Ruff config to pyproject.toml
2. Run `ruff check --fix` to auto-fix any new issues
3. Remove old tool configs
4. Update Hatch environments/scripts
5. Update Makefile
6. Update CI workflows
7. Update documentation
8. Remove pre-commit-check.sh and .flake8

## Risks

| Risk | Mitigation |
|------|------------|
| Ruff catches more issues than flake8 | Run `ruff check --fix` during migration |
| Team unfamiliar with Ruff | Update docs, Ruff CLI is similar to flake8 |
| Different formatting | Ruff format is Black-compatible |
