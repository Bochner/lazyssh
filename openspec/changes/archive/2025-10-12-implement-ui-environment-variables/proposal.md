## Why

The troubleshooting documentation currently references six environment variables (LAZYSSH_HIGH_CONTRAST, LAZYSSH_NO_RICH, LAZYSSH_REFRESH_RATE, LAZYSSH_NO_ANIMATIONS, LAZYSSH_COLORBLIND_MODE, LAZYSSH_PLAIN_TEXT) that have no implementation in the codebase. This creates confusion for users who try to use these documented features and find they don't work.

## What Changes

- **ADDED**: Environment variable support for UI customization and accessibility
  - LAZYSSH_HIGH_CONTRAST: Enable high contrast theme variant
  - LAZYSSH_NO_RICH: Disable Rich library features for basic terminal compatibility
  - LAZYSSH_REFRESH_RATE: Control refresh rate for live updates (integer, 1-10)
  - LAZYSSH_NO_ANIMATIONS: Disable progress animations and spinners
  - LAZYSSH_COLORBLIND_MODE: Enable colorblind-friendly theme variant
  - LAZYSSH_PLAIN_TEXT: Force plain text rendering without Rich formatting
- **ADDED**: Environment variable parsing and validation in UI initialization
- **ADDED**: Integration with existing Dracula theme system and accessibility themes
- **ADDED**: Unit tests for all environment variable functionality
- **MODIFIED**: Documentation to specify exact accepted values and precedence rules

## Impact

- Affected specs: user-interface
- Affected code: src/lazyssh/ui.py, src/lazyssh/__main__.py, docs/troubleshooting.md
- Breaking changes: None (additive only)
