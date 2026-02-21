# Release Audit - Technical Specification

## Technical Context

| Attribute | Value |
|-----------|-------|
| Language | Python 3.11+ (supports 3.11, 3.12, 3.13) |
| Build system | Hatch + Hatchling |
| Linter/Formatter | Ruff (replaces black, isort, flake8, pylint) |
| Type checker | mypy |
| Test framework | pytest + pytest-cov + pytest-timeout |
| CI/CD | GitHub Actions (lint, test, build, publish) |
| Tool management | mise |
| Git hooks | pre-commit |
| Package | lazyssh v1.6.2 |

### Source Structure

```
src/lazyssh/           # 14 modules, ~7,873 lines
  __init__.py          # Version, dependency checking
  __main__.py          # CLI entry point
  command_mode.py      # Interactive shell (1,994 lines)
  ssh.py               # SSH connections, tunnels (621 lines)
  scp_mode.py          # File transfers (2,201 lines)
  plugin_manager.py    # Plugin discovery/execution (639 lines)
  config.py            # TOML config persistence (481 lines)
  console_instance.py  # Rich console/theme (322 lines)
  logging_module.py    # Specialized loggers (387 lines)
  ui.py                # Rich UI components (840 lines)
  models.py            # Dataclasses (98 lines)
  plugins/             # Built-in plugins (~1,273 lines)
tests/                 # 20 files, ~15,577 lines, 955 tests
docs/                  # 5 user/maintainer docs + plugin template
```

### Key Dependencies

| Package | Constraint | Current | Purpose |
|---------|-----------|---------|---------|
| rich | >=13.0.0 | 14.x | Terminal UI |
| prompt_toolkit | >=3.0.39,<3.1.0 | 3.0.x | Interactive shell |
| click | >=8.0.0 | 8.x | CLI parsing |
| paramiko | >=3.0.0 | 4.x | SSH protocol |
| pexpect | >=4.8.0 | 4.x | Interactive process control |
| tomli-w | >=1.0.0 | 1.x | TOML writer |

---

## Implementation Approach

This audit is organized into 6 work areas, each containing changes that can be independently implemented and verified. The approach is incremental: each phase produces a testable result and does not break existing functionality.

---

### Area 1: Security Hardening

#### 1.1 Remove `shell=True` from subprocess calls

**Files:** `src/lazyssh/ssh.py`

**Current code (ssh.py:213-218):**
```python
cmd = f"ssh -S {socket_path} {tunnel_args} dummy"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
```

**Same pattern at ssh.py:269-274** for `close_tunnel()`.

**Approach:** Convert the f-string command to a list of arguments. The `tunnel_args` string contains SSH control options (`-O forward -L port:host:port`), which must be split into individual list elements.

**Target code pattern:**
```python
cmd = [
    "ssh", "-S", socket_path,
    "-O", "forward" if not reverse else "forward",
    f"-{'R' if reverse else 'L'}",
    f"{local_port}:{remote_host}:{remote_port}",
    "dummy",
]
result = subprocess.run(cmd, capture_output=True, text=True)
```

Similarly for `close_tunnel()` with `-O cancel` instead of `-O forward`.

**Risk:** Low. The existing tests mock `subprocess.run`, so the change is fully testable without SSH infrastructure. The argument list is constructed from validated internal state (connection socket path, integer ports, hostname strings).

**Test changes:** Update test assertions to expect list arguments instead of string commands. Verify `shell=True` is no longer passed.

#### 1.2 Enable Ruff security rules (S)

**Files:** `pyproject.toml`

**Changes:**
1. Add `"S"` to `[tool.ruff.lint] select`
2. Add `[tool.ruff.lint.per-file-ignores]` section:
   ```toml
   [tool.ruff.lint.per-file-ignores]
   "tests/*" = ["S101"]  # Allow assert in tests
   ```
3. Run `ruff check src tests` and triage all S-rule findings
4. For legitimate uses (e.g., `subprocess.run` with controlled inputs), add inline `# noqa: S603` with an explanatory comment
5. Fix genuine security issues found

**Expected findings:**
- S603 (subprocess without shell) - Expected on all `subprocess.run/Popen` calls; suppress with comment when inputs are controlled
- S607 (partial executable path) - Likely for `ssh`, `scp` commands; suppress since these are the tool's purpose
- S108 (hardcoded `/tmp`) - The project uses `/tmp/lazyssh` by design; suppress
- S101 (assert) - Only in tests, handled by per-file-ignores

