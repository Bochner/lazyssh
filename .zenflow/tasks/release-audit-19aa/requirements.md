# Release Audit - Product Requirements Document

## Overview

LazySSH is at version **1.6.2** with 14 source modules (3,568 statements), 955 tests at 100% line coverage, and a modern Python toolchain (Hatch, Ruff, mypy, mise). This audit identifies concrete improvements across security, code quality, testing, documentation, dependencies, and tooling to bring the project up to current best practices as of February 2026.

---

## Current State Summary

| Metric | Value |
|--------|-------|
| Version | 1.6.2 |
| Python support | 3.11, 3.12, 3.13 |
| Source modules | 14 files, 3,568 statements |
| Test count | 955 tests, 100% line coverage |
| Lint status | Clean (ruff + mypy, zero issues) |
| All tests | Passing (3.3s) |
| Build system | Hatch + Hatchling |
| CI/CD | GitHub Actions (lint, test, publish) |

---

## Audit Findings and Requirements

### 1. Security Hardening

#### 1.1 Remove `shell=True` from subprocess calls
- **Priority**: High
- **Location**: `src/lazyssh/ssh.py:218`, `ssh.py:274`
- **Finding**: Two `subprocess.run()` calls use `shell=True`, which is a command injection risk. The `cmd` variable is constructed as a string.
- **Requirement**: Refactor these to use list-based commands (`subprocess.run(cmd_list, ...)`) without `shell=True`. This requires converting the SSH command strings to proper argument lists.
- **Impact**: Eliminates a class of injection vulnerabilities in the core SSH module.

#### 1.2 Enable Ruff security rules (flake8-bandit)
- **Priority**: Medium
- **Finding**: The current Ruff config selects `E, F, I, UP, B, C4, SIM` rules but omits security scanning entirely.
- **Requirement**: Add `"S"` (flake8-bandit) to Ruff's `lint.select`. Add per-file ignores for tests (`"tests/*" = ["S101"]` to allow `assert`). Triage and fix or suppress any findings.
- **Impact**: Automated security scanning on every lint run and CI check.

### 2. Code Quality Improvements

#### 2.1 Refactor high-complexity functions
- **Priority**: Medium
- **Finding**: Several functions exceed 200 lines with high cyclomatic complexity:
  - `LazySSHCompleter.get_completions` (281 lines) in `command_mode.py:48`
  - `SCPModeCompleter.get_completions` (324 lines) in `scp_mode.py:132`
  - `CommandMode.cmd_help` (370 lines) in `command_mode.py:985`
  - `SCPMode.cmd_mget` (261 lines) in `scp_mode.py:1422`
- **Requirement**: Extract command-specific completion logic into separate methods. Extract `cmd_help` into a data-driven approach (dictionary mapping topics to help text). Break `cmd_mget` into file discovery, size calculation, and download phases.
- **Impact**: Improved maintainability and testability of the most complex code paths.

#### 2.2 Tighten exception handling
- **Priority**: Low
- **Finding**: ~30 instances of `except Exception` across the codebase. Most log the error (good), but several silently swallow exceptions:
  - `scp_mode.py:216,243,318` - `except Exception: pass` in completion code
  - `plugin_manager.py:597` - `except Exception: pass`
  - `config.py:287,367,463` - re-raise after cleanup but no logging before cleanup attempt
- **Requirement**: Add debug-level logging to silently swallowed exceptions. Where possible, narrow `except Exception` to more specific exception types (e.g., `OSError`, `subprocess.SubprocessError`, `tomllib.TOMLDecodeError`).
- **Impact**: Better debuggability and clearer exception contract.

#### 2.3 Resolve `type: ignore` comments
- **Priority**: Low
- **Finding**: Two `# type: ignore` comments without explanation:
  - `config.py:30` - return value narrowing
  - `ssh.py:606` - attribute assignment
- **Requirement**: Either fix the underlying type narrowing issue (e.g., use `Literal` types properly) or add explanatory comments.

### 3. Testing Enhancements

