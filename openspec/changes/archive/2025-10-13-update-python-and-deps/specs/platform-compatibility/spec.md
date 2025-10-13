## MODIFIED Requirements
### Requirement: Platform-Agnostic Dependency Checking

The dependency checking system SHALL differentiate between required and optional dependencies on supported Unix-like platforms and be validated on Python 3.13 and newer.

#### Scenario: Python 3.13+ runtime supported
- **WHEN** the application is executed under Python 3.13 or newer
- **THEN** startup and dependency checks SHALL succeed given required externals exist