---

### Area 2: Code Quality

#### 2.1 Refactor high-complexity functions

**Target functions and approach:**

| Function | File:Line | Lines | Approach |
|----------|-----------|-------|----------|
| `LazySSHCompleter.get_completions` | command_mode.py:48 | 281 | Extract per-command completion handlers into methods |
| `SCPModeCompleter.get_completions` | scp_mode.py:132 | 197 | Extract per-command completion handlers into methods |
| `CommandMode.cmd_help` | command_mode.py:985 | ~165 | Extract to data-driven dictionary mapping topics to help text |
| `SCPMode.cmd_mget` | scp_mode.py:1422 | 261 | Split into file discovery, size calculation, and download phases |

**Pattern for completer refactoring:**
```python
# Before: monolithic get_completions with inline logic per command
def get_completions(self, document, complete_event):
    if command == "lazyssh":
        # 50 lines of completion logic
    elif command == "tunc":
        # 40 lines of completion logic
    ...

# After: dispatch to per-command methods
def get_completions(self, document, complete_event):
    handler = self._completion_handlers.get(command)
    if handler:
        yield from handler(words, word_before_cursor)

def _complete_lazyssh(self, words, word_before_cursor):
    ...
```

**Pattern for cmd_help refactoring:**
```python
# Before: huge if/elif chain
# After: data-driven
HELP_TOPICS: dict[str, str] = {
    "lazyssh": "...",
    "tunc": "...",
    ...
}
```

**Pattern for cmd_mget refactoring:**
```python
# Before: single 261-line method
# After: three focused methods
def cmd_mget(self, args):
    files = self._mget_discover_files(args)
    total_size = self._mget_calculate_size(files)
    self._mget_download(files, total_size)
```

**Test impact:** Existing tests cover these functions at 100%. Refactoring preserves behavior, so tests should pass after extraction. New helper methods should be exercised through the existing test paths.

#### 2.2 Tighten exception handling

**Files:** All source modules (~65 instances of `except Exception`)

**Approach (incremental):**
1. **Silent swallowers first** (18 instances of `except Exception: pass` or without logging):
   - Add `SCP_LOGGER.debug(...)` or equivalent to every silent catch
   - Narrow to specific types where the expected failure is clear (e.g., `OSError` for file operations, `subprocess.SubprocessError` for process calls)
2. **Broad catches with logging** (remaining ~47 instances):
   - Narrow where the expected exception type is obvious
   - Leave as `except Exception` where genuinely unknown failures are possible (e.g., plugin execution)
   - Add `# noqa: BLE001` comment for intentionally broad catches if `BLE` rules are enabled later

**Priority exceptions to narrow:**
- `config.py` TOML operations: `tomllib.TOMLDecodeError`, `OSError`
- `scp_mode.py` file operations: `OSError`, `subprocess.SubprocessError`
- `ssh.py` connection operations: `subprocess.SubprocessError`, `OSError`
- `plugin_manager.py` metadata parsing: `ValueError`, `OSError`

#### 2.3 Resolve `type: ignore` comments

**9 instances across the codebase:**

| Location | Resolution |
|----------|------------|
| config.py:30 | Add error code: `# type: ignore[return-value]` with explanation |
| ssh.py:606 | Add error code: `# type: ignore[assignment]` with explanation |
| logging_module.py:323,325 | Type the dict properly: `dict[str, int]` instead of `dict[str, Any]` |
| plugin_manager.py:596 | Add error code: `# type: ignore[name-defined]` - variable conditionally defined in try/except |
| plugins/enumerate.py:37-40,45 | These are legitimate conditional imports; keep with existing error codes |

**Rule:** Every `# type: ignore` must have an error code and a brief reason comment.

---

### Area 3: Testing Enhancements

#### 3.1 Enforce coverage threshold

**File:** `pyproject.toml`

