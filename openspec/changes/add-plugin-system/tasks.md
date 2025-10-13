# Implementation Tasks

## 1. Core Plugin Infrastructure

- [x] 1.1 Create `src/lazyssh/plugin_manager.py` module
  - [x] 1.1.1 Implement plugin discovery function (scan plugins directory)
  - [x] 1.1.2 Implement plugin validation (check permissions, shebang, naming)
  - [x] 1.1.3 Implement plugin metadata extraction (name, description, requirements)
  - [x] 1.1.4 Implement plugin execution function with SSH connection context
  - [x] 1.1.5 Add error handling and logging for plugin operations
  - [x] 1.1.6 Create helper functions to pass connection info to plugins

- [x] 1.2 Create `src/lazyssh/plugins/` directory structure
  - [x] 1.2.1 Create plugins directory with `__init__.py`
  - [x] 1.2.2 Add `.gitignore` to preserve directory but ignore user plugins
  - [x] 1.2.3 Create plugin template file for reference

## 2. Command Mode Integration

- [x] 2.1 Add `plugin` command to command mode
  - [x] 2.1.1 Implement `plugin list` - show available plugins
  - [x] 2.1.2 Implement `plugin run <name> <socket>` - execute plugin on connection
  - [x] 2.1.3 Implement `plugin info <name>` - show plugin details
  - [x] 2.1.4 Add tab completion for plugin names and socket names
  - [x] 2.1.5 Add command help text and usage examples

## 3. UI Components

- [x] 3.1 Create plugin listing UI in `ui.py`
  - [x] 3.1.1 Add function to display plugins in table format
  - [x] 3.1.2 Show plugin name, type (Python/Shell), and description
  - [x] 3.1.3 Indicate plugin status (valid, invalid, missing dependencies)

- [x] 3.2 Create plugin execution UI feedback
  - [x] 3.2.1 Show progress indicator while plugin runs
  - [x] 3.2.2 Display plugin output with proper formatting
  - [x] 3.2.3 Handle and display plugin errors gracefully
  - [x] 3.2.4 Add execution time tracking and display

## 4. Enumeration Plugin

- [x] 4.1 Create `enumerate.py` plugin
  - [x] 4.1.1 Add plugin metadata header (description, requirements)
  - [x] 4.1.2 Implement OS information gathering
  - [x] 4.1.3 Implement user and group enumeration
  - [x] 4.1.4 Implement network configuration discovery
  - [x] 4.1.5 Implement process and service enumeration
  - [x] 4.1.6 Implement installed packages detection (apt, yum, pacman)
  - [x] 4.1.7 Implement filesystem and mount information
  - [x] 4.1.8 Implement environment variables extraction
  - [x] 4.1.9 Implement scheduled tasks discovery (cron, systemd timers)
  - [x] 4.1.10 Implement security configuration checks
  - [x] 4.1.11 Implement system logs summary
  - [x] 4.1.12 Add JSON output format option
  - [x] 4.1.13 Add human-readable report format
  - [x] 4.1.14 Handle errors gracefully for missing commands or permissions
  - [x] 4.1.15 Add progress indicators for long-running checks

## 5. Documentation

- [x] 5.1 Create plugin development guide
  - [x] 5.1.1 Document plugin structure and conventions
  - [x] 5.1.2 Document environment variables passed to plugins
  - [x] 5.1.3 Document plugin metadata format
  - [x] 5.1.4 Provide example plugins (basic Python and Shell)
  - [x] 5.1.5 Document best practices and security considerations
  - [x] 5.1.6 Document testing and debugging plugins

- [x] 5.2 Update user documentation
  - [x] 5.2.1 Add plugin system section to README.md
  - [x] 5.2.2 Add plugin command examples
  - [x] 5.2.3 Document the enumerate plugin and its output
  - [ ] 5.2.4 Add plugins section to command reference docs
  - [ ] 5.2.5 Add FAQ section for common plugin questions

## 6. Testing

- [ ] 6.1 Write unit tests for plugin manager
  - [ ] 6.1.1 Test plugin discovery with various scenarios
  - [ ] 6.1.2 Test plugin validation logic
  - [ ] 6.1.3 Test plugin execution with mock SSH connections
  - [ ] 6.1.4 Test error handling for invalid plugins
  - [ ] 6.1.5 Test plugin metadata extraction

- [ ] 6.2 Write integration tests
  - [ ] 6.2.1 Test plugin command in command mode
  - [ ] 6.2.2 Test enumerate plugin on test system
  - [ ] 6.2.3 Test plugin execution with real SSH connection
  - [ ] 6.2.4 Test plugin output formatting

- [ ] 6.3 Manual testing
  - [ ] 6.3.1 Test with various plugin types (Python, Shell)
  - [ ] 6.3.2 Test error scenarios (missing plugin, invalid format)
  - [ ] 6.3.3 Test tab completion for plugin commands
  - [ ] 6.3.4 Verify enumerate plugin output on multiple OS types

## 7. Quality Assurance

- [x] 7.1 Run linters and formatters
  - [x] 7.1.1 Run black on new Python files
  - [x] 7.1.2 Run isort on imports
  - [x] 7.1.3 Run flake8 and fix issues
  - [ ] 7.1.4 Run mypy and address type issues

- [x] 7.2 Update CHANGELOG.md with new feature

- [ ] 7.3 Ensure all pre-commit checks pass
