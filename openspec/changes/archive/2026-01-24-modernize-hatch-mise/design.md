## Context

LazySSH currently uses setuptools with a manual venv and extensive Makefile for build/dev operations. This approach works but:

1. Requires manual venv activation/management
2. Duplicates configuration across pyproject.toml, Makefile, and shell scripts
3. Uses an older Python packaging paradigm
4. Lacks reproducible tool versioning across developer machines and CI

**Hatch** is the modern Python project manager endorsed by the Python Packaging Authority (PyPA). It provides:
- Unified project management (build, test, publish)
- Automatic virtual environment management
- Built-in scripts/commands system
- PEP 517/518/621 compliant

**mise-en-place (mise)** is a polyglot tool version manager that:
- Replaces pyenv, nvm, rbenv, etc. with a single tool
- Uses a declarative `.mise.toml` configuration
- Supports automatic version switching per directory
- Works in CI environments with GitHub Actions

## Goals / Non-Goals

**Goals:**
- Adopt Hatch as the primary build system and project manager
- Use mise for Python version pinning (3.11+)
- Preserve all existing Make targets as compatibility layer
- Maintain backward compatibility for developers not using mise (fallback to system Python 3.11+)
- Simplify contributor onboarding
- Improve CI reproducibility

**Non-Goals:**
- Changing the source code structure (src layout stays)
- Modifying any runtime behavior
- Changing the package distribution format (still wheel + sdist)
- Forcing mise adoption (optional enhancement)

## Decisions

### Decision 1: Hatchling as build backend

**What**: Replace setuptools with hatchling in `[build-system]`

**Why**: Hatchling is faster, simpler, and designed for modern Python. It uses the same configuration format (pyproject.toml) and produces identical wheels.

**Alternatives considered**:
- PDM: Good but less adoption than Hatch
- Poetry: Heavier, non-standard lock file, different dependency resolution
- Flit: Simpler but less flexible for complex projects
- Keep setuptools: Works but increasingly legacy

### Decision 2: Hatch environments for dev workflows

**What**: Define Hatch environments for `dev`, `test`, `lint`, `typing` instead of single venv

**Why**:
- Hatch auto-manages these environments
- Cleaner separation of concerns
- No need to manually activate venvs
- `hatch run <env>:<command>` pattern

**Structure**:
```toml
[tool.hatch.envs.default]
dependencies = [...runtime deps...]

[tool.hatch.envs.dev]
dependencies = [...dev deps...]

[tool.hatch.envs.test]
dependencies = ["pytest", "pytest-cov"]

[tool.hatch.envs.lint]
dependencies = ["black", "isort", "flake8", "pylint"]

[tool.hatch.envs.typing]
dependencies = ["mypy"]
```

### Decision 3: mise for tool versioning

**What**: Add `.mise.toml` to pin Python version and optionally other tools

**Why**:
- Single source of truth for Python version
- CI and local dev use same version
- Automatic version switching when entering project directory
- Lighter than pyenv/asdf

**Configuration**:
```toml
[tools]
python = "3.11"
```

### Decision 4: Makefile as compatibility layer

**What**: Keep Makefile but rewrite targets to call Hatch

**Why**:
- Existing developers expect `make test`, `make lint`
- Makefile provides discoverable interface
- Delegates to Hatch for actual work

**Mapping**:
| Old | New |
|-----|-----|
| `make install` | `hatch env create` |
| `make dev-install` | `hatch env create dev` |
| `make test` | `hatch run test:pytest` |
| `make lint` | `hatch run lint:all` |
| `make fmt` | `hatch run lint:fmt` |
| `make check` | `hatch run check` |
| `make build` | `hatch build` |

### Decision 5: Version management with Hatch

**What**: Use Hatch's version source from `src/lazyssh/__init__.py`

**Why**:
- Single source of truth for version
- `hatch version` command for bumping
- No need for custom release.py (or minimal wrapper)

**Configuration**:
```toml
[tool.hatch.version]
path = "src/lazyssh/__init__.py"
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Developers unfamiliar with Hatch | Makefile compatibility layer, updated docs |
| mise not installed | Fallback to system Python; mise is optional |
| CI changes could break | Test in PR before merge |
| Different behavior from setuptools | Run full test suite, verify wheel contents |

## Migration Plan

### Phase 1: Add mise configuration
1. Add `.mise.toml` with Python 3.11
2. Update `.gitignore` for Hatch directories
3. Test locally

### Phase 2: Convert pyproject.toml to Hatch
1. Change build-system to hatchling
2. Add Hatch environment configurations
3. Configure version source
4. Add Hatch scripts for common operations

### Phase 3: Update Makefile
1. Rewrite targets to use Hatch commands
2. Preserve all existing target names
3. Add new Hatch-specific targets
4. Update help text

### Phase 4: Update CI workflows
1. Add mise setup action
2. Update Python setup to use mise
3. Change build/test commands to Hatch

### Phase 5: Update documentation
1. README.md - install instructions
2. CONTRIBUTING.md - dev setup
3. docs/maintainers.md - dev workflow
4. CLAUDE.md - command reference
5. openspec/project.md - tech stack

### Phase 6: Clean up
1. Remove pre-commit-check.sh (replaced by Hatch scripts)
2. Update .gitignore
3. Verify release workflow

### Rollback

If issues arise:
1. Revert pyproject.toml to setuptools
2. Restore original Makefile
3. Remove .mise.toml

Since this is infrastructure, rollback is straightforward.

## Open Questions

1. **Pre-commit hooks**: Should we integrate pre-commit with Hatch or keep separate?
   - Recommendation: Keep pre-commit separate but update config to use Hatch environments

2. **pytest-watch**: Currently installed separately; should it be in test env?
   - Recommendation: Add to dev environment for development convenience

3. **release.py**: Keep custom script or use `hatch version`?
   - Recommendation: Use `hatch version` directly, update docs with new workflow
