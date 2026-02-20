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

### [ ] Step 1: Low-risk configuration changes

Apply safe, config-only changes that reduce risk and enforce existing standards. No behavioral code changes.

- [ ] 1.1 Add `fail_under = 100` to `[tool.coverage.report]` in `pyproject.toml` (Req 3.1)
- [ ] 1.2 Add `branch = true` to `[tool.coverage.run]` in `pyproject.toml`; run `make test` to verify branch coverage level; adjust `fail_under` if branch coverage is below 100% (Req 3.1)
- [ ] 1.3 Remove `target-version = "py311"` from `[tool.ruff]` in `pyproject.toml`; verify Ruff infers from `requires-python` by running `ruff check src tests` (Req 5.3)
- [ ] 1.4 Add missing CHANGELOG entries for v1.6.1 and v1.6.2 based on `git log` between those releases (Req 4.1)
- [ ] 1.5 Run `make check && make test && make build` to verify no regressions

### [ ] Step 2: Security hardening — remove `shell=True`

Eliminate command injection risk by converting subprocess calls from string commands to argument lists.

- [ ] 2.1 In `src/lazyssh/ssh.py`, refactor `create_tunnel()` (~line 213-218): convert the f-string `cmd` to a list of arguments and remove `shell=True` from `subprocess.run()`
- [ ] 2.2 In `src/lazyssh/ssh.py`, refactor `close_tunnel()` (~line 269-274): same conversion — list-based args, remove `shell=True`
- [ ] 2.3 Update tests in `tests/` that assert on the subprocess `cmd` argument for tunnel operations: change expected values from string commands to argument lists; verify `shell=True` is no longer passed
- [ ] 2.4 Run `make check && make test` to verify all tests pass and coverage holds

### [ ] Step 3: Expand Ruff rules and add per-file ignores

Enable security (`S`), pytest-style (`PT`), and return-statement (`RET`) Ruff rules. Triage and resolve all findings.

- [ ] 3.1 In `pyproject.toml`, add `"S"`, `"PT"`, `"RET"` to `[tool.ruff.lint] select`
- [ ] 3.2 Add `[tool.ruff.lint.per-file-ignores]` section: `"tests/*" = ["S101", "S108"]`
- [ ] 3.3 Run `ruff check src tests` and triage all new findings:
  - Fix genuine issues
  - Add `# noqa:` with explanatory comments for intentional patterns (e.g., `S603` for controlled subprocess calls, `S607` for `ssh`/`scp` partial paths, `S108` for `/tmp/lazyssh`)
- [ ] 3.4 Fix any PT-rule violations (fixture style, `pytest.raises` usage, parametrize format)
- [ ] 3.5 Fix any RET-rule violations (unnecessary else after return, etc.)
- [ ] 3.6 Run `make check && make test` to verify zero violations and all tests pass

### [ ] Step 4: Strengthen mypy configuration

Tighten mypy settings incrementally. Move from global `ignore_missing_imports` to per-module overrides and enable stricter type checking.

- [ ] 4.1 In `pyproject.toml`, add `disallow_untyped_defs = true`, `strict_equality = true`, `no_implicit_optional = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true` to `[tool.mypy]`
- [ ] 4.2 Add `[[tool.mypy.overrides]]` for third-party modules (`paramiko`, `pexpect`, `prompt_toolkit`, `art`, `tomli_w`, `colorama`) with `ignore_missing_imports = true`
- [ ] 4.3 Remove the global `ignore_missing_imports = true`
- [ ] 4.4 Run `mypy src` and fix all new errors (add return type annotations, fix type narrowing issues)
- [ ] 4.5 Resolve all `# type: ignore` comments: add error codes and explanatory comments per spec section 2.3
- [ ] 4.6 Run `make check && make test` to verify zero mypy errors and all tests pass

### [ ] Step 5: Refactor high-complexity functions

Break down the four highest-complexity functions into smaller, focused methods. Preserve all existing behavior — tests must pass without modification.

- [ ] 5.1 Refactor `LazySSHCompleter.get_completions` in `command_mode.py`: extract per-command completion handlers into separate private methods, dispatch via a handler dictionary
- [ ] 5.2 Refactor `SCPModeCompleter.get_completions` in `scp_mode.py`: same pattern — extract per-command completion handlers into private methods
- [ ] 5.3 Refactor `CommandMode.cmd_help` in `command_mode.py`: extract to a data-driven approach using a dictionary mapping topic names to help text content
- [ ] 5.4 Refactor `SCPMode.cmd_mget` in `scp_mode.py`: split into `_mget_discover_files()`, `_mget_calculate_size()`, and `_mget_download()` helper methods
- [ ] 5.5 Run `make check && make test` after each refactor to verify behavior preservation and coverage maintenance

### [ ] Step 6: Tighten exception handling

Add logging to silent exception handlers and narrow broad `except Exception` catches where the expected failure type is clear.

- [ ] 6.1 In `scp_mode.py` (lines ~216, 243, 318): add `SCP_LOGGER.debug(...)` to `except Exception: pass` blocks and narrow to `OSError` or `subprocess.SubprocessError` where applicable
- [ ] 6.2 In `plugin_manager.py` (line ~597): add `APP_LOGGER.debug(...)` to silent catch; narrow to `ValueError` / `OSError` for metadata parsing
- [ ] 6.3 In `config.py` (lines ~287, 367, 463): add debug logging before cleanup attempts; narrow to `tomllib.TOMLDecodeError` / `OSError` where applicable
- [ ] 6.4 In `ssh.py`: narrow broad catches in connection operations to `subprocess.SubprocessError` / `OSError` where the expected failure is clear
- [ ] 6.5 Survey remaining `except Exception` instances across all source modules; narrow where safe, leave with comment where genuinely unknown failures are possible
- [ ] 6.6 Run `make check && make test` to verify all tests pass and coverage holds

### [ ] Step 7: Add parametrized tests

Convert 3-5 repetitive test groups to use `@pytest.mark.parametrize`, improving conciseness and edge case coverage.

- [ ] 7.1 Identify repetitive test patterns: terminal method options, environment variable toggles, config validation edge cases, connection parameter combinations, command parsing variations
- [ ] 7.2 Convert the identified groups to parametrized tests using `@pytest.mark.parametrize` with descriptive `ids`
- [ ] 7.3 Verify test count is maintained or increased (parametrized tests expand at runtime)
- [ ] 7.4 Run `make test` to confirm all tests pass and coverage is maintained

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
