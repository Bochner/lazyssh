## Why

Multiple significant changes have been implemented over the past months without corresponding updates to `openspec/project.md`. The project.md is the authoritative source of truth for the tech stack, conventions, and domain context, but it currently lacks documentation of:

1. **Build System Modernization**: Hatch + mise adoption, pre-commit hooks, pytest-html/coverage HTML reports, `artifacts/` directory, and `hatch test` command are not documented
2. **Test Coverage Requirements**: 100% test coverage requirement and HTML report generation are missing
3. **Pre-commit Hooks**: The pre-commit workflow, hooks configuration, and Makefile targets (`pre-commit-install`, `pre-commit`) are not mentioned
4. **Enumerate Plugin Enhancement**: The batched script execution, priority findings, JSON/log persistence to connection workspace, and `--json` flag are not described
5. **Python Version Support**: `pyproject.toml` now supports 3.11/3.12/3.13 but project.md only mentions 3.11
6. **Tool Version Changes**: `.mise.toml` now includes `pre-commit = "latest"` in addition to Python and Ruff

Secondary documentation files (CLAUDE.md, CONTRIBUTING.md) were updated during the Hatch/mise modernization but may have minor inconsistencies with current implementation.

## What Changes

- **Update openspec/project.md** comprehensively:
  - Add Hatch test command and HTML reporting to Build & Development Tools section
  - Add pre-commit hooks to development workflow
  - Document `artifacts/` directory for test/coverage reports
  - Update Python version to mention 3.12/3.13 support
  - Add pre-commit to mise tools list
  - Document enumerate plugin enhancements (batched execution, priority findings, JSON export)
  - Add 100% test coverage as a quality gate
  - Update Testing Strategy section with HTML reports

- **Update openspec/specs/user-documentation/spec.md** with new requirements:
  - Add requirement for project.md accuracy
  - Add requirement for documenting test/coverage infrastructure

- **Verify consistency** in:
  - CLAUDE.md (already updated but verify against project.md)
  - CONTRIBUTING.md (already updated but verify against project.md)

## Impact

- Affected specs: `user-documentation`
- Affected code/docs: `openspec/project.md`, possibly minor sync updates to `CLAUDE.md`, `CONTRIBUTING.md`
- No code changes required - documentation only
