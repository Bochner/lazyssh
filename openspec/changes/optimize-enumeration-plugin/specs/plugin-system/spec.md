## MODIFIED Requirements
### Requirement: Enumeration Plugin
The enumerate plugin SHALL minimize remote round trips while preserving comprehensive data coverage and deliver a triage-friendly summary.
#### Scenario: Single-session enumeration
- **WHEN** the enumerate plugin runs in default mode
- **THEN** it SHALL collect all category data through a single SSH command execution that leverages the existing control socket
- **AND** additional SSH executions SHALL only occur for explicit retries after a failure
- **AND** command batching SHALL preserve the current graceful-degradation behavior for missing tools.

#### Scenario: Priority findings summary
- **WHEN** enumeration completes
- **THEN** the plugin SHALL derive a prioritized findings summary including at minimum sudo membership, passwordless sudo rules, SUID/SGID binaries, world-writable paths outside sanctioned directories, weak SSH daemon settings, services listening on untrusted interfaces, and suspicious scheduled tasks
- **AND** each summarized item SHALL carry a severity indicator to guide quick triage
- **AND** the summary SHALL appear in both the Rich-rendered terminal report and the JSON output persisted to disk.

## ADDED Requirements
### Requirement: Python Plugin Permission Resilience
Python plugins SHALL remain runnable even when installation strips executable permissions, with best-effort remediation and clear user feedback.
#### Scenario: Python plugin lacking execute bit
- **WHEN** a packaged Python plugin is discovered without user-executable permissions
- **THEN** validation SHALL still mark it runnable by executing it via the configured Python interpreter
- **AND** a warning SHALL be logged to inform the user that permissions were repaired or bypassed.

#### Scenario: Built-in plugin permission repair
- **WHEN** LazySSH starts and built-in Python plugins are missing the executable bit on a writable filesystem
- **THEN** the system SHALL attempt to restore user-executable permissions
- **AND** failures to adjust permissions SHALL not block plugin execution but SHALL be logged for visibility.
