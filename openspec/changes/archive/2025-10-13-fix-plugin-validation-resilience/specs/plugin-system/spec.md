## MODIFIED Requirements
### Requirement: Python Plugin Permission Resilience
Python plugins SHALL remain runnable even when installation strips executable permissions or prevents file access during validation, with best-effort remediation and clear user feedback.
#### Scenario: Python plugin shebang check failure
- **WHEN** a Python plugin file cannot be opened for shebang validation
- **THEN** validation SHALL mark it as valid with a warning instead of invalid
- **AND** execution SHALL proceed via the Python interpreter regardless of shebang presence.

#### Scenario: Built-in plugin validation robustness
- **WHEN** LazySSH discovers built-in Python plugins
- **THEN** file access failures during validation SHALL not prevent plugin discovery or execution
- **AND** plugins SHALL execute successfully via interpreter even without executable permissions or readable shebangs.