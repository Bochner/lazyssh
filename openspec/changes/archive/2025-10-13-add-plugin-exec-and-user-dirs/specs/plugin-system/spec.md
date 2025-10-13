## ADDED Requirements
### Requirement: User Plugin Directories
LazySSH SHALL support loading plugins from user-defined directories in addition to packaged built-ins.

#### Scenario: Default user plugin directory
- **WHEN** no environment override is provided  
- **THEN** LazySSH SHALL include `~/.lazyssh/plugins` in its discovery search paths  
- **AND** discover `.py` and `.sh` files that meet validation rules

#### Scenario: Environment override for plugin directories
- **WHEN** `LAZYSSH_PLUGIN_DIRS` is set with colon-separated absolute paths  
- **THEN** LazySSH SHALL search those directories in the provided order, before the default user directory  
- **AND** ignore non-existent directories without failing discovery

#### Scenario: Precedence rules
- **WHEN** plugins with the same `PLUGIN_NAME` exist in multiple locations  
- **THEN** LazySSH SHALL prefer the first occurrence based on search order: env-provided directories (left to right), then default user directory, then packaged `plugins/`

### Requirement: Executable Built-in Plugins
Built-in plugins distributed with the package MUST be installed with executable permissions and valid shebangs so they are runnable immediately after installation.

#### Scenario: Executable bit present after install
- **WHEN** users install via `pipx install lazyssh` or `pip install lazyssh`  
- **THEN** packaged plugins under `lazyssh/plugins/` SHALL have the executable bit set (at least user-executable)  
- **AND** SHALL start with a valid shebang (`#!/usr/bin/env python3` or `#!/bin/bash`).

#### Scenario: Validation rejects non-executable or missing shebang
- **WHEN** discovery encounters a plugin file that is not executable or lacks a shebang  
- **THEN** the plugin SHALL be marked invalid with a meaningful validation error message

## ADDED Requirements
### Requirement: Plugin Discovery Safety
Discovery SHALL avoid following symlinks outside declared plugin directories and SHALL handle broken symlinks gracefully without crashing. The search MUST be restricted to configured directories and only consider top-level files by default.

#### Scenario: Symlink outside base is ignored
- **WHEN** a symlink points outside a configured plugin directory  
- **THEN** it SHALL be skipped and not loaded


