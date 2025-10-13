## ADDED Requirements

### Requirement: Environment Variable UI Configuration

The system SHALL support environment variables for UI customization and accessibility features, allowing users to control theme selection, Rich library usage, refresh rates, animations, and rendering modes.

#### Scenario: High contrast theme selection
- **WHEN** LAZYSSH_HIGH_CONTRAST environment variable is set to "true"
- **THEN** the system SHALL use the high contrast theme variant
- **AND** the theme SHALL provide enhanced visibility with Dracula colors
- **AND** the setting SHALL take precedence over default theme selection

#### Scenario: Rich library disable
- **WHEN** LAZYSSH_NO_RICH environment variable is set to "true"
- **THEN** the system SHALL disable Rich library features
- **AND** output SHALL use plain text formatting only
- **AND** the system SHALL fall back to basic terminal compatibility mode

#### Scenario: Refresh rate control
- **WHEN** LAZYSSH_REFRESH_RATE environment variable is set to an integer value between 1 and 10
- **THEN** the system SHALL use the specified refresh rate for live updates
- **AND** values outside the range SHALL default to 5
- **AND** invalid values SHALL be ignored with a warning logged

#### Scenario: Animation disable
- **WHEN** LAZYSSH_NO_ANIMATIONS environment variable is set to "true"
- **THEN** the system SHALL disable all progress animations and spinners
- **AND** progress indicators SHALL use static text instead of animated elements
- **AND** the setting SHALL apply to all UI components

#### Scenario: Colorblind-friendly theme
- **WHEN** LAZYSSH_COLORBLIND_MODE environment variable is set to "true"
- **THEN** the system SHALL use the colorblind-friendly theme variant
- **AND** the theme SHALL use Dracula colors with enhanced differentiation
- **AND** the setting SHALL take precedence over default theme selection

#### Scenario: Plain text mode
- **WHEN** LAZYSSH_PLAIN_TEXT environment variable is set to "true"
- **THEN** the system SHALL force plain text rendering
- **AND** all Rich formatting SHALL be disabled
- **AND** output SHALL use basic text only

#### Scenario: Environment variable precedence
- **WHEN** multiple conflicting environment variables are set
- **THEN** LAZYSSH_PLAIN_TEXT SHALL take highest precedence
- **AND** LAZYSSH_NO_RICH SHALL take precedence over theme variables
- **AND** theme variables (HIGH_CONTRAST, COLORBLIND_MODE) SHALL be mutually exclusive
- **AND** the last theme variable set SHALL take precedence

#### Scenario: Environment variable validation
- **WHEN** environment variables are parsed at startup
- **THEN** boolean variables SHALL accept "true", "false", "1", "0", "yes", "no" (case insensitive)
- **AND** LAZYSSH_REFRESH_RATE SHALL accept integers between 1 and 10
- **AND** invalid values SHALL be logged as warnings and ignored
- **AND** the system SHALL continue with default values for invalid settings
