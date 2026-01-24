## 1. Add Ruff Configuration

- [x] 1.1 Add `[tool.ruff]` configuration to pyproject.toml
- [x] 1.2 Add `[tool.ruff.lint]` with appropriate rule selection
- [x] 1.3 Add `[tool.ruff.format]` for formatting options
- [x] 1.4 Run `ruff check --fix src tests` to auto-fix issues
- [x] 1.5 Run `ruff format src tests` to normalize formatting
- [x] 1.6 Verify no ruff errors remain

## 2. Simplify Hatch Configuration

- [x] 2.1 Replace tool dependencies in default env (remove black, isort, flake8, pylint, pyupgrade; add ruff)
- [x] 2.2 Remove `[tool.hatch.envs.test]` section
- [x] 2.3 Remove `[tool.hatch.envs.lint]` section
- [x] 2.4 Remove `[tool.hatch.envs.typing]` section
- [x] 2.5 Rewrite default scripts to use ruff commands
- [x] 2.6 Remove `[tool.black]` and `[tool.isort]` sections
- [x] 2.7 Update pytest config to show coverage by default

## 3. Update mise Configuration

- [x] 3.1 Add ruff tool to `.mise.toml`
- [x] 3.2 Verify mise installs ruff correctly

## 4. Simplify Makefile

- [x] 4.1 Remove redundant targets (dev-install, coverage, verify, pre-commit, dist, publish-test, watch, deps-check, env-info, typecheck, all)
- [x] 4.2 Update `fmt` target to use ruff format
- [x] 4.3 Update `fix` target to use ruff check --fix + ruff format
- [x] 4.4 Update `lint` target to use ruff check
- [x] 4.5 Update `test` target to show coverage by default
- [x] 4.6 Update `check` target to use ruff + mypy
- [x] 4.7 Update help text
- [x] 4.8 Verify all Make targets work

## 5. Update CI Workflows

- [x] 5.1 Update python-lint.yml to use ruff
- [x] 5.2 Update python-publish.yml to use ruff
- [x] 5.3 Simplify CI steps (fewer tool invocations)

## 6. Remove Obsolete Files

- [x] 6.1 Remove `.flake8` config file
- [x] 6.2 Remove `pre-commit-check.sh`

## 7. Update Documentation

- [x] 7.1 Update README.md with new commands
- [x] 7.2 Update CONTRIBUTING.md with ruff workflow
- [x] 7.3 Update docs/maintainers.md
- [x] 7.4 Update CLAUDE.md
- [x] 7.5 Update openspec/project.md tech stack

## 8. Verification

- [x] 8.1 Run `make check` - all passes
- [x] 8.2 Run `make test` - all tests pass, coverage displayed
- [x] 8.3 Run `make build` - package builds
- [x] 8.4 Verify wheel installs and runs correctly
