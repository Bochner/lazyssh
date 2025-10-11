# Update Changelog

This command updates the CHANGELOG.md file by converting the "Unreleased" section into a versioned release entry.

## Instructions

1. **Find the current version:**
   - Read `pyproject.toml` and extract the version number from the `version = "X.X.X"` line
   - Verify it matches the version in `src/lazyssh/__init__.py` (should be `__version__ = "X.X.X"`)

2. **Check the Unreleased section:**
   - Read `CHANGELOG.md` and locate the `## [Unreleased]` section
   - If there are no changes under Unreleased, inform the user that there's nothing to release

3. **Create the release entry:**
   - Replace `## [Unreleased]` with `## [X.X.X] - YYYY-MM-DD` where:
     - X.X.X is the version from pyproject.toml
     - YYYY-MM-DD is today's date in ISO format
   - Add a new empty `## [Unreleased]` section at the top (after the intro paragraph)
   - Ensure proper formatting following [Keep a Changelog](https://keepachangelog.com/) standards

4. **Verify the structure:**
   - The file should have:
     - Title and intro paragraph
     - Empty `## [Unreleased]` section
     - New `## [X.X.X] - YYYY-MM-DD` section with the changes
     - Previous version sections below
   - Maintain consistent formatting with two blank lines before each version section

5. **Format guidelines:**
   - Use subsections: Added, Changed, Deprecated, Removed, Fixed, Security
   - Keep bullet points aligned with proper indentation
   - Preserve existing formatting and line breaks
   - Use `**BREAKING:**` prefix for breaking changes

## Example output format:

```markdown
# Changelog

All notable changes to LazySSH will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.4] - 2025-10-11

### Changed
- **BREAKING:** Removed native Windows support
  ...

### Fixed
- Fixed SCP mode connection when no arguments provided
  ...

## [1.3.3] - 2025-10-11
...
```