#### 3.1 Enforce coverage threshold
- **Priority**: High
- **Finding**: 100% coverage is achieved but not enforced. No `fail_under` setting in `[tool.coverage.report]`. A future change could silently reduce coverage without CI catching it.
- **Requirement**: Add `fail_under = 100` to `[tool.coverage.report]` in `pyproject.toml`.
- **Impact**: Prevents regression of the 100% coverage standard.

#### 3.2 Add parametrized tests
- **Priority**: Low
- **Finding**: No use of `@pytest.mark.parametrize` anywhere in the test suite (955 tests). Many test classes repeat similar patterns with different inputs.
- **Requirement**: Identify 3-5 areas with repetitive test patterns and convert to parametrized tests. Good candidates: environment variable testing, terminal method options, config validation edge cases.
- **Impact**: More concise tests, better edge case coverage, easier to extend.

#### 3.3 Add additional Ruff rule sets for test code
- **Priority**: Low
- **Finding**: Test code is not checked with `"PT"` (flake8-pytest-style) rules.
- **Requirement**: Add `"PT"` to Ruff's `lint.select` and triage findings. This catches common pytest anti-patterns.

### 4. Documentation Gaps

#### 4.1 Missing CHANGELOG entries for v1.6.1 and v1.6.2
- **Priority**: High
- **Finding**: `__init__.py` declares version 1.6.2, but CHANGELOG.md only has entries through 1.6.0. The git log shows:
  - `654cf2e` - "Bump version to 1.6.2 in __init__.py"
  - `54f1374` - "Fix list command to display status as documented"
- **Requirement**: Add CHANGELOG entries for v1.6.1 and v1.6.2 based on the git history between those releases. This is a documentation-only fix.
- **Impact**: Users can see what changed in each release.

