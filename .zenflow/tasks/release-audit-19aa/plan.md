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

### [ ] Step 8: Documentation updates

Update CHANGELOG, user docs, and contributor guidance to reflect current state.

- [ ] 8.1 Review `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, `docs/troubleshooting.md` against current command set and features in `command_mode.py`; update stale instructions for v1.6.x changes
- [ ] 8.2 Verify environment variable documentation matches actual usage across source modules
- [ ] 8.3 Verify config file format documentation matches `config.py` implementation
- [ ] 8.4 Verify plugin documentation matches `plugin_manager.py` behavior
- [ ] 8.5 Audit `CLAUDE.md`, `CONTRIBUTING.md`, `openspec/project.md` for contradictions or stale info; ensure distinct purpose for each; add cross-references where content overlaps

### [ ] Step 9: Dependency and packaging review

Review and adjust dependency constraints; document rationale.

- [ ] 9.1 Search codebase for `prompt_toolkit` APIs requiring >=3.0.39; if none found, relax lower bound to `>=3.0.36` or broader; keep `<3.1.0` upper bound; add comment documenting reasoning
- [ ] 9.2 Add comment in `pyproject.toml` noting that CI tests with latest resolved versions only and minimum compatibility is not separately tested
- [ ] 9.3 Run `make build` to verify packaging is clean

### [ ] Step 10: Final verification

Full quality gate and summary.

- [ ] 10.1 Run `make check` — zero ruff violations, zero mypy errors
- [ ] 10.2 Run `make test` — all tests pass, coverage threshold enforced
- [ ] 10.3 Run `make build` — package builds and `twine check` passes
- [ ] 10.4 Review all `# noqa:` comments added during audit to confirm each has an explanatory note
- [ ] 10.5 Confirm CHANGELOG is accurate and complete through v1.6.2
- [ ] 10.6 Record final test count, coverage percentage, and any deferred items in this plan