**Change:** Add `fail_under = 100` to `[tool.coverage.report]`:
```toml
[tool.coverage.report]
fail_under = 100
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

Also add `branch = true` to `[tool.coverage.run]` to enforce branch coverage (catches untested `if/else` paths):
```toml
[tool.coverage.run]
source = ["src/lazyssh"]
omit = ["tests/*"]
branch = true
```

**Risk:** Branch coverage may reveal untested branches that line coverage misses. If `fail_under = 100` fails with branch coverage enabled, the threshold may need to be adjusted or missing branches covered.

**Mitigation:** Enable branch coverage first, check the actual branch coverage percentage, then set `fail_under` accordingly. If branch coverage is significantly below 100%, set a realistic threshold (e.g., 95%) and note the gap.

#### 3.2 Add parametrized tests

**Candidates for parametrization (convert 3-5 repetitive test groups):**

1. **Terminal method options** - Tests that repeat for `auto`, `native`, `terminator`
2. **Environment variable toggle tests** - `LAZYSSH_PLAIN_TEXT`, `LAZYSSH_NO_ANIMATIONS`, `LAZYSSH_HIGH_CONTRAST`, `LAZYSSH_COLORBLIND_MODE`
3. **Config validation edge cases** - Various invalid config inputs
4. **Connection parameter combinations** - Different SSH option combinations
5. **Command parsing** - Same command with different argument patterns

**Pattern:**
```python
@pytest.mark.parametrize("method,expected", [
    ("auto", TerminalMethod.AUTO),
    ("native", TerminalMethod.NATIVE),
    ("terminator", TerminalMethod.TERMINATOR),
], ids=["auto", "native", "terminator"])
def test_terminal_method(method, expected):
    ...
```

**Impact:** Reduces test line count while improving edge case coverage. Does not reduce test count (parametrized tests expand at runtime).

#### 3.3 Add pytest-style lint rules (PT)

**File:** `pyproject.toml`

**Changes:**
1. Add `"PT"` to `[tool.ruff.lint] select`
2. Triage findings - common PT issues:
   - PT001: Use `@pytest.fixture` not `@pytest.fixture()`
   - PT006: Parametrize argument names should be tuple
   - PT011: `pytest.raises` should use `match` parameter
   - PT018: Composite assertion (multiple asserts in one statement)
3. Suppress rules that conflict with project style if needed

---

### Area 4: Documentation

#### 4.1 Add missing CHANGELOG entries

**File:** `CHANGELOG.md`

**Current state:** CHANGELOG has entries through 1.6.0. Missing entries for v1.6.1 and v1.6.2.

**Approach:**
1. Run `git log v1.6.0..HEAD --oneline` (or equivalent tag/commit range) to identify changes
2. Based on git history:
   - v1.6.2: "Bump version to 1.6.2 in __init__.py" (654cf2e)
   - v1.6.1/v1.6.2 changes: "Fix list command to display status as documented" (from PR #95/#96)
3. Add entries under appropriate version headers between `[Unreleased]` and `[1.6.0]`

#### 4.2 Verify and update user documentation

**Files:** `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, `docs/troubleshooting.md`

**Approach:**
1. Cross-reference documented commands against `CommandMode` command handlers
2. Cross-reference documented environment variables against actual usage
3. Verify config file format documentation matches `config.py` implementation
4. Check plugin documentation matches `plugin_manager.py` behavior
5. Update any stale instructions for v1.6.x changes

#### 4.3 Consolidate contributor guidance

**Files:** `CLAUDE.md`, `CONTRIBUTING.md`, `openspec/project.md`

**Approach:**
1. Audit for contradictions or stale info between the three files
2. Ensure distinct purpose:
   - `CLAUDE.md` - AI assistant instructions and quick reference
   - `CONTRIBUTING.md` - Human developer onboarding
   - `openspec/project.md` - Full project specification
3. Add cross-references where content overlaps
4. Remove duplicated information, keeping it in the most appropriate location

---

### Area 5: Dependencies and Packaging

#### 5.1 Review `prompt_toolkit` constraint

**File:** `pyproject.toml`

**Current:** `prompt_toolkit>=3.0.39,<3.1.0`

**Approach:**
1. Search the codebase for APIs introduced in 3.0.39 specifically
2. If no 3.0.39-specific features are found, relax to `>=3.0.36` or broader
3. Keep `<3.1.0` upper bound as a safety guard (no 3.1 exists)
4. Add a comment documenting the reasoning

#### 5.2 Audit minimum dependency versions

**Priority:** Low. Defer unless issues found.

**Approach:** Document that CI tests with latest resolved versions only. Add a comment in `pyproject.toml` noting this limitation. A minimum-version CI job is a future enhancement.

#### 5.3 Use `requires-python` for Ruff target

**File:** `pyproject.toml`

**Change:** Remove `target-version = "py311"` from `[tool.ruff]`. Ruff automatically infers the target from `project.requires-python = ">=3.11"`.

