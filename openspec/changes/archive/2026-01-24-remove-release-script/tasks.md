# Tasks: Remove Redundant Release Script

## Overview

Remove `scripts/release.py` and `make release` since Hatch handles versioning natively.

## Tasks

### Phase 1: Delete Redundant Files

- [x] 1.1 Delete `scripts/release.py`
- [x] 1.2 Remove empty `scripts/` directory

### Phase 2: Update Makefile

- [x] 2.1 Remove `release` from `.PHONY` targets
- [x] 2.2 Remove `make release` help text
- [x] 2.3 Remove `release:` target definition
- [x] 2.4 Update `make version` help text to clarify it shows version via Hatch

### Phase 3: Validation

- [x] 3.1 Run `make check` to ensure quality checks pass
- [x] 3.2 Run `make help` to verify updated help text
- [x] 3.3 Verify `hatch version` works correctly
- [x] 3.4 Verify `make version` works correctly

## Dependencies

None - this is a cleanup task with no dependencies on other changes.

## Parallelization

- Phase 1 tasks can run in parallel with Phase 2 tasks
- Phase 3 must run after Phases 1 and 2 complete
