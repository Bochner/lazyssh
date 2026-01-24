## Why

The current build and development tooling uses setuptools with a manually-managed venv and Makefile, which is functional but outdated compared to modern Python standards. Hatch provides a unified, PEP-compliant build system with automatic virtual environment management, while mise-en-place (mise) offers polyglot tool version management replacing pyenv, nvm, and similar tools with a single configuration file.

## What Changes

- **BREAKING**: Remove setuptools-based build system in favor of Hatch (hatchling backend)
- **BREAKING**: Remove manual venv management from Makefile; Hatch manages environments automatically
- Replace `venv/` workflow with `hatch env` commands
- Add `.mise.toml` for Python version pinning and tool version management
- Convert `pyproject.toml` to use hatchling as build backend with Hatch environments
- Modernize Makefile to delegate to Hatch commands where appropriate
- Update pre-commit-check.sh to use Hatch environments
- Update GitHub Actions workflows to use mise for Python version management
- Update all documentation (README, CONTRIBUTING, maintainers guide, CLAUDE.md)
- Preserve all existing functionality and test coverage

## Impact

- Affected specs: None (build tooling is not spec'd)
- Affected code:
  - `pyproject.toml` - Major restructure for Hatch
  - `Makefile` - Significant rewrite to use Hatch
  - `.mise.toml` - New file
  - `pre-commit-check.sh` - Update for Hatch environments
  - `.github/workflows/python-lint.yml` - Use mise
  - `.github/workflows/python-publish.yml` - Use mise + Hatch build
  - `scripts/release.py` - May need minor updates for Hatch version management
  - `README.md` - Update install/dev instructions
  - `CONTRIBUTING.md` - Update dev setup instructions
  - `docs/maintainers.md` - Update dev workflow
  - `CLAUDE.md` - Update build commands reference
  - `openspec/project.md` - Update tech stack and conventions
