## Why
- Current docs are sprawling across nine Markdown files with significant duplication between README, user guide, and command reference.
- Several instructions (e.g., `lazyssh --config`) drifted from actual CLI behaviour and confuse readers.
- Specs require layered documentation that is easy to scan; the existing material overwhelms users and slows updates.

## What Changes
- Reorganize user-facing docs into a concise set: refreshed README, `docs/getting-started.md`, `docs/reference.md`, `docs/guides.md`, trimmed `docs/troubleshooting.md`, and `docs/maintainers.md`.
- Remove or replace redundant files (`docs/user-guide.md`, `docs/commands.md`, `docs/scp-mode.md`, `docs/tunneling.md`, `docs/development.md`, `docs/publishing.md`, `docs/logging_module.md`, and `docs/Plugin/plugins.md`).
- Update documentation content to match current code (command syntax, environment variables, config workflow) and cross-link the new structure.
- Update specs (`user-documentation`, `connection-config`) so requirements reference the streamlined layout and accurate `--config` usage.

## Impact
- Clear documentation path for new users, advanced users, and maintainers with minimal overlap.
- Lower maintenance effort thanks to a single command reference and centralized environment variable list.
- Specs stay aligned with the streamlined docs, avoiding future drift.
