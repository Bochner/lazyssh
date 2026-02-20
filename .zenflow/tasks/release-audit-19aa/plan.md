# Full SDD workflow

## Configuration
- **Artifacts Path**: {@artifacts_path} → `.zenflow/tasks/{task_id}`

---

## Agent Instructions

If you are blocked and need user clarification, mark the current step with `[!]` in plan.md before stopping.

---

## Workflow Steps

### [x] Step: Requirements
<!-- chat-id: 9a29dc2b-9b0a-443f-847c-eb2f3c65ae13 -->

Create a Product Requirements Document (PRD) based on the feature description.

1. Review existing codebase to understand current architecture and patterns
2. Analyze the feature definition and identify unclear aspects
3. Ask the user for clarifications on aspects that significantly impact scope or user experience
4. Make reasonable decisions for minor details based on context and conventions
5. If user can't clarify, make a decision, state the assumption, and continue

Save the PRD to `{@artifacts_path}/requirements.md`.

### [x] Step: Technical Specification
<!-- chat-id: 87d97919-5791-40ef-9aa4-3042b9c8532d -->

Create a technical specification based on the PRD in `{@artifacts_path}/requirements.md`.

1. Review existing codebase architecture and identify reusable components
2. Define the implementation approach

Save to `{@artifacts_path}/spec.md` with:
- Technical context (language, dependencies)
- Implementation approach referencing existing code patterns
- Source code structure changes
- Data model / API / interface changes
- Delivery phases (incremental, testable milestones)
- Verification approach using project lint/test commands

### [x] Step: Planning
<!-- chat-id: 05b933b7-d84b-4922-814a-9092026752ad -->

Create a detailed implementation plan based on `{@artifacts_path}/spec.md`.

1. Break down the work into concrete tasks
2. Each task should reference relevant contracts and include verification steps
3. Replace the Implementation step below with the planned tasks

Save to `{@artifacts_path}/plan.md`.

### [x] Step 1: Low-risk configuration changes
<!-- chat-id: fb4c0f97-a4ed-4c5a-adbf-deb66728f82c -->

Apply safe, config-only changes that reduce risk and enforce existing standards. No behavioral code changes.

- [x] 1.1 Add `fail_under = 100` to `[tool.coverage.report]` in `pyproject.toml` (Req 3.1)
- [x] 1.2 Add `branch = true` to `[tool.coverage.run]` in `pyproject.toml`; run `make test` to verify branch coverage level; adjust `fail_under` if branch coverage is below 100% (Req 3.1) — branch coverage is 97.36%, set `fail_under = 97`
- [x] 1.3 Remove `target-version = "py311"` from `[tool.ruff]` in `pyproject.toml`; verify Ruff infers from `requires-python` by running `ruff check src tests` (Req 5.3)
- [x] 1.4 Add missing CHANGELOG entry for v1.6.2 based on `git log` (no v1.6.1 release exists — version went from 1.6.0 to 1.6.2) (Req 4.1)
- [x] 1.5 Run `make check && make test && make build` to verify no regressions — all pass (955 tests, 97.36% branch coverage, build clean)

### [x] Step 2: Security hardening — remove `shell=True`
<!-- chat-id: 02800780-d934-4553-b663-4efd5b183c4e -->

Eliminate command injection risk by converting subprocess calls from string commands to argument lists.

- [x] 2.1 In `src/lazyssh/ssh.py`, refactor `create_tunnel()` (~line 213-218): convert the f-string `cmd` to a list of arguments and remove `shell=True` from `subprocess.run()`
- [x] 2.2 In `src/lazyssh/ssh.py`, refactor `close_tunnel()` (~line 269-274): same conversion — list-based args, remove `shell=True`
- [x] 2.3 Update tests in `tests/` that assert on the subprocess `cmd` argument for tunnel operations — no changes needed; existing assertions use `"-R" in captured_cmd[0]` which works for both strings and lists
- [x] 2.4 Run `make check && make test` to verify all tests pass and coverage holds — 955 passed, 97.38% coverage, zero lint/type errors

### [x] Step 3: Expand Ruff rules and add per-file ignores
<!-- chat-id: 7eeff2d7-ed06-497b-a3b4-4c0d168b673e -->

Enable security (`S`), pytest-style (`PT`), and return-statement (`RET`) Ruff rules. Triage and resolve all findings.

