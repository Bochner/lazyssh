# Proposal: Add runtime plugin directory `/tmp/lazyssh/plugins`

## Summary
Introduce a runtime-writable plugin directory at `/tmp/lazyssh/plugins` that is created on startup if missing, and included in plugin discovery. This enables users to drop custom plugins without modifying the installed package, while keeping built-ins bundled.

## Goals
- Create `/tmp/lazyssh/plugins` at program start with permissions `0700`.
- Extend plugin discovery precedence to include `/tmp/lazyssh/plugins` ahead of packaged built-ins, but after any `LAZYSSH_PLUGIN_DIRS` env overrides and the default user dir `~/.lazyssh/plugins`.
- Ensure safety: ignore broken symlinks and prevent traversal outside declared directories.

## Non-Goals
- Plugin installation management or persistence across reboots (tmp is ephemeral).
- Versioning or signature verification of third-party plugins.

## Motivation
Users requested a simple, writeable place to stage custom plugins when running from packaged installs or CI where the site-packages tree is read-only. `/tmp/lazyssh/plugins` fits the existing runtime data model (we already use `/tmp/lazyssh/*`).

## Compatibility
Backward compatible. Existing locations continue to work. Discovery order is extended, not replaced.

## Security Considerations
- Restrict permissions to `0700`.
- Do not follow symlinks that resolve outside the base directory.
- Maintain existing validation (shebang, executable bit) and metadata parsing.
