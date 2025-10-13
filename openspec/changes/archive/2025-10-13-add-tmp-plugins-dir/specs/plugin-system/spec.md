# plugin-system Delta Specification

## MODIFIED Requirements

### Requirement: Plugin Discovery
The system SHALL automatically discover plugins from the following locations in order of precedence (first match wins):

1. Directories provided via `LAZYSSH_PLUGIN_DIRS` (left to right)
2. Default user directory: `~/.lazyssh/plugins`
3. Runtime directory: `/tmp/lazyssh/plugins`
4. Packaged built-in directory: `lazyssh/plugins/` (installed with the package)

#### Scenario: Runtime directory included
- **WHEN** plugin discovery runs
- **THEN** the `/tmp/lazyssh/plugins` directory SHALL be included in the search order as specified
- **AND** non-existent directories SHALL be ignored without error

### Requirement: Plugin Directory Creation
The system SHALL ensure the existence of `/tmp/lazyssh/plugins` at program startup.

#### Scenario: Create runtime plugin directory
- **WHEN** the program starts
- **THEN** the directory `/tmp/lazyssh/plugins` SHALL be created if it does not exist
- **AND** permissions SHALL be set to `0700`
- **AND** failures SHALL be logged without crashing the application

### Requirement: Discovery Safety
Discovery SHALL avoid following symlinks outside declared plugin directories and SHALL handle broken symlinks gracefully without crashing. The search MUST be restricted to configured directories and only consider top-level files by default.

#### Scenario: Symlink outside base is ignored
- **WHEN** a symlink points outside a configured plugin directory
- **THEN** it SHALL be skipped and not loaded