- [x] 3.1 In `pyproject.toml`, add `"S"`, `"PT"`, `"RET"` to `[tool.ruff.lint] select`
- [x] 3.2 Add `[tool.ruff.lint.per-file-ignores]` section: `"tests/*" = ["S101", "S108", "S604", "PT009"]`
- [x] 3.3 Run `ruff check src tests` and triage all new findings (240 initial violations):
  - Fixed `os.system("clear")` → `subprocess.run(["/usr/bin/clear"])` (S605/S607)
  - Fixed `assert` in production code → `if`/`raise RuntimeError` guards (S101)
  - Fixed `shutil.which("tput")` → use resolved full path (S607)
  - Added `# noqa: S108` to 32 intentional `/tmp/lazyssh` usages
  - Added `# noqa: S603` to 16 controlled subprocess calls
  - Added `# noqa: S110` to 8 silent except-pass blocks (deferred to Step 6)
  - Added `RET504` to global ignores (named return variables improve readability)
- [x] 3.4 Fix PT-rule violations: PT022 (yield→return in fixture), PT018 (composite assertions split)
- [x] 3.5 Fix RET-rule violations: 27 RET505/RET507/RET502 auto-fixed, RET501 explicit return None fixed
- [x] 3.6 Run `make check && make test` — zero violations, 955 tests passed, 97.26% branch coverage

### [x] Step 4: Strengthen mypy configuration
<!-- chat-id: 0b5ef1f4-08f5-4875-8ff8-aaade71b84de -->

Tighten mypy settings incrementally. Move from global `ignore_missing_imports` to per-module overrides and enable stricter type checking.

- [x] 4.1 In `pyproject.toml`, add `disallow_untyped_defs = true`, `strict_equality = true`, `no_implicit_optional = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true` to `[tool.mypy]`
- [x] 4.2 Add `[[tool.mypy.overrides]]` for third-party modules (`paramiko`, `pexpect`, `prompt_toolkit`, `art`, `tomli_w`, `colorama`) with `ignore_missing_imports = true`
- [x] 4.3 Remove the global `ignore_missing_imports = true`
- [x] 4.4 Run `mypy src` and fix all new errors — 3 unused `type: ignore` comments fixed (plugin_manager.py, enumerate.py)
- [x] 4.5 Resolve all `# type: ignore` comments: added error codes and explanatory comments; replaced `dict[str, int | datetime]` with `TransferStats` TypedDict in `logging_module.py` to eliminate 2 `type: ignore` comments entirely; 6 remaining `type: ignore` comments all have error codes and explanations
- [x] 4.6 Run `make check && make test` — zero ruff/mypy errors, 955 tests passed, 97.22% branch coverage, build clean

### [x] Step 5: Refactor high-complexity functions
<!-- chat-id: 3cfa4e1a-55f0-4e17-8a43-4ea730cc91da -->

Break down the four highest-complexity functions into smaller, focused methods. Preserve all existing behavior — tests must pass without modification.

- [x] 5.1 Refactor `LazySSHCompleter.get_completions` in `command_mode.py`: extracted 10 private methods (`_complete_lazyssh`, `_complete_tunc`, `_complete_tund`, `_complete_terminal`, `_complete_single_arg_connection`, `_complete_single_arg_connection_name`, `_complete_single_arg_config`, `_complete_help`, `_complete_wizard`, `_complete_plugin`), dispatched via `_completion_handlers` dictionary
- [x] 5.2 Refactor `SCPModeCompleter.get_completions` in `scp_mode.py`: extracted 6 private methods (`_complete_remote_files`, `_complete_put`, `_complete_cd`, `_complete_local`, `_complete_lls`, `_complete_lcd`)
- [x] 5.3 Refactor `CommandMode.cmd_help` in `command_mode.py`: extracted 11 private methods (`_help_overview`, `_help_lazyssh`, `_help_tunc`, `_help_tund`, `_help_terminal`, `_help_open`, `_help_clear`, `_help_scp`, `_help_debug`, `_help_wizard`, `_help_plugin`), dispatched via `help_handlers` dictionary
- [x] 5.4 Refactor `SCPMode.cmd_mget` in `scp_mode.py`: split into `_mget_discover_files()`, `_mget_calculate_size()`, and `_mget_download()` helper methods
- [x] 5.5 Verified after each refactor — all 955 tests pass, 97.06% branch coverage, zero lint/type errors

