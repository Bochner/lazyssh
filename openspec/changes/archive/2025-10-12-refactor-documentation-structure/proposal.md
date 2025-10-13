# Documentation Refactor Proposal

## Why

LazySSH documentation has accumulated verbosity, outdated references, and structural issues over multiple releases. Current problems include:

- **Outdated content**: References to Terminator as required (now optional), old `terminal <connection>` command (now `open`), incorrect environment variable names
- **Missing features**: Runtime terminal switching, native terminal improvements, modern SCP optimizations not documented
- **Excessive verbosity**: User-facing docs contain too much technical detail and implementation specifics better suited for developer documentation
- **Poor structure**: Significant overlap between user-guide.md and commands.md; no clear path from quick start to advanced usage; end users encounter developer-level detail prematurely

This impacts new user onboarding and makes it harder for existing users to find information quickly.

## What Changes

**Core Documentation Updates:**
- Simplify and modernize README.md with focus on quick start and essential features only
- Restructure user-guide.md as a streamlined user journey (installation → first connection → common workflows → next steps)
- Update commands.md with current command names and remove duplicate tutorial content
- Simplify scp-mode.md and tunneling.md to focus on practical usage patterns
- Update troubleshooting.md to reflect current architecture and remove obsolete Windows/Terminator issues
- Ensure development.md remains comprehensive but clearly marked as for contributors only

**Content Corrections:**
- Update all references from `terminal <connection>` to `open <connection>`
- Correct environment variable names (`LAZYSSH_TERMINAL_METHOD` not `LAZYSSH_TERMINAL`)
- Mark Terminator as optional throughout, with native terminal as the default
- Document runtime terminal method switching
- Remove Windows support references (now requires WSL)
- Update SCP mode features to reflect recent optimizations

**Structural Improvements:**
- Remove tutorial/example content from command reference docs
- Create clear separation: README (5-min overview) → User Guide (15-min journey) → Command Reference (lookup) → Specialized Guides (deep dives)
- Consolidate redundant content across multiple files
- Ensure each doc has a single, clear purpose

**Quality Standards:**
- Each user-facing doc should be scannable in under 2 minutes
- Examples should use realistic, modern scenarios
- Technical implementation details only in developer docs
- Every feature mentioned in CHANGELOG should be documented

## Impact

**Affected Documentation:**
- README.md (simplify, update features)
- docs/user-guide.md (restructure, reduce verbosity)
- docs/commands.md (update command names, remove tutorials)
- docs/scp-mode.md (simplify, modernize)
- docs/tunneling.md (simplify, add missing use cases)
- docs/troubleshooting.md (update for current architecture)
- docs/development.md (minor updates for clarity)
- docs/publishing.md (review for accuracy)

**Affected Specs:**
- No spec changes needed - this is a documentation-only refactor

**User Experience Impact:**
- Significantly improved onboarding for new users
- Easier to find specific information
- More accurate and up-to-date documentation
- Clearer distinction between user and developer documentation
