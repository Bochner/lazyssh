## ADDED Requirements

### Requirement: AI Assistant Quick Reference

CLAUDE.md SHALL serve as a concise quick reference for AI coding assistants, documenting essential development commands and quality gates without duplicating detailed information available in openspec/project.md or CONTRIBUTING.md.

#### Scenario: AI assistant reads CLAUDE.md

- **WHEN** an AI assistant reads CLAUDE.md at conversation start
- **THEN** it finds essential build commands (make fmt, make check, make test)
- **AND** it finds the quality gate requirement (make check must pass before commits)
- **AND** it finds cross-references to detailed documentation for deeper context

#### Scenario: Tool version management documented

- **WHEN** an AI assistant needs to understand tool versioning
- **THEN** CLAUDE.md documents that mise auto-activates correct Python and Ruff versions
- **AND** it references .mise.toml as the configuration source

#### Scenario: No duplication with project.md

- **WHEN** CLAUDE.md content is compared to openspec/project.md
- **THEN** CLAUDE.md provides summaries and quick commands
- **AND** detailed conventions, patterns, and rationale remain in project.md
- **AND** CLAUDE.md links to project.md for comprehensive information