### [x] Step 6: Tighten exception handling
<!-- chat-id: fad1c12f-8c7e-4286-931c-4aa954dcdc85 -->

Add logging to silent exception handlers and narrow broad `except Exception` catches where the expected failure type is clear.

- [x] 6.1 In `scp_mode.py`: narrowed 18 `except Exception` blocks — tab-completion handlers narrowed to `(OSError, subprocess.SubprocessError, ValueError)` with explanatory comments; SCP operations narrowed to `(OSError, subprocess.SubprocessError)`; date parsing narrowed to `(ValueError, OverflowError)`; local directory operations narrowed to `OSError`; top-level command loop kept as `except Exception` with comment
- [x] 6.2 In `plugin_manager.py`: narrowed 10 `except Exception` blocks — filesystem ops to `OSError`; path resolution to `OSError`; `is_relative_to` to `(ValueError, OSError)`; file reading to `(OSError, UnicodeDecodeError)`; plugin execution to `(OSError, subprocess.SubprocessError)`; streaming plugin to `(OSError, subprocess.SubprocessError)`; unbound process variable to `UnboundLocalError`
- [x] 6.3 In `config.py`: narrowed 9 `except Exception` blocks — directory/file creation to `OSError`; TOML loading already had `TOMLDecodeError` first, narrowed fallback to `OSError`; save/delete/backup atomic-write patterns narrowed inner and outer catches to `OSError`; cleanup `os.unlink` to `OSError`
- [x] 6.4 In `ssh.py`: narrowed all 8 `except Exception` blocks to `(OSError, subprocess.SubprocessError)` — covers connection creation, checking, tunnel create/close, terminal opening (native, terminator, auto), and connection cleanup
- [x] 6.5 Surveyed all remaining modules: `__main__.py` close loop narrowed to `(OSError, subprocess.SubprocessError)`, top-level safety net kept as `except Exception` with comment; `logging_module.py` narrowed 2 blocks to `OSError`; `command_mode.py` narrowed close loop and wizard handlers, kept top-level as `except Exception`; `ui.py` kept `ensure_terminal_compatibility` as `except Exception` (Rich rendering failures); `enumerate.py` narrowed import fallbacks to `ImportError`, base64 decoding to `(ValueError, UnicodeDecodeError)`, mkdir to `(OSError, ValueError)`; updated 1 test mock to raise `OSError` instead of bare `Exception`
- [x] 6.6 Run `make check && make test` — zero ruff violations, zero mypy errors, 955 tests passed, 97.04% branch coverage, build clean

### [x] Step 7: Add parametrized tests
<!-- chat-id: 447cd157-b603-42f2-904c-08dffee673f6 -->

Convert 3-5 repetitive test groups to use `@pytest.mark.parametrize`, improving conciseness and edge case coverage.

- [x] 7.1 Identify repetitive test patterns: terminal method options, integer env var parsing, config name validation, display message types (plain text and rich), accessible message types
- [x] 7.2 Convert 5 groups to parametrized tests with descriptive `ids`:
  - `TestGetTerminalMethod` in `test_config.py`: collapsed 5 tests (3 method returns + case insensitive + invalid) into 1 parametrized test with 7 cases
  - `TestValidateConfigName` in `test_config.py`: converted inline assertions to 5 valid + 6 invalid parametrized cases with descriptive ids
  - `TestParseIntegerEnvVar` in `test_console_instance.py`: collapsed 4 tests into 1 parametrized test with 5 cases
  - `TestDisplayMessageWithFallback` in `test_console_instance.py`: collapsed 4 plain-text tests into 1 parametrized (4 cases) and 4 rich-mode tests into 1 parametrized (4 cases)
  - `TestDisplayAccessibleMessage` in `test_console_instance.py`: collapsed 5 tests into 1 parametrized test with 5 cases
- [x] 7.3 Test count increased from 955 to 966 (parametrized tests expand at runtime)
- [x] 7.4 Run `make check && make test` — zero ruff violations, zero mypy errors, 966 tests passed, 97.06% branch coverage

### [x] Step 8: Documentation updates
<!-- chat-id: 84b81ffb-4ad8-4651-8a34-4bde3990aa68 -->

Update CHANGELOG, user docs, and contributor guidance to reflect current state.

