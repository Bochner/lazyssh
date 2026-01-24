## Why

CLAUDE.md serves as quick reference for AI assistants but currently lacks mention of mise for tool version management, doesn't emphasize the quality gate workflow, and duplicates content already available in project.md and CONTRIBUTING.md. The file should be streamlined to focus on what AI must always do while pointing to authoritative sources for details.

## What Changes

- Add mise tooling section explaining automatic tool version activation
- Add quality gate workflow section emphasizing `make check` before commits
- Streamline existing content to avoid duplication with project.md
- Add cross-references to detailed documentation (project.md, CONTRIBUTING.md)
- Consolidate environment variables into grouped categories

## Impact

- Affected specs: None (documentation-only change)
- Affected code: `CLAUDE.md` only