#### 4.2 Verify and update user documentation
- **Priority**: Medium
- **Finding**: User docs in `docs/` were last significantly updated in v1.5.1. Features and commands added or changed in 1.6.x may not be reflected.
- **Requirement**: Review `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, and `docs/troubleshooting.md` against the current command set and features. Update any stale instructions.

#### 4.3 Consolidate contributor guidance
- **Priority**: Low
- **Finding**: Developer guidance is spread across `CLAUDE.md`, `CONTRIBUTING.md`, and `openspec/project.md` with some overlapping and potentially conflicting information.
- **Requirement**: Audit for contradictions or stale info. Ensure each file has a distinct purpose without duplication. Add cross-references where appropriate.

### 5. Dependency and Packaging Updates

#### 5.1 Widen `prompt_toolkit` version constraint
- **Priority**: Medium
- **Finding**: Currently pinned to `>=3.0.39,<3.1.0`. The latest release is 3.0.52 (Aug 2025), which is compatible. The upper bound `<3.1.0` is reasonable since there's no 3.1.x release, but the lower bound of 3.0.39 is unnecessarily specific.
- **Requirement**: Review whether the lower bound can be relaxed to `>=3.0.0` or at least document why 3.0.39 is the minimum. Verify the project works with the latest 3.0.52.
- **Decision**: Keep `<3.1.0` as a safety guard (no 3.1 exists yet). Consider adjusting lower bound if no 3.0.39-specific features are used.

#### 5.2 Audit minimum dependency versions
- **Priority**: Low
- **Finding**: Some minimum versions may be more conservative than needed:
  - `rich>=13.0.0` (current: 14.3.3)
  - `click>=8.0.0` (current: 8.3.1)
  - `paramiko>=3.0.0` (current: 4.0.0)
- **Requirement**: Verify that the declared minimums are actually tested. Since CI only tests with the latest resolved versions, the actual minimum compatibility is unknown. Consider adding a CI job with `pip install --upgrade-strategy=only-if-needed` or testing against lower bounds.
- **Decision**: This is a nice-to-have. The current approach (generous lower bounds) works for most users.

#### 5.3 Consider `requires-python` in Ruff config
- **Priority**: Low
- **Finding**: Ruff config uses `target-version = "py311"` but best practice is to use `project.requires-python` instead, which Ruff can infer automatically.
- **Requirement**: Remove `target-version` from `[tool.ruff]` if Ruff can correctly infer from `requires-python = ">=3.11"`.

### 6. Tooling and CI/CD Improvements

#### 6.1 Expand Ruff rule set
- **Priority**: Medium
- **Finding**: Current rules: `E, F, I, UP, B, C4, SIM`. Missing commonly recommended rules:
  - `"S"` - Security (flake8-bandit) - covered in 1.2
  - `"N"` - PEP 8 naming conventions
  - `"PT"` - pytest style
  - `"RET"` - return statement checks
  - `"PTH"` - prefer pathlib over os.path
  - `"T20"` - no print statements (enforce logging)
- **Requirement**: Incrementally add rule sets, triage findings, and fix or document suppressions. Start with `"S"` and `"PT"`, then evaluate others.

#### 6.2 Strengthen mypy configuration
- **Priority**: Medium
- **Finding**: mypy uses `ignore_missing_imports = true` and `warn_return_any = true` but lacks stricter settings like `disallow_untyped_defs`, `strict_equality`, or `warn_unreachable`.
- **Requirement**: Incrementally tighten mypy. Since the codebase already has good type annotations, enabling `disallow_untyped_defs = true` and `strict_equality = true` should require minimal changes. Add `[[tool.mypy.overrides]]` for third-party modules that need `ignore_missing_imports`.

#### 6.3 Add per-file Ruff ignores for tests
- **Priority**: Low
- **Finding**: No `[tool.ruff.lint.per-file-ignores]` section exists. If security rules (`"S"`) are enabled, tests will flag `assert` usage.
- **Requirement**: Add `"tests/*" = ["S101"]` at minimum. Evaluate other per-file ignores as new rule sets are added.

---

## Out of Scope

The following items were considered but deemed out of scope for this audit:

- **Migration to uv**: While uv is the modern package manager trend, Hatch is well-established and working. Migration would be a separate initiative.
- **Python 3.14 support**: Not yet stable. Can be added when released.
- **Integration tests**: The project is a CLI tool that wraps SSH. True integration tests would require SSH infrastructure. The current unit test approach with thorough mocking is appropriate.
- **Free-threaded Python (PEP 703)**: Experimental in 3.13, not relevant for an SSH CLI tool.
- **Windows support**: Explicitly not supported (POSIX-only tool). No change needed.

---

## Priority Summary

| Priority | Item | Section |
|----------|------|---------|
| **High** | Remove `shell=True` from subprocess | 1.1 |
| **High** | Enforce coverage threshold (`fail_under = 100`) | 3.1 |
| **High** | Add missing CHANGELOG entries for v1.6.1, v1.6.2 | 4.1 |
| **Medium** | Enable Ruff security rules (`"S"`) | 1.2 |
| **Medium** | Refactor high-complexity functions | 2.1 |
| **Medium** | Verify/update user documentation | 4.2 |
| **Medium** | Widen/review `prompt_toolkit` constraint | 5.1 |
| **Medium** | Expand Ruff rule set | 6.1 |
| **Medium** | Strengthen mypy configuration | 6.2 |
| **Low** | Tighten exception handling | 2.2 |
| **Low** | Resolve `type: ignore` comments | 2.3 |
| **Low** | Add parametrized tests | 3.2 |
| **Low** | Add pytest-style lint rules | 3.3 |
| **Low** | Consolidate contributor docs | 4.3 |
| **Low** | Audit minimum dependency versions | 5.2 |
| **Low** | Use `requires-python` for Ruff target | 5.3 |
| **Low** | Add per-file Ruff ignores | 6.3 |

---

## Success Criteria

1. All high-priority items resolved
2. All medium-priority items resolved or explicitly deferred with rationale
3. `make check` and `make test` continue to pass with zero regressions
4. 100% test coverage maintained and enforced
5. No new security warnings from Ruff `"S"` rules (or documented suppressions)
6. CHANGELOG accurately reflects all released versions
