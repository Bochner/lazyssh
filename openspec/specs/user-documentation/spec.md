# user-documentation Specification

## Purpose
Define expectations for LazySSH's user-facing documentation structure, accuracy, completeness, and supporting GitHub issue templates.
## Requirements
### Requirement: Documentation Structure
User-facing documentation SHALL remain layered into quick start, guided journey, reference, and specialised guides, with each layer mapped to a single maintained file.

#### Scenario: Quick start stays in README
- **WHEN** a new user reads `README.md`
- **THEN** they see a concise overview plus installation & first-run steps
- **AND** the README links directly to the deeper guides in `docs/`

#### Scenario: Guided journey lives in getting-started doc
- **WHEN** a user opens `docs/getting-started.md`
- **THEN** they find step-by-step workflows for connections, tunnels, file transfers, and saving configs without reference duplication from other files

#### Scenario: Reference and advanced material are isolated
- **WHEN** a user consults `docs/reference.md` or `docs/guides.md`
- **THEN** `docs/reference.md` provides scannable command/environment tables
- **AND** `docs/guides.md` hosts advanced workflows (tunnelling, SCP, automation) without repeating quick-start content

### Requirement: Documentation Accuracy
All documentation SHALL reflect current command syntax, feature availability, and system behaviour.

#### Scenario: README commands execute as written
- **WHEN** a user copies any command example from `README.md`
- **THEN** the command runs successfully with the current CLI (e.g. explicit `--config /path` usage)

#### Scenario: Reference tables match implementation
- **WHEN** a maintainer reviews `docs/reference.md`
- **THEN** every listed command, flag, environment variable, and config key matches names found in `src/lazyssh`

### Requirement: Documentation Completeness
All user-facing features present in the current release SHALL be documented with usage examples.

#### Scenario: Recent features are documented
- **WHEN** a feature is added or changed in a release
- **THEN** documentation is updated to describe the feature before or concurrent with release

#### Scenario: Breaking changes are noted
- **WHEN** a command or behavior changes in a breaking way
- **THEN** documentation clearly indicates the old behavior and migration path

### Requirement: Documentation Conciseness
User-facing documentation SHALL prioritize clarity and scannability over comprehensiveness, moving technical details to developer documentation.

#### Scenario: User-facing docs are scannable
- **WHEN** a user scans a user-facing documentation file
- **THEN** they can identify relevant sections within 2 minutes using headings and examples

#### Scenario: Implementation details are separated
- **WHEN** a user reads user-facing documentation
- **THEN** they do not encounter internal implementation details, source code references, or development-specific information

### Requirement: Documentation Maintainability
Documentation SHALL avoid redundancy and maintain a single source of truth for each concept.

#### Scenario: Command syntax centralised in one place
- **WHEN** command syntax needs updating
- **THEN** only `README.md` (for the quick example) and `docs/reference.md` require edits, with other docs linking instead of duplicating syntax

#### Scenario: Environment variables have one canonical list
- **WHEN** a new UI or plugin environment variable is introduced
- **THEN** it is documented exactly once in the environment table within `docs/reference.md`

### Requirement: GitHub Issue Templates
The project SHALL provide user-friendly GitHub issue templates that facilitate bug reports and feature requests with minimal friction while maintaining sufficient information quality for maintainers.

#### Scenario: Bug report submission
- **WHEN** a user wants to report a bug
- **THEN** they can complete the bug report template with only essential information (description, steps to reproduce, environment details)
- **AND** optional fields are clearly marked as such
- **AND** field descriptions are concise and helpful

#### Scenario: Feature request submission
- **WHEN** a user wants to request a new feature
- **THEN** they can complete the feature request template with core information (description, use case)
- **AND** priority and alternatives are optional fields
- **AND** the template encourages contribution without requiring it

#### Scenario: Template usability
- **WHEN** users interact with issue templates
- **THEN** the templates feel approachable rather than overwhelming
- **AND** required fields are kept to the minimum necessary for triage
- **AND** field descriptions use clear, friendly language

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
