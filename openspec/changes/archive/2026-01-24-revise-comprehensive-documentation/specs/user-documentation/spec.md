## MODIFIED Requirements

### Requirement: Documentation Accuracy

All documentation SHALL reflect current command syntax, feature availability, and system behaviour.

#### Scenario: README commands execute as written
- **WHEN** a user copies any command example from `README.md`
- **THEN** the command runs successfully with the current CLI (e.g. explicit `--config /path` usage)

#### Scenario: Reference tables match implementation
- **WHEN** a maintainer reviews `docs/reference.md`
- **THEN** every listed command, flag, environment variable, and config key matches names found in `src/lazyssh`

#### Scenario: Project.md reflects current implementation
- **WHEN** a maintainer reviews `openspec/project.md`
- **THEN** all listed tools, libraries, and versions match `pyproject.toml` and `.mise.toml`
- **AND** all documented commands match the current Makefile and Hatch scripts
- **AND** the testing strategy section matches the actual test infrastructure

## ADDED Requirements

### Requirement: Project Context Maintenance

The openspec/project.md file SHALL be updated whenever significant implementation changes occur to build tooling, test infrastructure, or plugin capabilities.

#### Scenario: Build tool changes documented
- **WHEN** build tooling (Hatch, mise, pre-commit) is added or modified
- **THEN** project.md is updated to reflect the new tools and commands
- **AND** the change is made as part of the same change proposal or immediately following implementation

#### Scenario: Test infrastructure changes documented
- **WHEN** test infrastructure (coverage requirements, HTML reports, CI changes) is modified
- **THEN** project.md Testing Strategy section is updated
- **AND** relevant Makefile targets and Hatch scripts are documented

#### Scenario: Plugin enhancements documented
- **WHEN** built-in plugin capabilities are enhanced
- **THEN** project.md Plugin Architecture section is updated
- **AND** new command flags or output formats are described
