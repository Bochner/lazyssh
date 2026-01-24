# Proposal: Remove Redundant Release Script

## Summary

Remove `scripts/release.py` and the `make release` target since Hatch now provides native version management via `hatch version`. This cleanup removes redundant tooling and simplifies the release workflow.

## Motivation

After the recent modernization to Hatch, the codebase has two ways to bump versions:

1. **`hatch version X.Y.Z`** - Native Hatch command that directly updates `src/lazyssh/__init__.py`
2. **`scripts/release.py`** - A wrapper script that calls `hatch version` internally

The wrapper script adds no value over calling `hatch version` directly. The `make release` target already uses `hatch version` directly (not the script), making the script truly orphaned.

## Scope

### Files to Delete
- `scripts/release.py` - Redundant wrapper script

### Files to Modify
- `Makefile` - Remove `make release` target and update help text
- `docs/maintainers.md` - Already correct (uses `hatch version`)
- `CONTRIBUTING.md` - Already correct (uses `hatch version`)
- `CLAUDE.md` - Already correct (uses `hatch version`)
- `openspec/project.md` - Already correct (uses `hatch version`)
- `openspec/specs/build-system/spec.md` - Remove any reference to release script if present

### Verification
- All documentation already recommends `hatch version` as the primary method
- No code imports or references `scripts/release.py`
- The `make release` target in Makefile already uses `hatch version` directly

## Changes

### 1. Delete `scripts/release.py`

The script is a thin wrapper that:
- Validates version format (Hatch does this)
- Calls `hatch version` (redundant)
- Prints next steps (these are documented elsewhere)

### 2. Update Makefile

Remove the `release` target and its help text. The `make version` target remains for viewing the current version.

**Current help text:**
```
Release:
  make build      Build package
  make clean      Clean artifacts
  make version    Show version
  make release    Version bump workflow
  make publish    Publish to PyPI
```

**Updated help text:**
```
Release:
  make build      Build package
  make clean      Clean artifacts
  make version    Show version (hatch version)
  make publish    Publish to PyPI
```

### 3. Remove Empty Scripts Directory

After deleting `release.py`, the `scripts/` directory will be empty and should be removed.

## Non-Changes

The following files are already correct and need no modification:
- `docs/maintainers.md` - Uses `hatch version 1.2.3`
- `CONTRIBUTING.md` - Uses `hatch version` commands
- `CLAUDE.md` - Uses `hatch version X.Y.Z`
- `openspec/project.md` - Uses `hatch version X.Y.Z`
- `openspec/specs/build-system/spec.md` - Defines `hatch version` as the canonical method

## Risks

**Low risk.** The script is not imported by any code, not referenced in CI, and not documented as the primary method anywhere.

## Alternatives Considered

1. **Keep the script as convenience** - Rejected because `hatch version` is simpler and already documented everywhere
2. **Add features to the script** - Rejected because it duplicates Hatch functionality

## Success Criteria

- [x] `scripts/release.py` deleted
- [x] `scripts/` directory removed (empty)
- [x] `make release` target removed from Makefile
- [x] Makefile help text updated
- [x] `make check` passes
- [x] `hatch version` continues to work
