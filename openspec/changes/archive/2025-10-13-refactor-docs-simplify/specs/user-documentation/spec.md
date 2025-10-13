# user-documentation Delta Specification

## MODIFIED Requirements
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

### Requirement: Documentation Maintainability
Documentation SHALL avoid redundancy and maintain a single source of truth for each concept.

#### Scenario: Command syntax centralised in one place
- **WHEN** command syntax needs updating
- **THEN** only `README.md` (for the quick example) and `docs/reference.md` require edits, with other docs linking instead of duplicating syntax

#### Scenario: Environment variables have one canonical list
- **WHEN** a new UI or plugin environment variable is introduced
- **THEN** it is documented exactly once in the environment table within `docs/reference.md`