**Verification:** Run `ruff check src tests` after removal to confirm behavior is identical.

---

### Area 6: Tooling and CI/CD

#### 6.1 Expand Ruff rule set

**File:** `pyproject.toml`

**Phased expansion:**

**Phase 1 (with this audit):**
```toml
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "SIM",    # flake8-simplify
    "S",      # flake8-bandit (security) - NEW
    "PT",     # flake8-pytest-style - NEW
    "RET",    # flake8-return - NEW
]
```

**Phase 2 (evaluate and add if low-friction):**
- `"PTH"` - prefer pathlib (may require significant changes)
- `"T20"` - no print statements (enforce logging; need to audit for intentional print usage in CLI)

**Deferred (not included):**
- `"N"` - PEP 8 naming (may conflict with established conventions)
- `"FA"` - future annotations (not needed for 3.11+ only project)

**Per-file ignores:**
```toml
[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "S108"]
```

#### 6.2 Strengthen mypy configuration

**File:** `pyproject.toml`

**Target configuration:**
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
check_untyped_defs = true
strict_equality = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = [
    "paramiko.*",
    "pexpect.*",
    "prompt_toolkit.*",
    "art.*",
    "tomli_w.*",
    "colorama.*",
]
ignore_missing_imports = true
```

**Key change:** Replace global `ignore_missing_imports = true` with per-module overrides. This ensures mypy catches missing imports for first-party code and standard library while still allowing third-party packages without stubs.

**Incremental approach:**
1. Add `disallow_untyped_defs = true` - most impactful, catches missing type annotations
2. Add per-module `ignore_missing_imports` overrides
3. Remove global `ignore_missing_imports`
4. Fix any new mypy errors
5. Add remaining strict flags

**Risk:** Some functions may lack return type annotations. Since the codebase already has good typing, this should require minimal changes.

#### 6.3 CI workflow improvements

**File:** `.github/workflows/python-lint.yml`

**Current gap:** CI runs on a single Python version (whatever mise provides, typically 3.11). The `hatch test` matrix (3.11, 3.12, 3.13) is defined but not used in CI.

**Recommended change:** Add an explicit Python version matrix to the CI workflow:
```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12", "3.13"]
```

**Decision:** This is a configuration improvement. The existing hatch-test matrix handles multi-version testing locally, but CI should explicitly test all supported versions for confidence.

---

## Delivery Phases

### Phase 1: Low-risk configuration changes
- 3.1: Coverage threshold (`fail_under`)
- 5.3: Remove Ruff `target-version`
- 6.3: Per-file Ruff ignores
- 4.1: CHANGELOG entries

### Phase 2: Security hardening
- 1.1: Remove `shell=True` (ssh.py + test updates)
- 1.2: Enable Ruff `S` rules + triage

### Phase 3: Tooling tightening
- 6.1: Expand Ruff rules (add `S`, `PT`, `RET`)
- 6.2: Strengthen mypy configuration
- 3.3: Add PT rules (included in 6.1)

### Phase 4: Code quality refactoring
- 2.1: Refactor high-complexity functions
- 2.2: Tighten exception handling
- 2.3: Resolve `type: ignore` comments

### Phase 5: Testing improvements
- 3.2: Add parametrized tests

### Phase 6: Documentation and dependencies
- 4.2: Update user documentation
- 4.3: Consolidate contributor docs
- 5.1: Review `prompt_toolkit` constraint
- 5.2: Audit minimum dependency versions (documentation only)

---

## Verification Approach

After each phase, run the full quality gate:

```bash
make check    # ruff format --check + ruff check + mypy
make test     # pytest with coverage (must maintain 100%)
make build    # hatch build + twine check
```

**Regression criteria:**
- Zero ruff violations (or documented suppressions with `# noqa:` comments)
- Zero mypy errors
- 100% test coverage maintained (line; branch if enabled)
- All 955+ tests passing
- Package builds and verifies successfully

**Per-change verification:**
- Security changes (1.1): Verify subprocess calls no longer use `shell=True`
- Ruff rules (1.2, 6.1): Run `ruff check` with new rules, verify zero unfixed violations
- Mypy (6.2): Run `mypy src` with stricter config, verify zero errors
- Coverage (3.1): Verify `pytest` fails if coverage drops below threshold
- Refactoring (2.1): Verify all existing tests pass without modification (behavior preservation)
- Documentation (4.x): Manual review for accuracy