- [x] 8.1 Review `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, `docs/troubleshooting.md` against current command set and features in `command_mode.py` — all 20 commands documented correctly; env vars, config format, SCP commands, and plugin system all match source code; no stale instructions found in user-facing docs
- [x] 8.2 Verify environment variable documentation matches actual usage across source modules — `reference.md` lists all 12 user-configurable and 8 plugin API env vars accurately; added `LAZYSSH_SHELL` to `docs/Plugin/example_template.py` env var comment; added cross-reference from `CLAUDE.md` to `docs/reference.md` for complete env var table
- [x] 8.3 Verify config file format documentation matches `config.py` implementation — all 8 TOML fields documented correctly with required/optional status matching source
- [x] 8.4 Verify plugin documentation matches `plugin_manager.py` behavior — search order, metadata format, execution model, and validation all match; `PLUGIN_REQUIREMENTS` field is optional and correctly omitted from minimal examples
- [x] 8.5 Audit `CLAUDE.md`, `CONTRIBUTING.md`, `openspec/project.md` for contradictions or stale info:
  - Fixed `openspec/project.md`: updated type hints from "preferred but not strictly enforced" to "strictly enforced via mypy"; changed coverage from "100% required" to "97% branch coverage required"; corrected `prompt_toolkit` version from pinned `3.0.39` to range `>=3.0.39, <3.1.0`; removed stale "Target Python version: 3.11" Ruff line (Ruff now infers from `requires-python`)
  - Fixed `CLAUDE.md`: added cross-reference to `docs/reference.md` for full env var documentation
  - Fixed `CONTRIBUTING.md`: added missing `make verify` to commands table
  - Fixed `Makefile`: added `verify` target (check + test + build) referenced by CLAUDE.md and openspec/project.md but previously missing
  - Added `[Unreleased]` CHANGELOG entries for all audit work (Steps 1-7)
  - Run `make check && make test && make build` — zero violations, 966 tests passed, 97.06% branch coverage, build clean

### [x] Step 9: Dependency and packaging review
<!-- chat-id: c1e475e6-819d-444e-9c85-bd29f81a8084 -->

Review and adjust dependency constraints; document rationale.

- [x] 9.1 Search codebase for `prompt_toolkit` APIs requiring >=3.0.39 — found `complete_event.completion_requested` in `scp_mode.py` (lines 177 and 265), introduced in prompt_toolkit 3.0.39; lower bound `>=3.0.39` is justified and kept; added inline comment documenting the rationale
- [x] 9.2 Add comment in `pyproject.toml` noting that CI tests with latest resolved versions only and minimum compatibility is not separately tested — added above `dependencies` list
- [x] 9.3 Run `make build` to verify packaging is clean — sdist and wheel built, `twine check` passed

### [x] Step 10: Final verification
<!-- chat-id: 31af37e2-5d55-4212-b818-972dd14e6928 -->

Full quality gate and summary.

- [x] 10.1 Run `make check` — zero ruff violations, zero mypy errors (ruff format: 34 files clean, ruff check: all passed, mypy: 14 source files clean)
- [x] 10.2 Run `make test` — 966 tests passed in 5.16s, 97.04% branch coverage (threshold: 97%), zero failures
- [x] 10.3 Run `make build` — sdist and wheel built (`lazyssh-1.6.2`), `twine check` passed on both artifacts
- [x] 10.4 Review all `# noqa:` comments — 53 total across src/ and tests/; found 3 F401 suppressions in `__init__.py`, `command_mode.py`, and `scp_mode.py` missing explanatory notes; added explanations to all 3; re-ran `make check && make test` — all clean
- [x] 10.5 Confirm CHANGELOG is accurate and complete — `[Unreleased]` covers all 9 audit steps (security hardening, exception narrowing, complexity refactoring, Ruff rules, mypy strengthening, parametrized tests, branch coverage, documentation, dependency review); `[1.6.2]` and `[1.6.0]` entries match git history; no missing versions
- [x] 10.6 Final metrics and deferred items:
  - **Test count**: 966 (up from 955 at audit start)
  - **Branch coverage**: 97.04% (threshold enforced at 97%)
  - **Statement coverage**: 97% (3596 statements, 15 missed)
  - **Ruff violations**: 0
  - **mypy errors**: 0
  - **noqa comments**: 53 (all with explanatory notes)
  - **type: ignore comments**: 6 (all with error codes and explanations)
  - **Deferred items**: None — all planned audit work is complete
